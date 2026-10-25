t = list(input())
p = list(input())
s = input().split()
v = [0] * len(s)
for i in range(len(s)):
	v[i] = int(s[i])
(l, r) = (0, len(t))
while r - l > 1:
	m = (l + r) // 2
	t1 = t[:]
	for i in range(m):
		t1[v[i] - 1] = '*'
	(i, j) = (0, 0)
	while j < len(t1) and i < len(p):
		if p[i] == t1[j]:
			i += 1
		j += 1
	if i == len(p):
		l = m
	else:
		r = m
print(l)
