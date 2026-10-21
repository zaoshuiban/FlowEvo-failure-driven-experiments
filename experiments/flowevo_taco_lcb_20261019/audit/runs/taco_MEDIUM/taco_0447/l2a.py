import sys

def main():
    tokens = sys.stdin.buffer.read().split()
    if not tokens:
        return

    t = int(tokens[0])
    ans = []

    for i in range(1, t + 1):
        s = tokens[i]
        n = len(s)

        ok = (
            n >= 4
            and s[:2] == b"</"
            and s[-1] == ord(">")
        )

        if ok:
            body = s[2:-1]
            for ch in body:
                if not (
                    ord('a') <= ch <= ord('z')
                    or ord('0') <= ch <= ord('9')
                ):
                    ok = False
                    break

        ans.append("Success" if ok else "Error")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    main()