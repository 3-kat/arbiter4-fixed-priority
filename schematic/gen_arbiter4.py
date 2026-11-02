#!/usr/bin/env python3
"""
gen_arbiter4.py - 4-request fixed-priority arbiter for sky130A (xschem + SPICE)

  gnt0 = req0
  gnt1 = req1 & ~req0
  gnt2 = req2 & ~req1 & ~req0
  gnt3 = req3 & ~req2 & ~req1 & ~req0

Schematic style: every gate is drawn with real wires (VDD/GND rails, series
PMOS stack, parallel NMOS, output bus).  Only the signals that travel between
gates (req0..3, nreq0..3) use net labels, plus the top-level ports.

Outputs (current directory):
  arbiter4.sch        xschem schematic     ->  xschem arbiter4.sch
  arbiter4_ref.spice  plain SPICE subckt   ->  use for LVS / Cadence import
  tb_arbiter4.spice   ngspice testbench    ->  ngspice tb_arbiter4.spice
"""

PITCH, GAP = 320, 80          # column pitch, gap between gates
ROW_DY = 900                  # vertical distance between the two schematic rows
YP, YN = -100, 100            # PMOS / NMOS centre (xschem: y grows downward)
Y_VDD, Y_GND = -260, 260      # rail heights (relative to row origin)
X0 = 0

# ---------------------------------------------------------------- circuit ---
groups = [
    dict(t='INV: nreq0 = ~req0',              ins=['req0'],  out='nreq0', wp=2.0, row=0),
    dict(t='INV: gnt0 = ~nreq0 (= req0)',     ins=['nreq0'], out='gnt0',  wp=2.0, row=0),
    dict(t='INV: nreq1 = ~req1',              ins=['req1'],  out='nreq1', wp=2.0, row=0),
    dict(t='INV: nreq2 = ~req2',              ins=['req2'],  out='nreq2', wp=2.0, row=0),
    dict(t='INV: nreq3 = ~req3',              ins=['req3'],  out='nreq3', wp=2.0, row=0),
    dict(t='NOR2: gnt1 = ~(nreq1 | req0)',
         ins=['nreq1', 'req0'], out='gnt1', wp=4.0, row=0),
    dict(t='NOR3: gnt2 = ~(nreq2 | req1 | req0)',
         ins=['nreq2', 'req1', 'req0'], out='gnt2', wp=6.0, row=1),
    dict(t='NOR4: gnt3 = ~(nreq3 | req2 | req1 | req0)',
         ins=['nreq3', 'req2', 'req1', 'req0'], out='gnt3', wp=8.0, row=1),
]

def columns(g):
    """One column = (PMOS, NMOS) sharing a gate input.
    Transistor tuple: (kind, drain, gate, source, bulk, W).
    PMOS are in series from VDD to the output, NMOS in parallel to GND."""
    ins, out, wp = g['ins'], g['out'], g['wp']
    k = len(ins)
    cols = []
    for i, gate in enumerate(ins):
        s = 'VDD' if i == 0 else f'{out}_p{i}'
        d = out if i == k - 1 else f'{out}_p{i + 1}'
        cols.append((('p', d, gate, s, 'VDD', wp),
                     ('n', out, gate, 'GND', 'GND', 1.0)))
    return cols

# ------------------------------------------------------------ layout setup ---
cursor = {0: X0 + 200, 1: X0 + 200}
for g in groups:
    r = g['row']
    g['x0'] = cursor[r]
    g['oy'] = r * ROW_DY
    cursor[r] += len(g['ins']) * PITCH + GAP

# ------------------------------------------------------------ xschem output ---
AD = ('ad="\'int((nf+1)/2) * W/nf * 0.29\'"\n'
      'as="\'int((nf+2)/2) * W/nf * 0.29\'"\n'
      'pd="\'2*int((nf+1)/2) * (W/nf + 0.29)\'"\n'
      'ps="\'2*int((nf+2)/2) * (W/nf + 0.29)\'"\n'
      'nrd="\'0.29 / W\'"\n'
      'nrs="\'0.29 / W\'"\n')

