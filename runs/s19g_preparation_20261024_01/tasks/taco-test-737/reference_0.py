from collections import Counter
(counterX, counterY, counterXY) = (Counter(), Counter(), Counter())
ans = 0
for i in range(int(input())):
	(x, y) = map(int, input().split())
	ans += counterX[x] + counterY[y] - counterXY[x, y]
	counterX[x] += 1
	counterY[y] += 1
	counterXY[x, y] += 1
print(ans)
