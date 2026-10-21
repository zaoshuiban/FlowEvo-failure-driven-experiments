import sys
import itertools

def main():
    nums = [4, 8, 15, 16, 23, 42]

    def query(i, j):
        print(f"? {i} {j}", flush=True)
        return int(sys.stdin.readline())

    p1 = query(1, 2)
    p2 = query(2, 3)
    p3 = query(3, 4)
    p4 = query(4, 5)

    answer = None
    for perm in itertools.permutations(nums):
        if (perm[0] * perm[1] == p1 and
            perm[1] * perm[2] == p2 and
            perm[2] * perm[3] == p3 and
            perm[3] * perm[4] == p4):
            answer = perm
            break

    print("! " + " ".join(map(str, answer)), flush=True)

if __name__ == "__main__":
    main()