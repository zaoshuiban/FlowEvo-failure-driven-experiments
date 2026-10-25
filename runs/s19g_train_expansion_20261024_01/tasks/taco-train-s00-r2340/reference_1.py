import sys
import math
input = sys.stdin.readline
s = input().rstrip()
n = len(s)
q = int(input())

class segTree:

	def __init__(self):
		self.a = [0] * (2 * n)
		self.b = [0] * (2 * n)
		self.c = [0] * (2 * n)

	def build(self, arr):
		for i in range(n):
			self.a[i + n] = 0
			self.b[i + n] = 1 if arr[i] == '(' else 0
			self.c[i + n] = 1 if arr[i] == ')' else 0
		for i in range(n - 1, 0, -1):
			t = min(self.b[i << 1], self.c[i << 1 | 1])
			self.a[i] = self.a[i << 1] + self.a[i << 1 | 1] + 2 * t
			self.b[i] = self.b[i << 1] + self.b[i << 1 | 1] - t
			self.c[i] = self.c[i << 1] + self.c[i << 1 | 1] - t

	def query(self, l, r):
		left = []
		right = []
		l += n
		r += n
		while l <= r:
			if l & 1:
				left.append([self.a[l], self.b[l], self.c[l]])
				l += 1
			if not r & 1:
				right.append([self.a[r], self.b[r], self.c[r]])
				r -= 1
			l >>= 1
			r >>= 1
		a1 = b1 = c1 = 0
		for (a2, b2, c2) in left + right[::-1]:
			t = min(b1, c2)
			a1 += a2 + 2 * t
			b1 += b2 - t
			c1 += c2 - t
		return a1
tr = segTree()
tr.build(s)
for _ in range(q):
	(l, r) = map(int, input().split())
	print(tr.query(l - 1, r - 1))
