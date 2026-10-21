import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)

        # asc_only: positions already correct for ascending, but not for descending
        # desc_only: positions already correct for descending, but not for ascending
        # neither: positions correct for neither direction
        asc_only = 0
        desc_only = 0
        neither = 0

        for i in range(1, n + 1):
            p = next(it)

            is_asc = (p == i)
            is_desc = (p == n - i + 1)

            if is_asc and is_desc:
                continue
            elif is_asc:
                asc_only += 1
            elif is_desc:
                desc_only += 1
            else:
                neither += 1

        if desc_only + neither <= asc_only:
            answers.append("First")
        elif asc_only + neither < desc_only:
            answers.append("Second")
        else:
            answers.append("Tie")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()