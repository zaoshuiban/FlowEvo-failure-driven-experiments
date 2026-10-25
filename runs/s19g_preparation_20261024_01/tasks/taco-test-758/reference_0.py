x = int(input()) % 360
a = [min(abs(x), abs(x - 360))] + [abs(x - y) for y in range(90, 360, 90)]
print(a.index(min(a)))
