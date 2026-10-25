from collections import Counter

def f(s, k):
	l = list(s)
	l = sorted(l)
	base = l[:k]
	tt = l[k:]
	cnt = Counter(tt)
	cnt2 = Counter(base)
	mns = min(base)
	if tt:
		mn = max(tt)
		if len(cnt) == 1:
			i = mn
			k = cnt2[mns]
			tc = cnt[i]
			cc = cnt[i] // k
			tc -= cnt[i] // k * k
			t = i * cc
			for id in range(len(base)):
				if tc:
					base[id] += t + i
					tc -= 1
				else:
					base[id] += t
					break
		else:
			for i in cnt:
				base[0] += i * cnt[i]
	return max(base)
for _ in range(int(input())):
	(N, K) = map(int, input().strip().split())
	s = input()
	print(f(s, K))
