import sys

def main():
    data = sys.stdin.read().split()
    N = int(data[0])
    S = data[1]

    t_count = S.count('T')
    a_count = N - t_count

    if t_count > a_count:
        print('T')
    elif a_count > t_count:
        print('A')
    else:
        target = t_count
        t = 0
        a = 0

        for ch in S:
            if ch == 'T':
                t += 1
                if t == target:
                    print('T')
                    return
            else:
                a += 1
                if a == target:
                    print('A')
                    return

if __name__ == "__main__":
    main()