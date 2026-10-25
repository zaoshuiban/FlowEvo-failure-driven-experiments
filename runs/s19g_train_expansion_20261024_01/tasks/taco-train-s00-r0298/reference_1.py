from sys import stdin, stdout

def main():
	p = 1000000007
	(n, h) = readline()
	a = list(readline())
	for i in range(n):
		a[i] = h - a[i]
		if a[i] < 0:
			return 0
	if a[0] > 1 or a[n - 1] > 1:
		return 0
	for i in range(n - 1, 0, -1):
		a[i] -= a[i - 1]
		if a[i] > 1 or a[i] < -1:
			return 0
	answer = 1
	count = 0
	for i in range(n):
		if a[i] == 1:
			count = count + 1 % p
		elif a[i] == -1:
			answer = answer * count % p
			count -= 1
		else:
			answer = answer * (count + 1) % p
	return answer

def readline():
	return map(int, stdin.readline().strip().split())
stdout.write(str(main()) + '\n')
