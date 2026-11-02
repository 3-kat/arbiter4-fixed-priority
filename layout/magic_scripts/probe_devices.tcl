# probe_devices.tcl (v3) - generates one NFET and one PFET with Magic's sky130
# device generators and saves their geometry so it can be read as text.
# Run from the Magic tkcon window:   source probe_devices.tcl

puts "PROBE tech=[tech name]  windows=[windownames]"
if {[tech name] ne "sky130A"} { puts "PROBE ABORT: wrong tech"; return }

proc set_box {llx lly urx ury} {
    # try several spellings; Magic versions differ
    foreach cmd [list \
        "box values $llx $lly $urx $ury" \
        "box $llx $lly $urx $ury" \
        "box position $llx $lly"] {
        if {![catch {eval $cmd} err]} {
            if {[catch {box exists} ex] == 0 && $ex} { return 1 }
        } else {
            puts "PROBE box cmd failed: $cmd -> $err"
        }
    }
    puts "PROBE could not create a box (no layout window selected?)"
    return 0
}

proc try_gen {dev inst params} {
    set cmds [list \
        [list magic::gencell $dev $inst $params] \
        [concat [list magic::gencell $dev $inst] $params]]
    foreach cmd $cmds {
        if {![catch {{*}$cmd} err]} { puts "PROBE OK: $cmd"; return 1 }
        puts "PROBE failed: $cmd -> $err"
    }
    return 0
}

if {[catch {load probe} err]} { puts "PROBE load: $err" }
if {![set_box 0um 0um 1um 1um]} { return }
try_gen sky130::sky130_fd_pr__nfet_01v8 mn1 {w 1.0 l 0.15 nf 1}
set_box 10um 0um 11um 1um
try_gen sky130::sky130_fd_pr__pfet_01v8 mp1 {w 2.0 l 0.15 nf 1}

puts "PROBE cells: [cellname list allcells]"
catch {save probe} err; puts "PROBE save: $err"
catch {writeall force} err; puts "PROBE writeall: $err"
puts "PROBE done - now run in a shell:  ls *.mag"