wires, comps, texts = [], [], []
devices = []                     # (name, kind, d, g, s, b, W)
cn = {'n': 0, 'p': 0}
vdd_x = {0: [], 1: []}
gnd_x = {0: [], 1: []}
lab_id = [0]

def wire(x1, y1, x2, y2):
    if (x1, y1) != (x2, y2):
        wires.append((x1, y1, x2, y2))

def lab_pin(x, y, net, rot=0):
    lab_id[0] += 1
    comps.append(f'C {{devices/lab_pin.sym}} {x} {y} {rot} 0 '
                 f'{{name=l{lab_id[0]} sig_type=std_logic lab={net}}}')

def port(sym, x, y, name, net, flip=0):
    comps.append(f'C {{devices/{sym}.sym}} {x} {y} 0 {flip} {{name={name} lab={net}}}')

def fet(kind, W, x, y):
    cn[kind] += 1
    name = f'M{kind.upper()}{cn[kind]}'
    sym = 'nfet_01v8' if kind == 'n' else 'pfet_01v8'
    comps.append(
        f'C {{sky130_fd_pr/{sym}.sym}} {x} {y} 0 0 {{name={name}\n'
        f'L=0.15\nW={W}\nnf=1\nmult=1\n{AD}sa=0 sb=0 sd=0\n'
        f'model={sym}\nspiceprefix=X\n}}')
    return name

# pin offsets of the sky130 xschem symbols:
#   nfet: G(-20,0) B(20,0) D(20,-30) S(20,30)
#   pfet: G(-20,0) B(20,0) D(20,30)  S(20,-30)
for g in groups:
    oy, x0, ins, out = g['oy'], g['x0'], g['ins'], g['out']
    k = len(ins)
    r = g['row']
    yp, yn = oy + YP, oy + YN
    texts.append((g['t'], x0 - 100, oy + Y_VDD - 60))

    for ci, ((p, n), gate) in enumerate(zip(columns(g), ins)):
        x = x0 + ci * PITCH
        pname = fet('p', p[5], x, yp)
        nname = fet('n', n[5], x, yn)
        devices.append((pname,) + p)
        devices.append((nname,) + n)

        # ---- gate inputs
        if k == 1:      # inverter: both gates tied, one input stub
            wire(x - 20, yp, x - 60, yp)
            wire(x - 20, yn, x - 60, yn)
            wire(x - 60, yp, x - 60, oy)
            wire(x - 60, oy, x - 60, yn)
            wire(x - 60, oy, x - 100, oy)
            if gate.startswith('req'):
                port('ipin', x - 120, oy, f'pi_{gate}', gate)     # pin at +20
            else:
                lab_pin(x - 100, oy, gate, 2)
        else:           # NOR column: label on each gate
            wire(x - 20, yp, x - 60, yp); lab_pin(x - 60, yp, gate, 2)
            wire(x - 20, yn, x - 60, yn); lab_pin(x - 60, yn, gate, 2)

        # ---- PMOS source / bulk
        if ci == 0:     # top of the stack: source+bulk to VDD rail
            wire(x + 20, yp, x + 50, yp)
            wire(x + 50, yp, x + 50, yp - 30)
            wire(x + 50, yp - 30, x + 20, yp - 30)
            wire(x + 20, yp - 30, x + 20, oy + Y_VDD)
            vdd_x[r].append(x + 20)
        else:           # bulk to VDD by label; source comes from previous column
            wire(x + 20, yp, x + 50, yp)
            lab_pin(x + 50, yp, 'VDD', 0)

        # ---- PMOS drain
        if ci == k - 1:                         # last in stack: down to output bus
            wire(x + 20, yp + 30, x + 20, oy)
        else:                                   # feed next PMOS source, routed above
            xn = x + PITCH
            wire(x + 20, yp + 30, x + 140, yp + 30)
            wire(x + 140, yp + 30, x + 140, yp - 70)
            wire(x + 140, yp - 70, xn + 20, yp - 70)
            wire(xn + 20, yp - 70, xn + 20, yp - 30)

        # ---- NMOS source / bulk to GND rail, drain up to output bus
        wire(x + 20, yn, x + 50, yn)
        wire(x + 50, yn, x + 50, yn + 30)
        wire(x + 50, yn + 30, x + 20, yn + 30)
        wire(x + 20, yn + 30, x + 20, oy + Y_GND)
        gnd_x[r].append(x + 20)
        wire(x + 20, yn - 30, x + 20, oy)

        # ---- output bus between columns
        if ci > 0:
            wire(x - PITCH + 20, oy, x + 20, oy)

    xl = x0 + (k - 1) * PITCH + 20
    if out.startswith('gnt'):
        wire(xl, oy, xl + 60, oy)
        port('opin', xl + 80, oy, f'po_{out}', out)               # pin at -20
    else:
        wire(xl, oy, xl + 40, oy)
        lab_pin(xl + 40, oy, out, 0)

