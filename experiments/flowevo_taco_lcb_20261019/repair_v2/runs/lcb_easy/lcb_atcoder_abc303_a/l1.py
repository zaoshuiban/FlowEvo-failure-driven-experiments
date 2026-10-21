import sys

def similar(a: str, b: str) -> bool:
    if a == b:
        return True
    return (a == '1' and b == 'l') or (a == 'l' and b == '1') or \
           (a == '0' and b == 'o') or (a == 'o' and b == '0')

def main():
    input = sys.stdin.readline
    N = int(input())
    S = input().strip()
    T = input().strip()

    for s, t in zip(S, T):
        if not similar(s, t):
            print("No")
            return

    print("Yes")

if __name__ == "__main__":
    main()