from math import gcd

class SegTree:

	def __init__(self, arr=None, length=None):
		if arr is not None:
			self.n = len(arr)
			self.t = [1 for _ in range(2 * self.n)]
			self.ct = [0] * self.n + [1] * self.n
			self.construct(arr)
		else:
			assert False
			self.n = length
			self.t = [1 for _ in range(2 * self.n)]

	def construct(self, arr):
		self.t[self.n:] = arr
		for i in reversed(range(0, self.n)):
			self.t[i] = gcd(self.t[i * 2], self.t[i * 2 + 1])
			if self.t[i] == self.t[i * 2]:
				self.ct[i] += self.ct[i * 2]
			if self.t[i] == self.t[i * 2 + 1]:
				self.ct[i] += self.ct[i * 2 + 1]

	def modify(self, p, val):
		p += self.n
		self.t[p] = val
		self.ct[p] = 1
		while p > 1:
			self.t[p // 2] = gcd(self.t[p], self.t[p ^ 1])
			self.ct[p // 2] = 0
			if self.t[p // 2] == self.t[p]:
				self.ct[p // 2] += self.ct[p]
			if self.t[p // 2] == self.t[p ^ 1]:
				self.ct[p // 2] += self.ct[p ^ 1]
			p //= 2

	def gcd_query(self, l, r):
		l += self.n
		r += self.n
		res = self.t[l]
		while l < r:
			if l & 1:
				res = gcd(res, self.t[l])
				l += 1
			if r & 1:
				r -= 1
				res = gcd(res, self.t[r])
			l //= 2
			r //= 2
		return res

	def query_num_eq_gcd(self, l, r):
		my_gcd = self.gcd_query(l, r)
		l += self.n
		r += self.n
		res = 0
		while l < r:
			if l & 1:
				if self.t[l] == my_gcd:
					res += self.ct[l]
				l += 1
			if r & 1:
				r -= 1
				if self.t[r] == my_gcd:
					res += self.ct[r]
			l //= 2
			r //= 2
		return res
import sys
n = int(input())
s = [int(x) for x in input().split()]
st = SegTree(arr=s)
t = int(input())
for _ in range(t):
	(l, r) = [int(x) for x in sys.stdin.readline().split()]
	print(r - l + 1 - st.query_num_eq_gcd(l - 1, r))
