import sys
o = {'G':'S', 'S':'G'};n = int(input());d = [list(input()[:n]) for _ in range(n)];f = [1] * (n * n);finished = 1
if n % 2: print('NONE'); sys.exit()
x = [''] * (n // 2)
def findt(i, j): return abs(j - i) // 2 if (j - i) % 2 else min(i + j, 2 * (n - 1) - j - i) // 2
def findr(i, j, t):
    if (j - i) % 2: return o[t] if min(i, j) % 2 else t
    else:
        if i + j < n: return o[t] if i % 2 else t
        else: return t if i % 2 else o[t]
for i in range(n):
    for j in range(n):
        if d[i][j] != '.':
            t = findt(i, j);r = findr(i, j, d[i][j])
            if x[t] == o[r]: print('NONE'); sys.exit()
            else: x[t] = r
for i in range(n // 2):
    if not x[i]: print('MULTIPLE'); sys.exit()
for i in range(n):
    for j in range(n):d[i][j] = findr(i, j, x[findt(i, j)])
print('UNIQUE')
print('\n'.join(''.join(d[i]) for i in range(n)))