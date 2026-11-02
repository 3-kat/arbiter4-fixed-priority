import re,collections,runpy,sys,io,os
ns=runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)),'gen_all.py'))
gate,out,pdnet,psnet,WP,groups=ns['gate'],ns['out'],ns['pdnet'],ns['psnet'],ns['WP'],ns['groups']
def ren(n):
    m=re.match(r'(gnt\d)_l(\d+)$',n)
    if not m: return n
    o=m.group(1); size=next(len(cs) for k,cs,oo in groups if oo==o)
    return f'{o}_p{size-1-int(m.group(2))}'
lay=collections.Counter()
for k in range(14):
    lay[('p',float(WP[k]),gate[k],frozenset({ren(pdnet[k]),ren(psnet[k])}))]+=1
    lay[('n',1.0,gate[k],frozenset({out[k],'GND'}))]+=1
ref=collections.Counter()
for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','schematic','arbiter4_ref.spice')):
    m=re.match(r'XM([NP])\d+ (\S+) (\S+) (\S+) (\S+) \S+ L=0.15 W=(\S+)',l)
    if m: ref[(m.group(1).lower(),float(m.group(6)),m.group(3),frozenset({m.group(2),m.group(4)}))]+=1
print('devices layout/ref:',sum(lay.values()),sum(ref.values()),' identical:',lay==ref)
for d in (lay-ref,ref-lay): print(dict(d))
