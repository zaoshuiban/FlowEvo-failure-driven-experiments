S = input().strip()

for i, ch in enumerate(S):
    if S.count(ch) == 1:
        print(i + 1)
        break