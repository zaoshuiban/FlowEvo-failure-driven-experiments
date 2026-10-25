import sys
input = sys.stdin.buffer.readline

def main():
	q = int(input())
	for _ in range(q):
		(n, k) = map(int, input().split())
		s = str(input())
		s = s[2:len(s) - 3]
		X = [[0] * 3 for _ in range(n + 1)]
		for i in range(n):
			if i % 3 == 0:
				if s[i] == 'R':
					X[i + 1][0] = 1
				elif s[i] == 'G':
					X[i + 1][1] = 1
				else:
					X[i + 1][2] = 1
			elif i % 3 == 1:
				if s[i] == 'G':
					X[i + 1][0] = 1
				elif s[i] == 'B':
					X[i + 1][1] = 1
				else:
					X[i + 1][2] = 1
			elif s[i] == 'B':
				X[i + 1][0] = 1
			elif s[i] == 'R':
				X[i + 1][1] = 1
			else:
				X[i + 1][2] = 1
		for i in range(n):
			for j in range(3):
				X[i + 1][j] += X[i][j]
		ans = 10 ** 18
		for i in range(n - k + 1):
			temp = 0
			for j in range(3):
				temp = max(temp, X[i + k][j] - X[i][j])
			ans = min(ans, k - temp)
		print(ans)
main()
