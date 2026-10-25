from collections import Counter
import functools

def main():
	n = int(input())
	arr = [int(i) for i in input().split(' ')]
	arr.sort(reverse=True)
	mean = sum(arr) // n
	err = 0
	new_arr = [mean for i in range(n)]
	for i in range(len(arr)):
		err += arr[i] - mean
	for i in range(n):
		if err == 0:
			break
		new_arr[i] += 1
		err -= 1
	res = 0
	for i in range(n):
		res += abs(arr[i] - new_arr[i])
	print(res // 2)
main()
