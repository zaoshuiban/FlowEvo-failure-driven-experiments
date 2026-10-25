from sys import stdin

def iinput():
	return int(stdin.readline())

def sinput():
	return input()

def minput():
	return map(int, stdin.readline().split())

def linput():
	return list(map(int, stdin.readline().split()))
(a, m) = minput()
ans = 'No'
for k in range(21):
	if a * 2 ** k % m == 0:
		ans = 'Yes'
		break
print(ans)
