import re, itertools
devs=[]
for line in open('arbiter4_ref.spice'):
    m=re.match(r'X(M[NP]\d+) (\S+) (\S+) (\S+) (\S+) sky130_fd_pr__([np])fet',line)
    if m: devs.append((m.group(6),m.group(2),m.group(3),m.group(4)))
print(len(devs),'devices')
bad=0
for combo in itertools.product([0,1],repeat=4):
    val={'VDD':1,'GND':0}
    for i,v in enumerate(combo): val[f'req{i}']=v
    for _ in range(20):
        par={}
        def f(a):
            while par.setdefault(a,a)!=a:
                par[a]=par[par[a]]; a=par[a]
            return a
        for k,d,g,s in devs:
            if g in val and ((k=='n' and val[g]==1) or (k=='p' and val[g]==0)):
                par[f(d)]=f(s)
        comps={}
        for n in set([x for t in devs for x in (t[1],t[3])]):
            comps.setdefault(f(n),set()).add(n)
        for c in comps.values():
            up='VDD' in c; dn='GND' in c
            assert not(up and dn),('short',combo)
            if up or dn:
                for n in c: val[n]=1 if up else 0
    r=combo
    exp=[r[0], r[1]&(1-r[0]), r[2]&(1-r[1])&(1-r[0]), r[3]&(1-r[2])&(1-r[1])&(1-r[0])]
    got=[val.get(f'gnt{i}') for i in range(4)]
    if got!=exp: bad+=1; print('MISMATCH',combo,got,exp)
print('mismatches:',bad)
