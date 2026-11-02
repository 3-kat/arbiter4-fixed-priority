# build_arbiter4.tcl  -  STAGE 1: place 28 devices + tie each column's gates
# Run in the Magic GUI (click in the layout window first):  source build_arbiter4.tcl
# Units below are internal units: 1 unit = 0.005 um.

snap internal
proc um {n} { return "[format %.3f [expr {$n * 0.005}]]um" }
proc setbox {x1 y1 x2 y2} { box values [um $x1] [um $y1] [um $x2] [um $y2] }
proc rectpaint {layer x1 y1 x2 y2} { setbox $x1 $y1 $x2 $y2; paint $layer }

proc gen {dev inst w x y} {
    # place the device so the lower-left of its abutment box is at (x,y)
    setbox $x $y [expr {$x + 200}] [expr {$y + 200}]
    magic::gencell $dev $inst w $w l 0.15 nf 1
}

load arbiter4
snap internal
if {[llength [cellname list children arbiter4]] > 0} {
    puts "STAGE1 ABORT: arbiter4 already contains devices (re-running would confuse gencell)."
    puts "Fix: in a shell run   rm arbiter4.mag   then in tkcon run   flush arbiter4   and source this file again."
    return
}

# column order = schematic order (MP1/MN1 ... MP14/MN14)
# PMOS widths per column:
set wp {2.0 2.0 2.0 2.0 2.0  4.0 4.0  6.0 6.0 6.0  8.0 8.0 8.0 8.0}
set PITCH 422      ;# well width -> PMOS/NMOS wells abut, no well-spacing issue
set X0    0
set N_LLY -257     ;# NMOS abutment-box lower-left y  (NMOS centre at y=0)
set P_LLY  1300    ;# PMOS abutment-box lower-left y  (all PMOS bottom-aligned; tall channel for metal2 buses)

for {set k 0} {$k < 14} {incr k} {
    set n [expr {$k + 1}]
    set xc [expr {$X0 + $k * $PITCH}]               ;# column centre
    gen sky130::sky130_fd_pr__nfet_01v8 MN$n 1.0 [expr {$xc - 158}] $N_LLY
    gen sky130::sky130_fd_pr__pfet_01v8 MP$n [lindex $wp $k] [expr {$xc - 158}] $P_LLY
    # gate tie: NMOS top gate pad (top edge y=178) up to PMOS bottom gate pad (y=743..789)
    rectpaint metal1 [expr {$xc - 29}] 170 [expr {$xc + 29}] [expr {$P_LLY + 86}]
    # the unused gate pad at the far end of each gate is below the metal1
    # minimum area (0.083 um^2) -> grow it a little
    set W [lindex $wp $k]
    rectpaint metal1 [expr {$xc - 29}] -194 [expr {$xc + 29}] -132      ;# NMOS bottom pad
    set ptop [expr {$P_LLY + int($W * 200) + 207}]
    rectpaint metal1 [expr {$xc - 29}] $ptop [expr {$xc + 29}] [expr {$ptop + 63}]   ;# PMOS top pad
}

setbox 0 0 0 0
catch {view}
save arbiter4
drc check
drc catchup
puts "STAGE1 done. DRC error count follows:"
drc count
