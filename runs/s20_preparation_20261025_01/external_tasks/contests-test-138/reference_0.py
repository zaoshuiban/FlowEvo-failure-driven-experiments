from itertools import accumulate

class Dsu:
    def __init__(self, n):
        self.f = list(range(n))

    def find(self, x):
        if self.f[x] != x:
            self.f[x] = self.find(self.f[x])
        return self.f[x]

    def union(self, i, j, cnt, psum, maxv):
        fi, fj = self.find(i), self.find(j)
        if fi != fj:
            if fi < fj:
                fi, fj = fj, fi
            self.f[fj] = fi
            l1, l2 = cnt[fi], cnt[fj]
            l3 = l1 + l2
            cnt[fi] = l3
            maxv += psum[fi + 1 - l1] - psum[fi + 1 - l3] - (psum[fj + 1] - psum[fj + 1 - l2])
        return maxv

def main():
    n, m, q = map(int, input().split())
    a = list(map(int, input().split()))
    b = list(map(int, input().split()))
    qs = list(map(int, input().split()))
    qss = list(zip(qs, list(range(q))))
    qss.sort()

    nums = a + b
    nums.sort()
    tot = len(nums)
    cnt = [0] * tot
    i = j = 0
    a.sort()
    while i < n:
        while a[i] != nums[j]:
            j += 1
        cnt[j] = 1
        i += 1
        j += 1

    edges = []
    for i in range(tot):
        if i + 1 < tot:
            edges.append([nums[i + 1] - nums[i], i, i + 1])
    edges.sort(reverse=True)
    dsu = Dsu(tot)
    psum = [0] + list(accumulate(nums))
    maxv = sum(a)
    ans = [0] * q
    for k, idx in qss:
        while edges and edges[-1][0] <= k:
            _, i, j = edges.pop()
            maxv = dsu.union(i, j, cnt, psum, maxv)
        ans[idx] = maxv
    print(*ans, sep=" ")
    return


if __name__ == "__main__":
    main()





