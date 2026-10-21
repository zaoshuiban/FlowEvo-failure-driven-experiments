import sys
import math

def main():
    n = int(sys.stdin.readline().strip())
    answer = math.comb(n, 5) ** 2 * math.factorial(5)
    print(answer)

if __name__ == "__main__":
    main()