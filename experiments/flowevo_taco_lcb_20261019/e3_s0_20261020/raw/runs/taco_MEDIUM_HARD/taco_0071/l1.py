import sys

s = ''.join(sys.stdin.read().split())

lines = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6)
)

def win(ch):
    return any(s[a] == s[b] == s[c] == ch for a, b, c in lines)

x = s.count('X')
o = s.count('0')

wx = win('X')
wo = win('0')

if not (x == o or x == o + 1):
    print("illegal")
elif wx and wo:
    print("illegal")
elif wx:
    if x == o + 1:
        print("the first player won")
    else:
        print("illegal")
elif wo:
    if x == o:
        print("the second player won")
    else:
        print("illegal")
else:
    if x + o == 9:
        print("draw")
    elif x == o:
        print("first")
    else:
        print("second")