# ---- rails
for r in (0, 1):
    xs = [g['x0'] for g in groups if g['row'] == r]
    rl = min(xs) - 200
    for rail_y, drops, net, pname in ((Y_VDD, vdd_x[r], 'VDD', 'pv'),
                                      (Y_GND, gnd_x[r], 'GND', 'pg')):
        y = r * ROW_DY + rail_y
        pts = sorted(set([rl] + drops))
        for a, b in zip(pts, pts[1:]):
            wire(a, y, b, y)
        if r == 0:
            port('iopin', rl - 20, y, pname, net, flip=1)         # mirrored: pin at +20
        else:
            lab_pin(rl, y, net, 2)

sch = ['v {xschem version=3.4.5 file_version=1.2\n}\nG {}\nK {}\nV {}\nS {}\nE {}']
sch += [f'N {a} {b} {c} {d} {{}}' for a, b, c, d in wires]
sch += comps
sch += [f'T {{{t}}} {x} {y} 0 0 0.4 0.4 {{}}' for t, x, y in texts]
open('arbiter4.sch', 'w').write('\n'.join(sch) + '\n')

# ---------------------------------------------------- reference spice file ---
sp = ['* 4-request fixed-priority arbiter (generated, sky130A)',
      '.subckt arbiter4 req0 req1 req2 req3 gnt0 gnt1 gnt2 gnt3 VDD GND']
for name, kind, d, g_, s, b, W in devices:
    m = 'sky130_fd_pr__nfet_01v8' if kind == 'n' else 'sky130_fd_pr__pfet_01v8'
    sp.append(f'X{name} {d} {g_} {s} {b} {m} L=0.15 W={W} nf=1 mult=1')
sp.append('.ends arbiter4')
open('arbiter4_ref.spice', 'w').write('\n'.join(sp) + '\n')

# --------------------------------------------------------------- testbench ---
tb = ['* testbench for arbiter4',
      '.lib /foss/pdks/sky130A/libs.tech/ngspice/sky130.lib.spice tt',
      '.include arbiter4_ref.spice',
      'Vdd VDD 0 1.8',
      'Vr0 req0 0 PULSE(0 1.8 0 100p 100p 0.5u 1u)',
      'Vr1 req1 0 PULSE(0 1.8 0 100p 100p 1u 2u)',
      'Vr2 req2 0 PULSE(0 1.8 0 100p 100p 2u 4u)',
      'Vr3 req3 0 PULSE(0 1.8 0 100p 100p 4u 8u)',
      'Xdut req0 req1 req2 req3 gnt0 gnt1 gnt2 gnt3 VDD GND arbiter4']
tb += [f'Cl{i} gnt{i} 0 10f' for i in range(4)]
tb += ['.tran 10n 8u',
       '.control',
       'run',
       'plot req0 req1+2 req2+4 req3+6 title "requests (offset)"',
       'plot gnt0 gnt1+2 gnt2+4 gnt3+6 title "grants (offset)"',
       '.endc',
       '.end']
open('tb_arbiter4.spice', 'w').write('\n'.join(tb) + '\n')

print(f'{len(devices)} transistors, {len(wires)} wires written')
print('files: arbiter4.sch  arbiter4_ref.spice  tb_arbiter4.spice')
