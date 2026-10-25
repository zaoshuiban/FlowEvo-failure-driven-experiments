(n, k) = map(int, input().split())
skills = [int(i) for i in input().split()]
dic = {}
ret = []
s = sorted(skills)
dic[s[0]] = 0
for i in range(1, n):
	if s[i] != s[i - 1]:
		dic[s[i]] = i
s = [0] * n
for i in range(k):
	(a, b) = map(int, input().split())
	if skills[a - 1] > skills[b - 1]:
		s[a - 1] -= 1
	elif skills[a - 1] < skills[b - 1]:
		s[b - 1] -= 1
for i in range(n):
	print(dic[skills[i]] + s[i] if dic[skills[i]] + s[i] > 0 else 0, end=' ')
