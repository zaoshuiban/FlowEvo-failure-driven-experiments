import sys

def solve():
    numbers = [4, 8, 15, 16, 23, 42]
    S = set(numbers)
    
    # Map each product of two distinct special numbers to the unordered pair.
    prod_to_pair = {}
    for i in range(6):
        for j in range(i + 1, 6):
            prod = numbers[i] * numbers[j]
            prod_to_pair[prod] = {numbers[i], numbers[j]}
    
    def ask(i, j):
        sys.stdout.write(f"? {i} {j}\n")
        sys.stdout.flush()
        return int(sys.stdin.buffer.readline())
    
    p12 = ask(1, 2)
    p23 = ask(2, 3)
    p34 = ask(3, 4)
    p45 = ask(4, 5)
    
    E1 = prod_to_pair[p12]  # {a1, a2}
    E2 = prod_to_pair[p23]  # {a2, a3}
    
    a2 = (E1 & E2).pop()
    a1 = (E1 - {a2}).pop()
    a3 = (E2 - {a2}).pop()
    
    E3 = prod_to_pair[p34]  # {a3, a4}
    a4 = (E3 - {a3}).pop()
    
    E4 = prod_to_pair[p45]  # {a4, a5}
    a5 = (E4 - {a4}).pop()
    
    used = {a1, a2, a3, a4, a5}
    a6 = (S - used).pop()
    
    ans = [a1, a2, a3, a4, a5, a6]
    sys.stdout.write("! " + " ".join(map(str, ans)) + "\n")
    sys.stdout.flush()

if __name__ == "__main__":
    solve()