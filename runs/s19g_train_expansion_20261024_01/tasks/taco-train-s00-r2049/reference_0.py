import sys
input = sys.stdin.readline

def main():
	(n, h, k) = map(int, input().split())
	l = list(map(int, input().split()))
	ret = 0
	rem = 0
	for a in l:
		ret += rem // k
		rem %= k
		if rem + a <= h:
			rem += a
		else:
			ret += 1
			rem = a
	ret += (rem + k - 1) // k
	print(ret)
main()
