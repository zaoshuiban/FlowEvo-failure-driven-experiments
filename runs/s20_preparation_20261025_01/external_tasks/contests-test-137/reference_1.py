# cook your dish here
import sys
#import random
from bisect import bisect_left as lb
from bisect import bisect_right as rb
from collections import deque
#sys.setrecursionlimit(10**8)
from queue import PriorityQueue as pq
from math import gcd
#import math
input_ = lambda: sys.stdin.readline().strip("\r\n")
ii = lambda : int(input_())
il = lambda : list(map(int, input_().split()))
ilf = lambda : list(map(float, input_().split()))
lii = lambda : list(map(int, list(ip())))
ip = lambda : input_()
fi = lambda : float(input_())
ap = lambda ab,bc,cd : ab[bc].append(cd)
li = lambda : list(input_())
pr = lambda x : print(x)
prinT = lambda x : print(x)
f = lambda : sys.stdout.flush()
inv =lambda x:pow(x,mod-2,mod)
dx = [0,0,1,-1]
dy = [1,-1,0,0]
mod = 10**9 + 7
mod1 = 998244353

for _ in range (1) :
    x,y = il()

    a = bin(x)[2:] + '1'
    b = bin(y)[2:]
    t = len(a)
    fl = 0

    if (x == y) :
        print("YES")
        continue
    

    a1 = a[:len(a)-1]

    #print(a,b)
    for mn in range (2) :
        t = len(a)
        #print(a)
        for i in range (len(b)) :
            if (i + t - 1 >= len(b)) :
                break
            temp = b[i:i+t]
            if (temp == a) :
                t1 = b[:i]
                t2 = b[i+t:]

                if (t1.count('0')) or (t2.count('0')) :
                    pass
                else :
                    fl = 1
                    break
        #a1 = a
        a = a[::-1]

        for i in range (len(b)) :
            if (i + t - 1 >= len(b)) :
                break
            temp = b[i:i+t]
            if (temp == a) :
                t1 = b[:i]
                t2 = b[i+t:]

                if (t1.count('0')) or (t2.count('0')) :
                    pass
                else :
                    fl = 1
                    break
        ind = -1

        for i in range (len(a1)-1,-1,-1) :
            if (a1[i] == '1') :
                ind = i
                break

        a = a1[:ind+1]
    
    if (fl) :
        print("YES")
    else :
        print("NO")
