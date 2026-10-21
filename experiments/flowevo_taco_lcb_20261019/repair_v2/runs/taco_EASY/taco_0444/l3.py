import sys

def main():
    data = sys.stdin.read().split()
    if not data:
        return
    t = int(data[0])
    ans = []
    idx = 1

    for _ in range(t):
        x = int(data[idx])
        y = int(data[idx + 1])
        idx += 2

        if y % x != 0:
            ans.append("0 0")
            continue

        k = y // x

        if k == 1:
            ans.append("3 1")
            continue

        found = False
        # Try to express k as b^a with a >= 2, choosing the smallest a.
        for a in range(2, 11):          # 2^10 > 100 >= k
            for b in range(2, 101):     # k <= 100
                val = 1
                for _ in range(a):
                    val *= b
                    if val > k:
                        break
                if val == k:
                    ans.append(f"{a} {b}")
                    found = True
                    break
            if found:
                break

        if not found:
            ans.append(f"1 {k}")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    main()