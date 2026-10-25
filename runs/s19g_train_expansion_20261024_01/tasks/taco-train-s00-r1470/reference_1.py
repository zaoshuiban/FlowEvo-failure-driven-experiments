s = input()
l = list(s)
pile = list()
k = 0
for i in l:
	if i == '(':
		pile.append(i)
	elif i == ')':
		if len(pile) != 0:
			k += 1
			pile.pop()
print(2 * k)
