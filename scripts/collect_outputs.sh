#!/usr/bin/env bash
# Copies the files produced inside the IIC-OSIC-TOOLS container into this repo.
# Usage:  ./scripts/collect_outputs.sh [design-dir]      (default: ~/eda/designs/arbiter4)
set -uo pipefail
SRC="${1:-$HOME/eda/designs/arbiter4}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/layout" "$ROOT/results"
cp_or_warn() { cp -v "$1" "$2" 2>/dev/null || echo "WARNING: missing $1"; }
cp_or_warn "$SRC/arbiter4.gds"   "$ROOT/layout/arbiter4.gds"
cp_or_warn "$SRC/arbiter4.mag"   "$ROOT/layout/arbiter4.mag"
for f in "$SRC"/sky130_fd_pr__*.mag; do [ -e "$f" ] && cp -v "$f" "$ROOT/layout/"; done
cp_or_warn "$SRC/arbiter4.spice"  "$ROOT/results/arbiter4_extracted.spice"
cp_or_warn "$SRC/lvs_out.txt"     "$ROOT/results/lvs_out.txt"
cp_or_warn "$SRC/sky130_drc.txt"  "$ROOT/results/klayout_drc_report.rdb.txt"
echo
for img in docs/images/xschem_schematic.png docs/images/ngspice_waveforms.png; do
  [ -e "$ROOT/$img" ] || echo "TODO: add screenshot $img (README references it)"
done
echo "Done. Review with:  git status"
