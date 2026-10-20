"""Tiny s-expression reader for KiCad 9/10 .kicad_sch, used to plan schematic surgery."""
import re, sys

def tokenize(text):
    return re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^()\s"]+', text)

def parse(tokens):
    stack = [[]]
    for t in tokens:
        if t == '(':
            stack.append([])
        elif t == ')':
            done = stack.pop()
            stack[-1].append(done)
        else:
            stack[-1].append(t)
    return stack[0]

def unquote(s):
    if isinstance(s, str) and s.startswith('"'):
        return s[1:-1].replace('\\"', '"')
    return s

def find(node, name):
    out = []
    if isinstance(node, list):
        if node and node[0] == name:
            out.append(node)
        for c in node:
            out.extend(find(c, name))
    return out

def prop(node, name):
    for p in find(node, 'property'):
        if unquote(p[1]) == name:
            return unquote(p[2]) if len(p) > 2 else ''
    return ''

def main(path):
    tree = parse(tokenize(open(path).read()))
    syms = find(tree, 'symbol')
    print('== instances ==')
    for s in syms:
        if not any(isinstance(c, list) and c[0] == 'lib_id' for c in s):
            continue  # library-defined nested symbol, not a placed instance
        lib = unquote(s[1]) if isinstance(s[1], str) else ''
        at = [c for c in s if isinstance(c, list) and c[0] == 'at']
        xy = [float(x) for x in at[0][1:3]] if at else None
        ang = at[0][3] if at and len(at[0]) > 3 else '0'
        print(f'{prop(s,"Reference") or prop(s,"Value"):>10}  {lib:34} at {xy} angle {ang}  uuid={prop(s,"uuid") or ""}')
    print('== wires ==')
    for w in find(tree, 'wire'):
        pts = [c for c in w if isinstance(c, list) and c[0] == 'pts'][0]
        a = (float(pts[1][1]), float(pts[1][2]))
        b = (float(pts[2][1]), float(pts[2][2]))
        print(f'{a} -> {b}')
    print('== labels / power / text ==')
    for kind in ('label', 'global_label', 'text', 'hierarchical_label'):
        for l in find(tree, kind):
            print(kind, [unquote(x) if isinstance(x, str) else x for x in l[1:4]])

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'nuc-fan-controller.kicad_sch')
