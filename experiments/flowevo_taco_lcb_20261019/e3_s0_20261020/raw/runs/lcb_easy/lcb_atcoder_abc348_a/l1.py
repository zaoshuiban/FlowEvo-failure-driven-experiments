import sys

def main():
    n = int(sys.stdin.readline().strip())
    result = ''.join('x' if i % 3 == 0 else 'o' for i in range(1, n + 1))
    print(result)

if __name__ == "__main__":
    main()