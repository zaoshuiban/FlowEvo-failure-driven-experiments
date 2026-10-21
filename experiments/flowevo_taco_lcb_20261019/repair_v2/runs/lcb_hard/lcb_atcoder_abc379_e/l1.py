import sys

def main():
    input = sys.stdin.readline
    N = int(input())
    S = input().strip()

    pref = []
    total = 0

    for i, ch in enumerate(S, start=1):
        total += (ord(ch) - ord('0')) * i
        pref.append(total)

    carry = 0
    digits = []

    for coeff in reversed(pref):
        value = coeff + carry
        digits.append(chr(ord('0') + value % 10))
        carry = value // 10

    while carry:
        digits.append(chr(ord('0') + carry % 10))
        carry //= 10

    digits.reverse()
    print(''.join(digits))

if __name__ == "__main__":
    main()