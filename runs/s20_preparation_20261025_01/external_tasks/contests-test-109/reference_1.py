
MOD=998244353 
MAX=200005
fact=[1]
for zz in range(1,MAX+1):
    fact.append((fact[-1]*zz)%MOD) #with MOD
#    fact.append(fact[-1]*zz) #without MOD
def nCr(n,r): #choose, MOD is prime
    num=fact[n]
    den=(fact[r]*fact[n-r])%MOD
    return (num*pow(den,MOD-2,MOD))%MOD #with MOD, O(log(MOD))
#    den= fact[r]*fact[n-r]# without MOD
#    return num//den # without MOD

from collections import Counter

def main():
    
    MOD = 998244353 
    cnts = Counter()
    
    n = int(input())
    arr = []
    for _ in range(n):
        s = input()
        arr.append(s)
        cnts[s] += 1
    
    wCnt = bCnt = 0
    for k, v in cnts.items():
        for i in range(2):
            if k[i] == 'W': wCnt += v
            if k[i] == 'B': bCnt += v
    if wCnt > n or bCnt > n:
        print(0)
        return
    
    gap = n - wCnt + n - bCnt
    total = nCr(gap, n - wCnt)
    
    # subtract cases with no WW or BB, and has a mix of WB, BW
    if cnts['WW'] == cnts['BB'] == 0:
        subtract = 0
        minWBCnts = minBWCnts = 0
        for wb in ['W?', '?B', 'WB']: minWBCnts += cnts[wb]
        for bw in ['B?', '?W', 'BW']: minBWCnts += cnts[bw]
        gap = n - minWBCnts - minBWCnts
        qq = cnts['??']
        for wbCnts in range(1, n):
            bwCnts = n - wbCnts
            if wbCnts < minWBCnts or bwCnts < minBWCnts:
                continue
            assert qq >= wbCnts - minWBCnts
            subtract += nCr(qq, wbCnts - minWBCnts)
            subtract %= MOD
        total = (total - subtract + MOD) % MOD
    print(total)
    
    return


import sys
# input=sys.stdin.buffer.readline #FOR READING PURE INTEGER INPUTS (space separation ok)
input=lambda: sys.stdin.readline().rstrip("\r\n") #FOR READING STRING/TEXT INPUTS.

def oneLineArrayPrint(arr):
    print(' '.join([str(x) for x in arr]))
def multiLineArrayPrint(arr):
    print('\n'.join([str(x) for x in arr]))
def multiLineArrayOfArraysPrint(arr):
    print('\n'.join([' '.join([str(x) for x in y]) for y in arr]))
 
def readIntArr():
    return [int(x) for x in input().split()]
# def readFloatArr():
#     return [float(x) for x in input().split()]
 
def makeArr(defaultValFactory,dimensionArr): # eg. makeArr(lambda:0,[n,m])
    dv=defaultValFactory;da=dimensionArr
    if len(da)==1:return [dv() for _ in range(da[0])]
    else:return [makeArr(dv,da[1:]) for _ in range(da[0])]
 
def queryInteractive(i,j):
    print('? {} {}'.format(i,j))
    sys.stdout.flush()
    return int(input())
 
def answerInteractive(i,j,k):
    print('! {} {} {}'.format(i,j,k))
    sys.stdout.flush()
 
inf=float('inf')
# MOD=10**9+7
# MOD=998244353

from math import gcd,floor,ceil
import math
# from math import floor,ceil # for Python2
 
for _abc in range(1):
    main()