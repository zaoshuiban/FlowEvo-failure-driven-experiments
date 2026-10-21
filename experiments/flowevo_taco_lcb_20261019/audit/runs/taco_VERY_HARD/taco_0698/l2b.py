```python
import sys

MOD = 1000000007


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    k = int(data[1])
    s = data[2]

    # d[r]: no B^k has appeared yet, current suffix has r consecutive B's
    # e[r]: B^k has appeared, no W^k after it yet, current suffix has r consecutive W's
    d = [0] * k
    e = [0] * k

    d[0] = 1

    offD = 0
    lenD = 1
    totD = 1

    offE = 0
    lenE = 1
    totE = 0

    succ = 0

    mod = MOD
    kk = k
    km1 = k - 1

    for ch in s:
        if ch == 66:  # 'B'
            Sd = totD

            if lenD == kk:
                idx = offD + km1
                if idx >= kk:
                    idx -= kk
                tailD = d[idx]
            else:
                tailD = 0