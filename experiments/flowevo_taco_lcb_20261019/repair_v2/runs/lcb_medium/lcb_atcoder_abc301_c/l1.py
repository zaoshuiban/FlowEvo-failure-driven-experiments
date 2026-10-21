import sys
from collections import Counter

def main():
    S = sys.stdin.readline().strip()
    T = sys.stdin.readline().strip()

    cs = Counter(S)
    ct = Counter(T)

    allowed = set("atcoder")

    need_s = 0  # Number of @ needed in S
    need_t = 0  # Number of @ needed in T

    for ch in set(cs.keys()) | set(ct.keys()):
        if ch == '@':
            continue

        diff = cs[ch] - ct[ch]

        if diff == 0:
            continue

        if ch not in allowed:
            print("No")
            return

        if diff < 0:
            need_s += -diff
        else:
            need_t += diff

    if need_s <= cs['@'] and need_t <= ct['@']:
        print("Yes")
    else:
        print("No")

if __name__ == "__main__":
    main()