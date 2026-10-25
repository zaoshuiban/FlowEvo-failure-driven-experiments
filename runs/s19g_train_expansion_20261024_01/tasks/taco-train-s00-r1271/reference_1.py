t = int(input())
for w in range(t):
	(n, x) = map(int, input().split())
	a = list(map(int, input().split()))
	pr = True
	for i in range(n - 1):
		if a[i] != a[i + 1]:
			pr = False
			break
	if pr and a[0] == x:
		print(0)
		continue
	pr = False
	for i in range(n):
		if a[i] == x:
			pr = True
			break
	if pr:
		print(1)
		continue
	s = 0
	for q in a:
		s += q
	if n * x == s:
		print(1)
	else:
		print(2)
