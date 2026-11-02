import re, sys, collections
txt = open('arbiter4.sch').read()

wires = [tuple(map(int, m.groups())) for m in re.finditer(r'^N (-?\d+) (-?\d+) (-?\d+) (-?\d+) \{\}', txt, re.M)]
comps = []
for m in re.finditer(r'^C \{(\S+?)\} (-?\d+) (-?\d+) (\d) (\d) \{([^{}]*)\}', txt, re.M):
    sym, x, y, rot, flip, props = m.groups()
    comps.append((sym.split('/')[-1], int(x), int(y), int(flip), props))

PINS = {
    'nfet_01v8.sym': {'G': (-20, 0), 'B': (20, 0), 'D': (20, -30), 'S': (20, 30)},
    'pfet_01v8.sym': {'G': (-20, 0), 'B': (20, 0), 'D': (20, 30), 'S': (20, -30)},
    'ipin.sym': {'p': (20, 0)}, 'opin.sym': {'p': (-20, 0)},
    'iopin.sym': {'p': (-20, 0)}, 'lab_pin.sym': {'p': (0, 0)},
}

parent = {}
def find(a):
    parent.setdefault(a, a)
    while parent[a] != a:
        parent[a] = parent[parent[a]]; a = parent[a]
    return a
def union(a, b): parent[find(a)] = find(b)

objs = collections.defaultdict(list)       # point -> list of (what)
for (x1, y1, x2, y2) in wires:
    union((x1, y1), (x2, y2)); objs[(x1, y1)].append('wire'); objs[(x2, y2)].append('wire')

term = {}      # (device, pin) -> point
labels = collections.defaultdict(set)
for sym, x, y, flip, props in comps:
    for pin, (dx, dy) in PINS[sym].items():
        if flip: dx = -dx
        pt = (x + dx, y + dy); find(pt)
        objs[pt].append(sym)
        if sym.startswith(('nfet', 'pfet')):
            name = re.search(r'name=(\S+)', props).group(1); term[(name, pin)] = pt
        else:
            labels[pt].add(re.search(r'lab=(\S+)', props).group(1))

errors = []
# xschem merges every pin/label that carries the same name into one net
byname = collections.defaultdict(list)
for pt, ls in labels.items():
    for l in ls: byname[l].append(pt)
for l, ps in byname.items():
    for p in ps[1:]: union(ps[0], p)
# 1) nothing may touch the interior of a wire (xschem would connect it)
pts = set(objs)
for (x1, y1, x2, y2) in wires:
    for p in pts:
        if p in ((x1, y1), (x2, y2)): continue
        if x1 == x2 == p[0] and min(y1, y2) < p[1] < max(y1, y2): errors.append(('T-touch', p, (x1, y1, x2, y2)))
        if y1 == y2 == p[1] and min(x1, x2) < p[0] < max(x1, x2): errors.append(('T-touch', p, (x1, y1, x2, y2)))
# 2) every pin / label must touch at least one other object
for p, o in objs.items():
    if len(o) < 2: errors.append(('dangling', p, o))
# 3) net names
rootname = collections.defaultdict(set)
for pt, ls in labels.items(): rootname[find(pt)] |= ls
for r, ls in rootname.items():
    if len(ls) > 1: errors.append(('SHORT between names', ls))

# 4) compare with intended netlist
intended = {}
for line in open('arbiter4_ref.spice'):
    m = re.match(r'X(M[NP]\d+) (\S+) (\S+) (\S+) (\S+) sky130', line)
    if m:
        n, d, g, s, b = m.groups()
        intended.update({(n, 'D'): d, (n, 'G'): g, (n, 'S'): s, (n, 'B'): b})
fwd, back = {}, {}
for key, net in intended.items():
    r = find(term[key])
    if fwd.setdefault(net, r) != r: errors.append(('net split', net, key))
    if back.setdefault(r, net) != net: errors.append(('nets merged', net, back[r], key))
    named = net.startswith(('req', 'nreq', 'gnt', 'VDD', 'GND')) and '_p' not in net
    if named and rootname.get(r) != {net}: errors.append(('wrong/missing label', net, key, rootname.get(r)))
print('devices:', len({k[0] for k in intended}), ' nets:', len(fwd), ' wires:', len(wires))
print('ERRORS:' if errors else 'connectivity OK - every terminal sits on the intended net, no shorts, no dangling pins')
for e in errors[:20]: print(' ', e)
