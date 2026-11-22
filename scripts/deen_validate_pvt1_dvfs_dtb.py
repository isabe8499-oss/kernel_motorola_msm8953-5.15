#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Verify the compiled C100 integration DTB against the supplied stock FDT."""
import hashlib
import subprocess
import sys

dtb = sys.argv[1]
soc = "/soc@0"
clock = soc + "/clock-controller@b116000"
ctrl = soc + "/regulator-controller@b018000"
corner = ctrl + "/thread/regulator"
s5 = soc + "/spmi@200f000/pmic@1/regulator@2000"
policy = soc + "/cpufreq"


def get(*args):
    return subprocess.check_output(["fdtget", *args[:2], dtb, *args[2:]], text=True).strip()


def cells(node, key):
    return [int(x, 16) for x in get("-t", "x", node, key).split()]


def phandle(node):
    value, = cells(node, "phandle")
    return value


def digest(node, keys):
    h = hashlib.sha256()
    for key in sorted(keys):
        value = bytes(int(x, 16) for x in get("-t", "bx", node, key).split())
        h.update(key.encode() + b"\0" + len(value).to_bytes(4, "big") + value)
    return h.hexdigest()


def properties(node):
    return subprocess.check_output(["fdtget", "-p", dtb, node], text=True).splitlines()


def equal(actual, expected, subject):
    if actual != expected:
        raise SystemExit(f"{subject}: got {actual}, expected {expected}")


equal(cells("/", "qcom,board-id"), [77, 0xc100], "board")
equal(cells(policy, "clocks"), [phandle(clock), 0x96854074] +
      [phandle(clock), 0x2e6af930] * 8, "shared clocks")
equal(cells(policy, "qcom,cpufreq-table"),
      [345600, 533000, 729600, 1036800, 1401600, 1651600, 1804800, 1958400, 2016000],
      "stock CPUFreq requests")
equal(cells(clock, "power-domains"), [phandle("/smd/rpm/rpm-requests/power-controller"), 6], "MX AO")
equal(cells(clock, "clocks"), [phandle("/clocks/xo-board")], "XO")
for node, key, target in [
    (clock, "vdd-cl-supply", corner), (ctrl, "vdd-supply", s5),
    (ctrl, "vdd-limit-supply", s5 + "/avs-limit-regulator"),
    (ctrl, "qcom,apm-ctrl", soc + "/power-mux@b1112a8"),
    (ctrl, "mem-acc-supply", soc + "/regulator@19461d4"),
]:
    equal(cells(node, key), [phandle(target)], key)

saw = soc + "/voltage-controller@b1d2000"
equal(cells(s5, "motorola,cci-saw"), [phandle(saw)], "S5 voltage controller")
equal(cells(saw, "reg"), [0xb1d2000, 0x1000], "CCI SAW aperture")
equal(cells(soc + "/power-mux@b1112a8", "reg"), [0xb1112a8, 12], "APM aperture")
for name, start, size in [
    ("memory@90001000", 0x90001000, 0x13ff000),
    ("memory@aefd2000", 0xaefd2000, 0x2000),
    ("memory@aefd4000", 0xaefd4000, 0x2c000),
    ("ramoops@ef000000", 0xef000000, 0xa0000),
    ("memory@ef0a0000", 0xef0a0000, 0x20000),
]:
    equal(cells("/reserved-memory/" + name, "reg"), [0, start, 0, size], name)

ramoops = "/reserved-memory/ramoops@ef000000"
for key, size in [("record-size", 0x20000), ("console-size", 0x40000), ("pmsg-size", 0x40000)]:
    equal(cells(ramoops, key), [size], key)
equal(cells(policy, "vdd-s5-supply"), [phandle(s5)], "readback from S5")
clock_keys = [k for k in properties(clock) if k.startswith("qcom,speed") or k in ("reg", "reg-names")]
cpr_keys = [k for k in properties(corner) if k.startswith(("qcom,", "regulator-"))]
equal(digest(clock, clock_keys), "d3215ce11e02935035a5b9b352e5c899e595c76ae3f7d5768762822dbc2bf875",
      "stock CPU/CCI plans and resources")
equal(digest(corner, cpr_keys), "f1facfb6e55917bd7ff0e9e46e0ef5401883632b0d251f5f3645a4768fe4eb6f",
      "stock CPR4 corner calibration")
print("PASS compiled C100 DTB: eight CPUs, CPU/CCI plans, MX, CPR4 supplies and calibration")
