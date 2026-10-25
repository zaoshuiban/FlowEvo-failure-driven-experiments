import sys
t = int(sys.stdin.buffer.readline().decode('utf-8'))
ans = [''] * t
for _ in range(t):
	a = list(map(int, sys.stdin.buffer.readline().decode('utf-8').rstrip()))
	n = len(a)
	parity = [0] * 10
	for x in a:
		parity[x] ^= 1
	psum = sum(parity)
	for (i, free) in zip(range(n - 1, -1, -1), range(n)):
		psum += -1 if parity[a[i]] else 1
		parity[a[i]] ^= 1
		for j in range(a[i] - 1, -1, -1):
			if psum + (-1 if parity[j] else 1) - free <= 0:
				if i == 0 and j == 0:
					ans[_] = '9' * (n - 2)
					break
				parity[j] ^= 1
				a[i] = j
				for k in range(n - 1, i, -1):
					for l in range(10):
						if parity[l]:
							a[k] = l
							parity[l] = 0
							break
						else:
							a[k] = 9
				ans[_] = ''.join(map(str, a))
				break
		else:
			continue
		break
sys.stdout.buffer.write('\n'.join(ans).encode('utf-8'))
