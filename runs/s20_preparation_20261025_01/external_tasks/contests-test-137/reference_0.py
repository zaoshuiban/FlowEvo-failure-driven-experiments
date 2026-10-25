#import io,os
#input = io.BytesIO(os.read(0, os.fstat(0).st_size)).readline
from collections import deque 





def main(t):

    x, y = map(int,input().split())
    sx, sy = bin(x)[2:],bin(y)[2:]



    dic = {}
    queue = deque()
    queue.append(sx)
    dic[sx] = 1

    i = len(sx)-1
    while i>=0 and sx[i]=='0':  i -= 1
    queue.append(sx[:i+1])
    dic[sx[:i+1]] = 1

#    print(dic)
    
    




    while queue:
        curr = queue.popleft()
        nextcurr1 = curr[::-1]
        i = 0
 
        while nextcurr1[i]=='0': i += 1
        nextcurr1 = nextcurr1[i:]
        if nextcurr1 not in dic:
            dic[nextcurr1] = 1
            queue.append(nextcurr1)
        nextcurr2 = (curr + '1')[::-1]
        if nextcurr2 not in dic:
            dic[nextcurr2] = 1
            if len(nextcurr2) <= len(sy): queue.append(nextcurr2)


 #   print(dic)

    if sy in dic:  
        print("YES")
    else:
        print("NO")
        



























T = 1 #int(input())
t = 1
while t<=T:
    main(t)
    t += 1
