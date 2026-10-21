import sys

def classify(word):
    endings = {
        "lios": ('a', 1),
        "liala": ('a', 2),
        "etr": ('n', 1),
        "etra": ('n', 2),
        "initis": ('v', 1),
        "inites": ('v', 2)
    }
    
    for ending, info in endings.items():
        if word.endswith(ending):
            return info
    return None


words = sys.stdin.read().split()

if not words:
    print("NO")
    sys.exit()

if len(words) == 1:
    print("YES" if classify(words[0]) is not None else "NO")
    sys.exit()

gender = None
seen_noun = False
valid = True

for word in words:
    info = classify(word)
    if info is None:
        valid = False
        break

    part, g = info

    if gender is None:
        gender = g
    elif gender != g:
        valid = False
        break

    if part == 'a':
        if seen_noun:
            valid = False
            break
    elif part == 'n':
        if seen_noun:
            valid = False
            break
        seen_noun = True
    else:  # verb
        if not seen_noun:
            valid = False
            break

if valid and not seen_noun:
    valid = False

print("YES" if valid else "NO")