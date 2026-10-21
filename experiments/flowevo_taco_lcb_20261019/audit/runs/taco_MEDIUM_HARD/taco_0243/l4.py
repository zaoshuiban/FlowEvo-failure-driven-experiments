import sys

def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    a = int(data[0])
    b = int(data[1])

    if a < b:
        print(-1)
        return

    # Candidate from a descending segment:
    # x = (a + b) / (2m), maximizing valid m minimizes x.
    m_b = (a + b) // (2 * b)
    best_num = a + b
    best_den = 2 * m_b

    # Candidate from an ascending segment:
    # x = (a - b) / (2m), if such a segment is possible.
    m_a = (a - b) // (2 * b)
    if m_a > 0:
        if (a - b) * m_b < (a + b) * m_a:
            best_num = a - b
            best_den = 2 * m_a

    ans = best_num / best_den
    print(f"{ans:.12f}")

if __name__ == "__main__":
    main()