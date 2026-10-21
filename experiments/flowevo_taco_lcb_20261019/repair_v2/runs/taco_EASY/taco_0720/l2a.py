import sys

def main():
    input = sys.stdin.readline
    q = int(input())
    
    current_to_original = {}
    
    for _ in range(q):
        old, new = input().split()
        
        if old in current_to_original:
            original = current_to_original.pop(old)
        else:
            original = old
        
        current_to_original[new] = original
    
    print(len(current_to_original))
    for current, original in current_to_original.items():
        print(original, current)

if __name__ == "__main__":
    main()