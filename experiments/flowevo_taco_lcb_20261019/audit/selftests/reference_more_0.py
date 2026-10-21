import sys
input = sys.stdin.readline

def solution(n):
	current = n - 1
	r = int(current ** 0.5)
	if r ** 2 < current:
		r += 1
	first = r ** 2 - current
	if first == 0:
		return list(range(n))
	return list(range(first, n)) + solution(first)
t = int(input())
for _ in range(t):
	n = int(input())
	result = solution(n)
	print(' '.join(map(str, result[::-1])))
