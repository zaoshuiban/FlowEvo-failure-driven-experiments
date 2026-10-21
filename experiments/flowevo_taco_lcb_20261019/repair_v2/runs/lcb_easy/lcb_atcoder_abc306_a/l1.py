import sys

def main():
    input = sys.stdin.readline
    n = int(input())
    s = input().strip()
    print(''.join(ch * 2 for ch in s))

if __name__ == "__main__":
    main()