#!/usr/bin/env python3
"""Read-only FDT memory inventory for the Motorola One Deen bring-up.

Accepts a DTB, optionally a stock C100 FDT, and produces a JSON ledger.
No external Python libraries, device access, flashing, or kernel modifications.
A numeric region match is NEVER interpreted as firmware/driver equivalence.
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

MAGIC = 0xd00dfeed
TOK_BEGIN_NODE, TOK_END_NODE, TOK_PROP, TOK_NOP, TOK_END = 1, 2, 3, 4, 9


def words(raw):
    if len(raw) % 4:
        return None
    return [v[0] for v in struct.iter_unpack(">I", raw)]


def strings(raw):
    return [s.decode("utf-8", "replace") for s in raw.rstrip(b"\0").split(b"\0") if s]


def number(cells):
    value = 0
    for cell in cells:
        value = (value << 32) | cell
    return value


def parse_fdt(data):
    if len(data) < 40:
        raise ValueError("FDT header truncated")
    (magic, total, struct_off, strings_off, reserve_off, version, _last,
     _boot, strings_size, struct_size) = struct.unpack_from(">10I", data, 0)
    if magic != MAGIC or version < 16 or total > len(data):
        raise ValueError("invalid FDT header, version, or total size")
    if (struct_off + struct_size > total or strings_off + strings_size > total
            or reserve_off + 16 > total):
        raise ValueError("FDT block extends past total size")
    nodes = {}
    stack = []
    pos = struct_off
    limit = struct_off + struct_size
    while pos + 4 <= limit:
        token = struct.unpack_from(">I", data, pos)[0]
        pos += 4
        if token == TOK_BEGIN_NODE:
            end = data.find(b"\0", pos, limit)
            if end < 0:
                raise ValueError("unterminated node name")
            name = data[pos:end].decode("utf-8", "replace")
            pos = (end + 4) & ~3
            stack.append(name)
            path = "/" + "/".join(segment for segment in stack if segment)
            if path in nodes:
                raise ValueError("duplicate node path " + path)
            nodes[path] = {}
        elif token == TOK_END_NODE:
            if not stack:
                raise ValueError("unexpected END_NODE")
            stack.pop()
        elif token == TOK_PROP:
            if pos + 8 > limit or not stack:
                raise ValueError("invalid property header")
            size, name_offset = struct.unpack_from(">2I", data, pos)
            pos += 8
            if pos + size > limit or name_offset >= strings_size:
                raise ValueError("property extends outside FDT blocks")
            name_end = data.find(b"\0", strings_off + name_offset,
                                 strings_off + strings_size)
            if name_end < 0:
                raise ValueError("unterminated property name")
            name = data[strings_off + name_offset:name_end].decode("utf-8", "replace")
            path = "/" + "/".join(segment for segment in stack if segment)
            nodes[path][name] = data[pos:pos + size]
            pos += (size + 3) & ~3
        elif token == TOK_NOP:
            continue
        elif token == TOK_END:
            if stack:
                raise ValueError("unterminated FDT nodes")
            break
        else:
            raise ValueError(f"unknown token {token} at byte {pos - 4}")
    else:
        raise ValueError("missing FDT_END token")

    memreserve = []
    pos = reserve_off
    while pos + 16 <= total:
        start, size = struct.unpack_from(">QQ", data, pos)
        pos += 16
        if start == size == 0:
            break
        memreserve.append({"start": start, "size": size,
                           "end_exclusive": start + size})
    else:
        raise ValueError("unterminated memreserve table")
    return nodes, memreserve


def resolve_cells(nodes, parent):
    props = nodes.get(parent, {})
    address = words(props.get("#address-cells", b""))
    size = words(props.get("#size-cells", b""))
    if not address or not size or not 1 <= address[0] <= 4 or not 0 <= size[0] <= 4:
        return None
    return address[0], size[0]


def decode_reg(props, address_cells, size_cells):
    cells = words(props.get("reg", b""))
    length = address_cells + size_cells
    if cells is None or not cells or not length or len(cells) % length:
        return []
    out = []
    for idx in range(0, len(cells), length):
        base = number(cells[idx:idx + address_cells])
        size = number(cells[idx + address_cells:idx + length])
        out.append({"start": base, "size": size, "end_exclusive": base + size})
    return out


def inventory(data, source_label):
    nodes, memreserve = parse_fdt(data)
    root = nodes.get("/", {})
    reserved = nodes.get("/reserved-memory", {})
    cells = resolve_cells(nodes, "/reserved-memory")
    if cells is None:
        raise ValueError("cannot determine reserved-memory #address/#size-cells")
    phandles = {}
    duplicate_phandles = []
    for path, props in nodes.items():
        for key in ("phandle", "linux,phandle"):
            vals = words(props.get(key, b""))
            if vals and len(vals) == 1:
                if vals[0] in phandles and phandles[vals[0]] != path:
                    duplicate_phandles.append([vals[0], phandles[vals[0]], path])
                phandles[vals[0]] = path
    entries, references = [], []
    for path, props in nodes.items():
        if path.startswith("/reserved-memory/") and path.count("/") == 2:
            entries.append({
                "node": path,
                "reg": decode_reg(props, *cells),
                "dynamic_size_cells": words(props.get("size", b"")),
                "compatible": strings(props.get("compatible", b"")),
                "no_map": "no-map" in props,
                "reusable": "reusable" in props,
                "phandle": (words(props.get("phandle", b"")) or [None])[0],
            })
        for key in ("memory-region", "qcom,rpm-msg-ram"):
            vals = words(props.get(key, b""))
            if vals:
                names = strings(props.get("memory-region-names", b""))
                for index, handle in enumerate(vals):
                    references.append({
                        "consumer": path, "property": key,
                        "index": index, "name": names[index] if index < len(names)
                        and key == "memory-region" else None,
                        "phandle": handle, "provider": phandles.get(handle),
                    })
    spans = [(e["node"], r["start"], r["end_exclusive"])
             for e in entries for r in e["reg"] if r["size"] > 0]
    spans.sort(key=lambda r: (r[1], r[2]))
    overlap = [{"a": a[0], "b": b[0], "start": max(a[1], b[1]),
                "end_exclusive": min(a[2], b[2])}
               for i, a in enumerate(spans)
               for b in spans[i + 1:] if a[1] < b[2] and b[1] < a[2]]
    return {
        "source": source_label,
        "sha256": hashlib.sha256(data).hexdigest(),
        "fdt_node_count": len(nodes),
        "root_model": strings(root.get("model", b"")),
        "qcom_board_id_cells": words(root.get("qcom,board-id", b"")),
        "qcom_msm_id_cells": words(root.get("qcom,msm-id", b"")),
        "memreserve_table": memreserve,
        "reserved_memory": entries,
        "direct_references": references,
        "overlap_between_fixed_reserved_memory_nodes": overlap,
        "duplicate_phandles": duplicate_phandles,
        "unresolved_memory_references": [r for r in references if r["provider"] is None],
        "limits": [
            "No driver/firmware ownership or ABI inference",
            "Dynamic memory pools and non-memory-region phandle consumers not exhaustively traced",
            "An FDT file does not prove the bootloader selects it",
            "This is not a boot, schema, ROM or flash validation",
        ],
    }


def compare_stock(candidate, stock):
    cr = [(e["node"], r["start"], r["size"])
          for e in candidate["reserved_memory"] for r in e["reg"]]
    sr = [(e["node"], r["start"], r["size"])
          for e in stock["reserved_memory"] for r in e["reg"]]
    return {
        "stock_only_fixed_intervals": [{"node": p, "start": s, "size": n}
                                      for p, s, n in sr if not any((s, n) == (x, y) for _, x, y in cr)],
        "candidate_only_fixed_intervals": [{"node": p, "start": s, "size": n}
                                          for p, s, n in cr if not any((s, n) == (x, y) for _, x, y in sr)],
        "same_start_size_does_not_prove_semantic_equivalence": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path, help="compiled candidate DTB (read-only)")
    parser.add_argument("--stock", type=Path, help="original extracted stock FDT; optional")
    parser.add_argument("--expected-board-id", type=lambda x: int(x, 0),
                        help="second qcom,board-id cell, e.g. 0xc100")
    parser.add_argument("--expected-msm-id", type=lambda x: int(x, 0),
                        help="first qcom,msm-id cell, e.g. 0x125; optional")
    parser.add_argument("--strict-structural", action="store_true",
                        help="fail on overlap, dangling direct refs, duplicate phandles or board mismatch")
    args = parser.parse_args()
    try:
        candidate = inventory(args.candidate.read_bytes(), args.candidate.name)
        result = {"candidate": candidate}
        if args.stock:
            stock = inventory(args.stock.read_bytes(), args.stock.name)
            result["stock"] = stock
            result["stock_comparison"] = compare_stock(candidate, stock)
        if args.expected_board_id is not None:
            result["board_identity_matches_expected"] = (
                candidate["qcom_board_id_cells"] == [0x4d, args.expected_board_id]
            )
        if args.expected_msm_id is not None:
            result["msm_identity_matches_expected"] = (
                candidate["qcom_msm_id_cells"] == [args.expected_msm_id, 0]
            )
        invalid = (candidate["overlap_between_fixed_reserved_memory_nodes"]
                   or candidate["duplicate_phandles"]
                   or candidate["unresolved_memory_references"]
                   or result.get("board_identity_matches_expected") is False
                   or result.get("msm_identity_matches_expected") is False)
        result["structural_result"] = "FAIL" if invalid else "PASS_SCOPE_LIMITED"
        result["global_result"] = "HOLD_NOT_BOOT_VALIDATION"
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 3 if invalid and args.strict_structural else 0
    except (ValueError, OSError, struct.error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())