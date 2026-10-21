import sys

MOD = 10**9 + 7

def main():
    n = int(sys.stdin.readline())
    
    fact = 1
    for i in range(2, n + 1):
        fact = fact * i % MOD
    
    ans = (fact - pow(2, n - 1, MOD)) % MOD
    print(ans)

if __name__ == "__main__":
    main()