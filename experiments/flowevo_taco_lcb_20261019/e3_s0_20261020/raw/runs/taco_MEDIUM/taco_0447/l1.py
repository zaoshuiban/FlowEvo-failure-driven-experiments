import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    ans = []

    for i in range(1, t + 1):
        s = data[i]
        valid = True

        if len(s) < 4:
            valid = False
        elif s[0] != ord('<') or s[1] != ord('/') or s[-1] != ord('>'):
            valid = False
        else:
            body = s[2:-1]
            if len(body) == 0:
                valid = False
            else:
                for c in body:
                    if not ((ord('a') <= c <= ord('z')) or (ord('0') <= c <= ord('9'))):
                        valid = False
                        break

        ans.append("Success" if valid else "Error")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()