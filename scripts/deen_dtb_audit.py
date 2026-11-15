#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Inventory FDTs embedded in a stock Android boot image and compare one DTB.

Structural inventory only. This tool does not prove hardware correctness,
bootloader selection, or bootability.
"""
import argparse
import json
import struct
import sys
from pathlib import Path

MAGIC = b"\xd0\x0d\xfe\xed"
BEGIN, END_NODE, PROP, NOP, END = 1, 2, 3, 4, 9


def cells(raw):
    if raw is None or len(raw) % 4:
        return None
    return list(struct.unpack(">" + "I" * (len(raw) // 4), raw))


def parse_fdt(data, offset=0):
    if offset < 0 or offset + 40 > len(data) or data[offset:offset + 4] != MAGIC:
        return None
    try:
        (magic, total, struct_off, strings_off, _reserve, _version,
         _last, _bootcpu, strings_size, struct_size) = struct.unpack_from(">10I", data, offset)
    except struct.error:
        return None
    if magic != 0xD00DFEED or total < 40 or offset + total > len(data):
        return None
    if struct_off + struct_size > total or strings_off + strings_size > total:
        return None
    st = data[offset + struct_off:offset + struct_off + struct_size]
    names = data[offset + strings_off:offset + strings_off + strings_size]
    pos, stack, root, nodes = 0, [], None, []
    try:
        while pos + 4 <= len(st):
            token = struct.unpack_from(">I", st, pos)[0]
            pos += 4
            if token == BEGIN:
                end = st.index(b"\0", pos)
                name = st[pos:end].decode("utf-8", "replace")
                pos = (end + 4) & ~3
                node = {"name": name, "props": {}, "children": []}
                if stack:
                    stack[-1]["children"].append(node)
                elif root is None:
                    root = node
                else:
                    return None
                stack.append(node)
                nodes.append(node)
            elif token == END_NODE:
                if not stack:
                    return None
                stack.pop()
            elif token == PROP:
                if pos + 8 > len(st) or not stack:
                    return None
                length, nameoff = struct.unpack_from(">II", st, pos)
                pos += 8
                if nameoff >= len(names) or pos + length > len(st):
                    return None
                end = names.find(b"\0", nameoff)
                if end < 0:
                    return None
                key = names[nameoff:end].decode("utf-8", "replace")
                stack[-1]["props"][key] = st[pos:pos + length]
                pos = (pos + length + 3) & ~3
            elif token == NOP:
                continue
            elif token == END:
                break
            else:
                return None
    except (ValueError, struct.error):
        return None
    if root is None or stack:
        return None
    return {"offset": offset, "size": total, "root": root, "nodes": nodes}


def flatten(root):
    result = {}
    def visit(node, parent):
        path = (parent.rstrip("/") + "/" + node["name"]) if parent else "/"
        result[path] = node
        for child in node["children"]:
            visit(child, path)
    visit(root, "")
    return result


def prop_cells(node, key):
    return cells(node["props"].get(key))


def compatibles(node):
    return [x.decode("utf-8", "replace") for x in
            node["props"].get("compatible", b"").split(b"\0") if x]


def scan(data):
    found, start = [], 0
    while True:
        offset = data.find(MAGIC, start)
        if offset < 0:
            break
        item = parse_fdt(data, offset)
        if item:
            found.append(item)
        start = offset + 1
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("boot_image", type=Path, help="raw stock boot.img or boot_b image")
    ap.add_argument("candidate_dtb", type=Path, help="compiled candidate DTB")
    ap.add_argument("--msm-id", default="0x125,0", help="two cells, default: 0x125,0")
    ap.add_argument("--board-id", default="0x4d,0xc100", help="two cells, default: 0x4d,0xc100")
    ap.add_argument("--json", type=Path, help="optional JSON report path")
    args = ap.parse_args()
    msm = [int(x, 0) for x in args.msm_id.split(",")]
    board = [int(x, 0) for x in args.board_id.split(",")]
    if len(msm) != 2 or len(board) != 2:
        ap.error("--msm-id and --board-id must each contain exactly two cells")

    blobs = scan(args.boot_image.read_bytes())
    matches = [x for x in blobs if prop_cells(x["root"], "qcom,msm-id") == msm
               and prop_cells(x["root"], "qcom,board-id") == board]
    if len(matches) != 1:
        print("ERROR: expected exactly one stock FDT for the requested tuple; "
              f"found {len(matches)} (valid FDT blobs: {len(blobs)})", file=sys.stderr)
        return 2
    stock = matches[0]
    candidate = parse_fdt(args.candidate_dtb.read_bytes())
    if not candidate:
        print("ERROR: candidate is not a valid FDT", file=sys.stderr)
        return 2

    s, c = flatten(stock["root"]), flatten(candidate["root"])
    sp, cp = set(s), set(c)
    missing, extra, common = sorted(sp - cp), sorted(cp - sp), sp & cp
    report = {
        "classification": "STRUCTURAL_INVENTORY_ONLY_NOT_BOOTABILITY",
        "valid_fdt_blobs_in_stock_image": len(blobs),
        "selected_stock_fdt": {"offset": stock["offset"], "size_bytes": stock["size"],
                               "node_count": len(stock["nodes"])},
        "identity": {"msm_id": msm, "board_id": board,
                     "stock_compatible": compatibles(stock["root"]),
                     "candidate_compatible": compatibles(candidate["root"])},
        "candidate": {"size_bytes": candidate["size"], "node_count": len(candidate["nodes"])},
        "path_comparison": {
            "stock_only_node_paths": len(missing),
            "candidate_only_node_paths": len(extra),
            "common_node_paths": len(common),
            "stock_properties_missing_on_common_nodes": sum(
                len(set(s[p]["props"]) - set(c[p]["props"])) for p in common),
            "candidate_extra_properties_on_common_nodes": sum(
                len(set(c[p]["props"]) - set(s[p]["props"])) for p in common),
            "sample_stock_only_paths": missing[:80],
            "sample_candidate_only_paths": extra[:80],
        },
        "warning": "Path/name differences are not a semantic device-by-device verdict. "
                   "Matching identity and structural counts do not prove register, "
                   "interrupt, clock, memory, firmware, or runtime correctness."
    }
    rendered = json.dumps(report, indent=2)
    print(rendered)
    if args.json:
        args.json.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
