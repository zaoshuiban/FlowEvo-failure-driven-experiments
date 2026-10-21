import sys

def main():
    s = sys.stdin.readline().strip()
    mirror_letters = set("AHIMOTUVWXY")
    if s == s[::-1] and all(ch in mirror_letters for ch in s):
        print("YES")
    else:
        print("NO")

if __name__ == "__main__":
    main()