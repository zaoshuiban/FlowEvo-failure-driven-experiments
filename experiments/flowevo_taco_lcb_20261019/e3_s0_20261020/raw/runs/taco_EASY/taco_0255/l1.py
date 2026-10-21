import sys

def main():
    input = sys.stdin.readline
    n = int(input())
    
    depth = {"polycarp": 1}
    
    for _ in range(n):
        parts = input().split()
        name1 = parts[0].lower()
        name2 = parts[2].lower()
        depth[name1] = depth[name2] + 1
    
    print(max(depth.values()))

if __name__ == "__main__":
    main()