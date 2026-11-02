import runpy,io,contextlib,os
with contextlib.redirect_stdout(io.StringIO()): ns=runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)),'gen_all.py'))
TY,xs,P_LLY,RAIL_V,RAIL_G,x_lo=ns['TY'],ns['xs'],ns['P_LLY'],ns['RAIL_V'],ns['RAIL_G'],ns['x_lo']
lab=[]   # (layer,x1,y1,x2,y2,name,type)
bus_x1={}
for n in ('req0','req1','req2','gnt1','gnt2','gnt3'):
    vx=[x for k,x in enumerate(xs) if ns['gate'][k]==n]+[x-88 for k,x in enumerate(xs) if ns['out'][k]==n]
    bus_x1[n]=min(vx)-26
for n,t in (('req0','input'),('req1','input'),('req2','input'),('gnt1','output'),('gnt2','output'),('gnt3','output')):
    y=TY[n]; lab.append(('metal2',bus_x1[n]+4,y-12,bus_x1[n]+64,y+12,n,t))
lab.append(('metal1',xs[4]-20,600,xs[4]+20,640,'req3','input'))
lab.append(('metal1',xs[1]-114+8,600,xs[1]-114+44,640,'gnt0','output'))
lab.append(('metal1',x_lo+10,RAIL_V[0]+14,x_lo+70,RAIL_V[1]-14,'VDD','power bidirectional'))
lab.append(('metal1',x_lo+10,RAIL_G[0]+14,x_lo+70,RAIL_G[1]-14,'GND','ground bidirectional'))
body=''.join(f'flabel {l} s {a} {b} {c} {d} 0 FreeSans 200 0 0 0 {n}\nport {i+1} nsew signal {t}\n' if not t.startswith(('power','ground')) else
             f'flabel {l} s {a} {b} {c} {d} 0 FreeSans 200 0 0 0 {n}\nport {i+1} nsew {t}\n' for i,(l,a,b,c,d,n,t) in enumerate(lab))
tcl=r'''# stage4_labels_lvs_gds.tcl - pin labels/ports, extraction, GDS
# run in tkcon (cell arbiter4 saved, stage 3 done):   source stage4_labels_lvs_gds.tcl
save arbiter4
set fn [file join [pwd] arbiter4.mag]
set fh [open $fn r]; set txt [read $fh]; close $fh
if {[string first "<< labels >>" $txt] >= 0} {
    puts "STAGE4: labels already present - skipping insertion"
} else {
    set LBL {''' + body + r'''}
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
'''
open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','magic_scripts','stage4_labels_lvs_gds.tcl'),'w').write(tcl)
print(body)
