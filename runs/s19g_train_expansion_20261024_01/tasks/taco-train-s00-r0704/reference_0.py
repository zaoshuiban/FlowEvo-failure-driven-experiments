n = int(input())
parr = {}
narr = {}
zero = 0
ans = 0
for i in range(n):
	s = input()
	x = 0
	y = 0
	left = True
	right = True
	for j in range(len(s)):
		if s[j] == '(':
			x += 1
		else:
			x -= 1
		if x < 0:
			left = False
		if s[-1 * (j + 1)] == '(':
			y += 1
		else:
			y -= 1
		if y > 0:
			right = False
	if left and right and (x == 0):
		zero += 1
	elif left or right:
		if x > 0:
			parr[x] = parr.get(x, 0) + 1
		else:
			narr[x] = narr.get(x, 0) + 1
ans += zero // 2
for i in narr.keys():
	ans += min(narr[i], parr.get(-i, 0))
print(ans)
