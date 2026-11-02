import itertools, collections, os
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','magic_scripts')
PITCH=422; P_LLY=1300
WP=[2,2,2,2,2,4,4,6,6,6,8,8,8,8]
# column table: (gate net, out net, group, position-in-group)  ; groups: list of column lists, left->right = P_m ... P_1
groups=[('inv',[0],'nreq0'),('inv',[1],'gnt0'),('inv',[2],'nreq1'),('inv',[3],'nreq2'),('inv',[4],'nreq3'),
        ('nor',[5,6],'gnt1'),('nor',[7,8,9],'gnt2'),('nor',[10,11,12,13],'gnt3')]
gate={0:'req0',1:'nreq0',2:'req1',3:'req2',4:'req3',5:'req0',6:'nreq1',7:'req0',8:'req1',9:'nreq2',10:'req0',11:'req1',12:'req2',13:'nreq3'}
out={};pdnet={};psnet={};full=set();p1=set()
for kind,cs,o in groups:
    for j,c in enumerate(cs):
        out[c]=o
        pdnet[c]=o if j==0 else f'{o}_l{j-1}'
        psnet[c]='VDD' if j==len(cs)-1 else f'{o}_l{j}'
        if j==0: full.add(c)            # dv reaches the PMOS drain pad
        if j==len(cs)-1: p1.add(c)
TRACKS=['req0','req1','req2','nreq0','nreq1','nreq2','nreq3','gnt1','gnt2','gnt3']
TY={n:320+90*i for i,n in enumerate(TRACKS)}
xs=[k*PITCH for k in range(14)]
x_lo,x_hi=xs[0]-200,xs[-1]+200
RAIL_G=(-310,-222); RAIL_V=(P_LLY+1986,P_LLY+2074)
# each entry: (layer, net, x1,y1,x2,y2, flag)   flag: 'dev' existing, 'ext' unconnected-by-metal pad, 'new'
S=[]
def add(l,n,a,b,c,d,f='new'): S.append((l,n,a,b,c,d,f))
vias=[]           # (net,cx,cy)
stage2=[];stage3=[];vialis=[]
for k,xc in enumerate(xs):
    W=WP[k]; half=W*100; cy=P_LLY+166+half; g=gate[k]
    add('m1',g,xc-29,170,xc+29,P_LLY+86,'dev')                    # stage-1 gate tie
    add('m1',g,xc-29,132,xc+29,178,'dev'); add('m1',g,xc-29,-194,xc+29,-132,'ext')
    add('m1',g,xc-29,P_LLY+79,xc+29,P_LLY+125,'dev'); add('m1',g,xc-29,P_LLY+W*200+207,xc+29,P_LLY+W*200+270,'ext')
    add('m1',out[k],xc-67,-100,xc-21,100,'dev'); add('m1','GND',xc+21,-100,xc+67,100,'dev')
    add('m1',pdnet[k],xc-67,P_LLY+166,xc-21,P_LLY+166+W*200,'dev')
    add('m1',psnet[k],xc+21,P_LLY+166,xc+67,P_LLY+166+W*200,'dev')
# ---- stage 2 (rails, rings, supply sources)
def s2(l,n,*r): add(l,n,*r); stage2.append((l,)+r)
s2('m1','GND',x_lo,RAIL_G[0],x_hi,RAIL_G[1]); s2('m1','VDD',x_lo,RAIL_V[0],x_hi,RAIL_V[1])
for k,xc in enumerate(xs):
    W=WP[k]
    vialis.append((xc-17,-274,xc+17,-240)); s2('m1','GND',xc+57,-230,xc+85,-60)
    bar=P_LLY+W*200+315; vialis.append((xc-17,bar,xc+17,bar+34)); s2('m1','VDD',xc-29,bar-10,xc+29,RAIL_V[0]+40)
    if k in p1: s2('m1','VDD',xc+57,P_LLY+166+W*200-60,xc+85,RAIL_V[0]+40)
# ---- stage 3 (signals)
def s3(l,n,*r): add(l,n,*r); stage3.append((l,)+r)
busx=collections.defaultdict(list)
for k,xc in enumerate(xs):
    top=P_LLY+226 if k in full else (TY[out[k]]+30 if out[k] in TY else 0)
    if k in full or out[k] in TY:
        s3('m1',out[k],xc-114,-60,xc-62,max(top,TY.get(out[k],0)+34))
    if out[k] in TY: busx[out[k]].append((xc-88,'dv'))
    if gate[k] in TY: busx[gate[k]].append((xc,'tie'))
