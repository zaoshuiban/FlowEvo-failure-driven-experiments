queue = []
N, array = int(input()), []
for i in range(N):
	array.append([each for each in input().split(' ')])

def build():
	for i in range(N):
		for j in range(N):
			if array[i][j] == 'E':
				queue.append([i,j,0]); return

build()
while True:
	x = queue.pop(0)
	#print x
	if array[x[0]][x[1]] == 'S':
		print(x[2]); exit()
	if array[x[0]][x[1]] == 'T':
		continue
	if array[x[0]][x[1]] in ['P','E']:
		if x[0]<N-1 and array[x[0]+1][x[1]] in ['P','S']:
			queue.append([x[0]+1, x[1], x[2]+1])

		if x[0]>0 and array[x[0]-1][x[1]] in ['P','S']:
			queue.append([x[0]-1, x[1], x[2]+1])

		if x[1]<N-1 and array[x[0]][x[1]+1] in ['P','S']:
			queue.append([x[0], x[1]+1, x[2]+1])

		if x[1]>0 and array[x[0]][x[1]-1] in ['P','S']:
			queue.append([x[0], x[1]-1, x[2]+1])
		array[x[0]][x[1]] = 'X'
