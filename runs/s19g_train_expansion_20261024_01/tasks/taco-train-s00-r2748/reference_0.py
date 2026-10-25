mod = 10 ** 9 + 7
MAX = 2 * 10 ** 5 + 1
r = [1] * MAX
factorial = [1] * MAX
rfactorial = [1] * MAX
rp = [1] * MAX
for i in range(2, MAX):
	factorial[i] = i * factorial[i - 1] % mod
	r[i] = mod - mod // i * r[mod % i] % mod
	rfactorial[i] = rfactorial[i - 1] * r[i] % mod
for i in range(1, MAX):
	rp[i] = rp[i - 1] * (mod + 1) // 2 % mod
(n, T) = list(map(int, input().split()))
t = list(map(int, input().split()))
t.append(10 ** 10 + 1)
S = 0
EX = 0
for i in range(len(t)):
	cof = rp[1]
	for add in range(2):
		(l_, r_) = (max(0, T - S - t[i] + add), min(i, T - S))
		for x in range(l_, r_ + 1):
			EX = (EX + i * (factorial[i] * rfactorial[x] * rfactorial[i - x]) * rp[i] * cof) % mod
	S += t[i]
print(EX)
