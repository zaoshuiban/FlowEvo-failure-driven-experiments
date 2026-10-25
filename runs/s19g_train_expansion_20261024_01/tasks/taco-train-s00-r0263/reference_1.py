I = input
s = list(I())
S = len(s)
n = int(I())
t = 0
(*l,) = sorted(map(int, I().split()))
for i in range(S // 2):
	while t < n and l[t] <= i + 1:
		t += 1
	if t % 2:
		(s[i], s[S - i - 1]) = (s[S - i - 1], s[i])
print(''.join(s))
