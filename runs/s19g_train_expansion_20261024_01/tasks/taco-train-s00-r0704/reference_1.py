N = int(input())
zerocount = 0
tzero = []
tarr = [0]
s = []
larr = [0 for i in range(5 * 10 ** 5 + 100)]
rarr = [0 for i in range(5 * 10 ** 5 + 100)]
for i in range(N):
	s.append(input())
s = sorted(s)
for i in range(N):
	left = 0
	right = 0
	for j in range(len(s[i])):
		if s[i][j] == '(':
			left += 1
		if s[i][j] == ')':
			if left > 0:
				left -= 1
			else:
				right += 1
	if left == 0 and right == 0:
		zerocount += 1
	else:
		if left == 0 and right > 0:
			rarr[right] += 1
		if right == 0 and left > 0:
			larr[left] += 1
ans = 0
if zerocount > 1:
	ans += zerocount // 2
for i in range(5 * 10 ** 5 + 1):
	ans += min(larr[i], rarr[i])
print(ans)
