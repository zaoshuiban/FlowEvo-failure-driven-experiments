import sys

def beats(a, b):
    return (a == "rock" and b == "scissors") or \
           (a == "scissors" and b == "paper") or \
           (a == "paper" and b == "rock")

def main():
    gestures = [line.strip() for line in sys.stdin.read().splitlines()[:3]]
    names = ["F", "M", "S"]

    for i in range(3):
        j = (i + 1) % 3
        k = (i + 2) % 3
        if beats(gestures[i], gestures[j]) and beats(gestures[i], gestures[k]):
            print(names[i])
            return

    print("?")

if __name__ == "__main__":
    main()