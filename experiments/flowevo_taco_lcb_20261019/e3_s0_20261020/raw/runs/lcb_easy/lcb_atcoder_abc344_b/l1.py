import sys

def main():
    numbers = sys.stdin.read().split()
    numbers.reverse()
    sys.stdout.write("\n".join(numbers))
    if numbers:
        sys.stdout.write("\n")

if __name__ == "__main__":
    main()