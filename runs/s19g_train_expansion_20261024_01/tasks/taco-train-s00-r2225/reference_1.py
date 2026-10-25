from itertools import permutations

def parse(s):
	return tuple(map(int, s.strip().split('.')))

def win(birth):
	print('YES')
	import sys
	sys.exit()
days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

def get_days_in_month(y, m):
	if y % 4 == 0 and m == 2:
		return 29
	return days_in_month[m - 1]
target = parse(input())
(D, M, Y) = target
given = parse(input())
feasible = False
for birth in permutations(given):
	(d, m, y) = birth
	if m > 12 or d > get_days_in_month(y, m):
		continue
	if y % 4 != 0 and (m, d) == (3, 1) and (Y % 4 == 0):
		(m, d) = (2, 29)
	if y % 4 == 0 and (m, d) == (2, 29) and (Y % 4 != 0):
		(m, d) = (3, 1)
	if Y - y > 18:
		win(birth)
	if Y - y == 18:
		if m < M:
			win(birth)
		if m == M and d <= D:
			win(birth)
print('NO')
