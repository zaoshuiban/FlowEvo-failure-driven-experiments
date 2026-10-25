def maxSubArraySum(a, size):
	max_so_far = 0
	max_ending_here = 0
	for i in range(0, size):
		max_ending_here = max_ending_here + a[i]
		if max_ending_here < 0:
			max_ending_here = 0
		elif max_so_far < max_ending_here:
			max_so_far = max_ending_here
	return max_so_far
for _ in range(int(input())):
	n = int(input())
	l = [int(i) for i in input().split()][:n]
	evensum = 0
	for i in range(0, len(l), 2):
		evensum += l[i]
	(x, y) = ([], [])
	for i in range(1, len(l), 2):
		x.append(l[i] - l[i - 1])
		if i + 1 < len(l):
			y.append(l[i] - l[i + 1])
	p = maxSubArraySum(x, len(x))
	q = maxSubArraySum(y, len(y))
	add = max(p, q)
	if add > 0:
		evensum += add
	print(evensum)
