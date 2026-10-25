from math import ceil

def readline():
	return [int(c) for c in input().split()]

def main():
	(_n, h, k) = readline()
	a = readline()
	ans = 0
	stack = a[::-1]
	processor = 0
	while stack:
		while stack and processor + stack[-1] <= h:
			processor += stack.pop()
		processor -= min(processor, k)
		ans += 1
		if stack and processor + stack[-1] > h:
			diff = processor + stack[-1] - h
			rem = ceil(diff / k)
			ans += rem
			processor -= min(processor, rem * k)
	ans += ceil(processor / k)
	print(ans)
main()
