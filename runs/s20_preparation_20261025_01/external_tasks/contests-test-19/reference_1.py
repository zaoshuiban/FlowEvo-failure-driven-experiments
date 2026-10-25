import io,os
import sys

input = io.BytesIO(os.read(0, os.fstat(0).st_size)).readline


    




def main(t):


    n = int(input())
    arr = list(map(int,input().split()))
 
    m = 2*max(arr)+1


    dp = [2147483647]*(m)
    dp[arr[0]] = arr[0]

    for i in range(1,n):
        newdp = [2147483647]*m
        for j in range(m):
            nextj = max(j-arr[i],0)
            newdp[nextj] = min( newdp[nextj], dp[j]+ max(arr[i]-j,0)  )


            if j+arr[i]<m:   newdp[j+arr[i]] = min( newdp[j+arr[i]], dp[j] + max(arr[i]-dp[j]+j, 0)  )

        dp = newdp



            
    





    ans = min(dp)
    print(ans)




















T = int(input())
t = 1
while t<=T:
    main(t)
    t += 1
