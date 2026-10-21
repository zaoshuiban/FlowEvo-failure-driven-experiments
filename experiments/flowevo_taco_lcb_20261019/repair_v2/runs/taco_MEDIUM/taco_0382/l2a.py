import sys

def main():
    numbers = [4, 8, 15, 16, 23, 42]
    number_set = set(numbers)

    products = []
    for j in range(2, 6):
        print(f"? 1 {j}")
        sys.stdout.flush()
        products.append(int(sys.stdin.readline().strip()))

    answer = None

    for x in numbers:
        quotients = []
        used = {x}
        ok = True

        for p in products:
            if p % x != 0:
                ok = False
                break

            q = p // x
            if q not in number_set or q in used:
                ok = False
                break

            used.add(q)
            quotients.append(q)

        if ok and len(quotients) == 4:
            answer = [x] + quotients
            break

    used = set(answer)
    for x in numbers:
        if x not in used:
            answer.append(x)
            break

    print("! " + " ".join(map(str, answer)))
    sys.stdout.flush()


if __name__ == "__main__":
    main()