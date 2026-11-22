#!/system/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
# Read-only. Run on Android after ordinary use, with no USB or host tools.
set -eu
export LC_ALL=C
skip() { printf 'INCONCLUSIVE %s\n' "$*" >&2; exit 2; }
dt=/sys/firmware/devicetree/base
[ -r "$dt/qcom,board-id" ] || skip "board-id unreadable"
board=$(od -An -tx1 -v "$dt/qcom,board-id" | tr -d '[:space:]')
[ "$board" = 0000004d0000c100 ] || skip "board-id=$board"
tr '\000' '\n' < "$dt/compatible" | grep -Fxq 'qcom,msm8953-deen' || skip "Deen compatible missing"
release=$(uname -r)
printf 'board=C100 kernel=%s\n' "$release"
case "$release" in 5.15|5.15.*|5.15-*) ;; *) skip "requires the 5.15 candidate";; esac
policy=/sys/devices/system/cpu/cpufreq/policy0
[ -r "$policy/scaling_driver" ] || skip "CPUFreq policy0 unreadable"
[ "$(cat "$policy/scaling_driver")" = deen-cpr4 ] || skip "different CPUFreq driver"
cpus=$(awk '{$1=$1;print}' "$policy/related_cpus")
[ "$cpus" = '0 1 2 3 4 5 6 7' ] || skip "related_cpus=$cpus"
set -- /sys/bus/platform/drivers/deen-cpr4-cpufreq/*/deen_validation
[ "$#" -eq 1 ] && [ -r "$1" ] || skip "driver snapshot unavailable"
sample=$(cat "$1") || skip "PLL, mux or CPR4 readback failed"
printf '%s\n' "$sample"
printf '%s\n' "$sample" | awk '
NF==5 && $1~/^cpu_hz=[1-9][0-9]*$/ && $2~/^cci_hz=[1-9][0-9]*$/ &&
$3~/^corner=[1-9]$/ && $4~/^up=[0-9]+$/ && $5~/^down=[0-9]+$/ {
  split($1,c,"="); split($2,i,"="); split($4,u,"="); split($5,d,"=")
  ok = (c[2]*2 == i[2]*5 && u[2]+0 > 0 && d[2]+0 > 0)
}
END { exit !ok }' || skip "need verified transitions in both directions and a valid current snapshot"
set -- /sys/bus/platform/drivers/qcom,spm-regulator/*/s5_microvolts
[ "$#" -eq 1 ] && [ -r "$1" ] || skip "S5 hardware readback unavailable"
uv=$(cat "$1") || skip "CCI SAW voltage read failed"
case "$uv" in ''|*[!0-9]*) skip "invalid S5 voltage";; esac
[ "$uv" -ge 400000 ] && [ "$uv" -le 1140000 ] || skip "S5 outside C100 constraints"
printf 's5_microvolts=%s\n' "$uv"
printf '%s\n' 'PASS C100 CPUFreq up/down, PLL and CCI readback, CPR4 corner and S5 status'
