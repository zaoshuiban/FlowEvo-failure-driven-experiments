import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    idx = 1
    answers = []

    for _ in range(n):
        l = data[idx]
        r = data[idx + 1]
        idx += 2

        best_num = r
        best_pop = r.bit_count()

        # Try making each set bit of r equal to 0 and setting all lower bits to 1.
        for bit in range(r.bit_length()):
            if (r >> bit) & 1:
                candidate = ((r >> (bit + 1)) << (bit + 1)) | ((1 << bit) - 1)

                if candidate >= l:
                    pop = candidate.bit_count()
                    if pop > best_pop or (pop == best_pop and candidate < best_num):
                        best_pop = pop
                        best_num = candidate

        answers.append(str(best_num))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()