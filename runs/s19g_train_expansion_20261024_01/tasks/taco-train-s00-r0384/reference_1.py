n = int(input())
row = input()
g = 0
s = 0
m = 0
leng = []
lens = []
for i in range(n):
	if row[i] == 'G':
		g += 1
	elif g != 0:
		if g > m:
			m = g
		leng.append(g)
		g = 0
if row[n - 1] == 'G':
	leng.append(g)
	if g > m:
		m = g
for i in range(n):
	if row[i] == 'S':
		s += 1
	elif s != 0:
		lens.append(s)
		s = 0
if row[n - 1] == 'S':
	lens.append(s)
if len(leng) == 0:
	print(0)
elif len(leng) == 1:
	print(leng[0])
else:
	if row[0] == 'S':
		lens = lens[1:len(lens)]
	m += 1
	ans = m
	for i in range(1, len(leng)):
		if lens[i - 1] == 1:
			if len(leng) == 2:
				if leng[0] + leng[1] > ans:
					ans = leng[0] + leng[1]
			elif leng[i] + leng[i - 1] + 1 > ans:
				ans = leng[i] + leng[i - 1] + 1
	print(ans)
