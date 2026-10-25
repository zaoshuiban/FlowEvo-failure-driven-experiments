import sys
sys.setrecursionlimit(100000)

def _r(): return sys.stdin.buffer.readline()
def rs(): return _r().decode('ascii').strip()
def rn(): return int(_r())
def rnt(): return map(int, _r().split())
def rnl(): return list(rnt())

# [(2, -1), (1, 1), (4, -1), (2, 2), (5, 0), (3, 3), (7, 0)]
# [(1, 1), (2, 2), (2, -1), (3, 3), (4, -1), (5, 0), (7, 0)]
# [1, 2, -1, 3, -1, 0, 0]

# [(4, -3), (2, 0), (3, 0), (1, 3)]
# [(1, 3), (2, 0), (3, 0), (4, -3)]
# [3, 0, 0, -3]

import bisect

def lis(a):
    dp = []
    for num in a:
        i = bisect.bisect_right(dp, num)
        if i == len(dp):
            dp.append(num)
        dp[i] = num
    return len(dp)

def solve(n, a):
    b = [(x, i+1-x) for i, x in enumerate(a) if i+1-x >= 0]
    b.sort(key=lambda x:(x[0], -x[1]))
    b = list(map(lambda x:x[1], b))
    return lis(b)

n = rn()
a = rnl()
print(solve(n, a))

# for _ in range(rn()):
#     n, x = rnt()
#     a = rnl()
#     print('YES' if solve(n, x, a) else 'NO')

# def solve(n, m, mat):
#     def _try(r, c, dr, dc):
#         sol = 0
#         for i in range(c+1, c+dc):
#             sol += 1 - int(mat[r][i])
#             sol += 1 - int(mat[r+dr][i])
#         for i in range(r+1, r+dr):
#             sol += 1 - int(mat[i][c])
#             sol += 1 - int(mat[i][c+dc])
#         for i in range(r+1, r+dr):
#             for j in range(c+1, c+dc):
#                 sol += int(mat[i][j])
#         return sol
#     sol = float('inf')
#     sols = [[0]*m for _ in range(n)]
#     for r in range(n-4):
#         for c in range(m-3):
#             dr = 4
#             while r+dr < n:
#                 dc = 3
#                 while c+dc < m:
#                     sols[r+dr][c+dc] = _try(r, c, dr, dc)
#                     sol = min(sol, _try(r, c, dr, dc))
#                     dc += 1
#                 dr += 1
#     for row in sols:
#         print(row)
#     return sol

# for _ in range(rn()):
#     n, m = rnt()
#     mat = []
#     for _ in range(n):
#         mat.append(rs())
#     print(solve(n, m, mat))