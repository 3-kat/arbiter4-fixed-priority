# stage4_labels_lvs_gds.tcl - pin labels/ports, extraction, GDS
# run in tkcon (cell arbiter4 saved, stage 3 done):   source stage4_labels_lvs_gds.tcl
save arbiter4
set fn [file join [pwd] arbiter4.mag]
set fh [open $fn r]; set txt [read $fh]; close $fh
if {[string first "<< labels >>" $txt] >= 0} {
    puts "STAGE4: labels already present - skipping insertion"
} else {
    set LBL {flabel metal2 s -22 308 38 332 0 FreeSans 200 0 0 0 req0
port 1 nsew signal input
flabel metal2 s 822 398 882 422 0 FreeSans 200 0 0 0 req1
port 2 nsew signal input
flabel metal2 s 1244 488 1304 512 0 FreeSans 200 0 0 0 req2
port 3 nsew signal input
flabel metal2 s 2000 938 2060 962 0 FreeSans 200 0 0 0 gnt1
port 4 nsew signal output
flabel metal2 s 2844 1028 2904 1052 0 FreeSans 200 0 0 0 gnt2
port 5 nsew signal output
flabel metal2 s 4110 1118 4170 1142 0 FreeSans 200 0 0 0 gnt3
port 6 nsew signal output
flabel metal1 s 1668 600 1708 640 0 FreeSans 200 0 0 0 req3
port 7 nsew signal input
flabel metal1 s 316 600 352 640 0 FreeSans 200 0 0 0 gnt0
port 8 nsew signal output
flabel metal1 s -190 3300 -130 3360 0 FreeSans 200 0 0 0 VDD
port 9 nsew power bidirectional
flabel metal1 s -190 -296 -130 -236 0 FreeSans 200 0 0 0 GND
port 10 nsew ground bidirectional
}
    set idx [string last "<< end >>" $txt]
    set fh [open $fn w]
    puts -nonewline $fh "[string range $txt 0 [expr {$idx - 1}]]<< labels >>\n$LBL<< end >>\n"
    close $fh
    flush arbiter4
    puts "STAGE4: labels inserted"
}
drc check
drc catchup
puts "STAGE4: DRC after labels:"
drc count
if {[catch {extract all} e]} { puts "STAGE4 extract failed: $e" }
ext2spice lvs
if {[catch {ext2spice} e]} { puts "STAGE4 ext2spice failed: $e" }
if {[catch {gds write arbiter4} e]} { puts "STAGE4 gds failed: $e" }
puts "STAGE4 done. Files: arbiter4.ext arbiter4.spice arbiter4.gds (in this folder)"
