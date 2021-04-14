import sys
is_debugging=False
numerics = lambda s:''.join([ch for ch in s if (ch.isdigit() or (ch == '.'))])
normalize = lambda n:eval(n) if (len(n) > 0) else 0.0
d = {}
l = sys.argv[1:]
if (is_debugging):
    print('BEGIN:')
for item in l:
    n = normalize(numerics(item))
    if (item.endswith('m')):
        n += 0.01
    d[n] = item
    if (is_debugging):
        print('{} -> {}'.format(item, n))
if (is_debugging):
    print('END!!!')
l=sorted(list(d.keys()))
items = []
for i in l:
    items.append(d.get(i))
print('{}'.format(' '.join(items)))