for n,lst in busx.items():
    y=TY[n]; x1=min(x for x,_ in lst)-34; x2=max(x for x,_ in lst)+34
    s3('m2',n,x1,y-28,x2,y+28)
    for x,_ in lst:
        vias.append((n,x,y)); stage3.append(('via1',x-26,y-26,x+26,y+26))
        add('m1',n,x-26,y-26,x+26,y+26,'via'); add('m2',n,x-26,y-26,x+26,y+26,'via')
for kind,cs,o in groups:
    for j in range(len(cs)-1):
        a,b=xs[cs[j]],xs[cs[j+1]]; s3('m1',f'{o}_l{j}',a+40,P_LLY+260,b-40,P_LLY+300)
# ---------------- verification
idx=list(range(len(S))); par=idx[:]
def f(i):
    while par[i]!=i: par[i]=par[par[i]]; i=par[i]
    return i
def gap(a,b):
    dx=max(a[2]-b[4],b[2]-a[4],0); dy=max(a[3]-b[5],b[3]-a[5],0); return (dx*dx+dy*dy)**.5
for i,j in itertools.combinations(idx,2):
    if S[i][0]==S[j][0] and gap(S[i],S[j])==0: par[f(i)]=f(j)
# via rects belong to both layers, so m1 and m2 components merge through them
for i,j in itertools.combinations(idx,2):
    if S[i][6]=='via' and S[j][6]=='via' and S[i][2:6]==S[j][2:6]: par[f(i)]=f(j)
comp=collections.defaultdict(list)
for i in idx: comp[f(i)].append(i)
err=0
for c,m in comp.items():
    names={S[i][1] for i in m}
    if len(names)>1: err+=1; print('SHORT',names)
byname=collections.defaultdict(set)
for c,m in comp.items():
    for i in m:
        if S[i][6]!='ext': byname[S[i][1]].add(c)
for n,cs in byname.items():
    if len(cs)>1: err+=1; print('OPEN',n,len(cs),'pieces')
print('nets:',len(byname),'-> every net one piece, no shorts' if not err else '')

# via enclosure rule: in at least one direction the metal must extend >=6 past the 52-unit tile on both sides
for n,x,y in vias:
    vx1,vy1,vx2,vy2=x-26,y-26,x+26,y+26
    for layer in ('m1','m2'):
        R=[r for r in S if r[0]==layer and r[6]!='via' and r[1]==n]
        okx=any(r[2]<=vx1-6 and r[4]>=vx2+6 and r[3]<=vy1 and r[5]>=vy2 for r in R)
        oky=any(r[3]<=vy1-6 and r[5]>=vy2+6 and r[2]<=vx1 and r[4]>=vx2 for r in R)
        if not (okx or oky): print('VIA ENCLOSURE',layer,n,x,y); err+=1
print('via enclosure rule checked for',len(vias),'vias x 2 layers; errors:',err)
sp=0
RULE={'m1':28,'m2':28}
for i,j in itertools.combinations(idx,2):
    if S[i][0]==S[j][0] and f(i)!=f(j):
        g=gap(S[i],S[j])
        if g<RULE[S[i][0]] and S[i][6]!='via' and S[j][6]!='via': sp+=1; print('SPACING',g,S[i],S[j])
vs=[(x,y,n) for n,x,y in vias]
for (a,b,n),(c,d,m) in itertools.combinations(vs,2):
    if n!=m and max(abs(a-c),abs(b-d))<52+34: sp+=1; print('VIA SPACING',n,m)
print('spacing violations:',sp,' errors:',err)
for l,*r in stage2+stage3:
    if l!='via1': assert min(r[2]-r[0],r[3]-r[1])>=28,(l,r)
# ---------------- emit
H=['snap internal','proc um {n} { return "[format %.3f [expr {$n * 0.005}]]um" }',
   'proc rp {layer x1 y1 x2 y2} { box values [um $x1] [um $y1] [um $x2] [um $y2]; paint $layer }','load arbiter4']
T=['box values 0um 0um 0um 0um','catch {view}','save arbiter4','drc check','drc catchup']
def emit(name,lines,msg):
    open(os.path.join(OUT,name),'w').write('\n'.join(H+lines+T+[f'puts "{msg} DRC count follows:"','drc count'])+'\n')
emit('stage2_rails.tcl',['rp viali %d %d %d %d'%v for v in vialis]+['rp metal1 %d %d %d %d'%r[1:] for r in stage2],'STAGE2 done.')
L=[('rp metal1 %d %d %d %d'%r[1:]) if r[0]=='m1' else ('rp metal2 %d %d %d %d'%r[1:]) for r in stage3 if r[0]!='via1']
L+=['rp via1 %d %d %d %d'%r[1:] for r in stage3 if r[0]=='via1']
emit('stage3_signals.tcl',L,'STAGE3 done.')
print(len(stage2),'stage2 rects,',len(stage3),'stage3 shapes written')

