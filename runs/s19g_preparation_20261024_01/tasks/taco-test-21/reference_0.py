import heapq

def solution(n: int, arr: [[int]]) -> [int]:
	queue = []
	heap = []
	result = []
	lastIndex = 0
	for i in arr:
		if i[0] == 1:
			lastIndex += 1
			element = [-i[1], lastIndex, False]
			queue.append(element)
			heapq.heappush(heap, element)
		if i[0] == 2:
			customer = queue.pop(0)
			while customer[2] == True:
				customer = queue.pop(0)
			customer[2] = True
			result.append(customer[1])
		if i[0] == 3:
			customer = heapq.heappop(heap)
			while customer[2] == True:
				customer = heapq.heappop(heap)
			customer[2] = True
			result.append(customer[1])
	return result

def main():
	n = int(input())
	arr = [[int(j) for j in input().split(' ')] for i in range(n)]
	print(' '.join([str(i) for i in solution(n, arr)]))
main()
