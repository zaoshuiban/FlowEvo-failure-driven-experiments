import sys

def main():
    data = sys.stdin.read().split()
    R, G, B = map(int, data[:3])
    C = data[3]

    pens = {
        "Red": R,
        "Green": G,
        "Blue": B
    }

    answer = min(price for color, price in pens.items() if color != C)
    print(answer)

if __name__ == "__main__":
    main()