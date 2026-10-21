import sys

def main():
    A, B = map(int, sys.stdin.readline().split())
    answer = str(A - B)

    if answer[0] == '1':
        answer = '2' + answer[1:]
    else:
        answer = '1' + answer[1:]

    print(answer)

if __name__ == "__main__":
    main()