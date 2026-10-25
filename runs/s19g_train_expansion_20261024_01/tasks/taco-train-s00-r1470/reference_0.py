sequence = input()

def maximum_length(sequence):
	opened = 0
	closed = 0
	for bracket in sequence:
		if bracket == '(':
			opened += 1
		elif opened > 0:
			closed += 1
			opened -= 1
	return closed * 2
print(maximum_length(sequence))
