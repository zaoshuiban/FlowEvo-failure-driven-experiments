import sys,os,io
# input = io.BytesIO(os.read(0, os.fstat(0).st_size)).readline
from collections import deque
input = sys.stdin.readline

def isGood(i,j):
    if (i<0 or j<0 or i>=n or j>=m or a[i][j]=='#' or a[i][j]=='L' or a[i][j]=='+'):
        return 0
    return 1


for _ in range (int(input())):
    n,m = [int(i) for i in input().split()]
    a = []
    li,lj = -1,-1
    for i in range (n):
        a.append(list(input().strip()))
        if 'L' in a[-1]:
            li,lj = i,a[-1].index('L')
    q = deque([(li,lj)])
    parent = {}
    parent[(li,lj)] = -1
    vis = [[0]*m for i in range (n)]
    while q:
        # print(q)
        ci,cj = q.popleft()
        cnt = 0
        cur = []
        if isGood(ci+1,cj):
            cur.append((ci+1,cj))
            cnt+=1
        if isGood(ci-1,cj):
            cur.append((ci-1,cj))
            cnt+=1
        if isGood(ci,cj+1):
            cur.append((ci,cj+1))
            cnt+=1
        if isGood(ci,cj-1):
            cur.append((ci,cj-1))
            cnt+=1
        if cnt <= 1 and a[ci][cj]=='.':
            a[ci][cj]='+'
            vis[ci][cj]=1
            for i in cur:
                if (vis[i[0]][i[1]]==0):
                    q.append(i)
        if a[ci][cj]=='L':
            for i in cur:
                if (vis[i[0]][i[1]]==0):
                    q.append(i)
            
    for i in a:
        print(''.join(i))