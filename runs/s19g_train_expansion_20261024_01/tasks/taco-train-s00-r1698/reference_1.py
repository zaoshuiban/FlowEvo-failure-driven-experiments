import sys
k = int(sys.stdin.buffer.readline().decode('utf-8'))
s = sys.stdin.buffer.readline().decode('utf-8').rstrip()
n = len(s)
(prev, words) = (-1, [])
for i in range(n):
	if s[i] == ' ' or s[i] == '-':
		words.append(i - prev)
		prev = i
words.append(n - prev - 1)
(ok, ng) = (n + 1, max(words) - 1)
while abs(ok - ng) > 1:
	mid = ok + ng >> 1
	(line, width) = (1, 0)
	for w in words:
		if width + w > mid:
			line += 1
			width = w
		else:
			width += w
	if line <= k:
		ok = mid
	else:
		ng = mid
print(ok)
