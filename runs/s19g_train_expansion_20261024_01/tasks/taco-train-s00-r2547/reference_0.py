for _ in range(int(input())):
	(n, k) = map(int, input().split())
	a = input()
	s = ['RGB' * (k // 3) + 'RGB'[:k % 3], 'GBR' * (k // 3) + 'GBR'[:k % 3], 'BRG' * (k // 3) + 'BRG'[:k % 3]]
	minn = n
	for i in range(n - k + 1):
		for j in s:
			total = 0
			for l in range(k):
				total += 1 if a[i + l] != j[l] else 0
			minn = min(total, minn)
			if minn == 0:
				break
		if minn == 0:
			break
	print(minn)
