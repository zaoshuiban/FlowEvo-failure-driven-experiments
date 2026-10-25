from __future__ import print_function
import sys
import math
n = int(input())
M = list(map(int, input().split()))
avg = sum(M) / len(M)
ceil = math.ceil(avg)
floor = math.floor(avg)
ceil_count = 0
floor_count = 0
for m in M:
	if m > ceil:
		ceil_count = ceil_count + m - ceil
	if m < floor:
		floor_count = floor_count + floor - m
count = max(ceil_count, floor_count)
print(count)
