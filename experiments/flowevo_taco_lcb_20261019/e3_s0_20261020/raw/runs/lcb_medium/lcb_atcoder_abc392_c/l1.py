import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    P = data[1:1 + n]
    Q = data[1 + n:1 + 2 * n]

    inv_bib = [0] * (n + 1)
    for person_idx, bib in enumerate(Q):
        inv_bib[bib] = person_idx

    ans = []
    for bib in range(1, n + 1):
        person_idx = inv_bib[bib]
        target_person_idx = P[person_idx] - 1
        ans.append(str(Q[target_person_idx]))

    sys.stdout.write(" ".join(ans))

if __name__ == "__main__":
    main()