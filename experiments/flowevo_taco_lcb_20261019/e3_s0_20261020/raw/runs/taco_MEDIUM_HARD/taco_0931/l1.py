def bowling_score(frames):
    rolls = []

    for ch in frames:
        if ch == ' ':
            continue
        elif ch == 'X':
            rolls.append(10)
        elif ch == '/':
            rolls.append(10 - rolls[-1])
        elif ch == '-':
            rolls.append(0)
        else:
            rolls.append(int(ch))

    score = 0
    i = 0

    for _ in range(10):
        if rolls[i] == 10:
            score += 10 + rolls[i + 1] + rolls[i + 2]
            i += 1
        elif rolls[i] + rolls[i + 1] == 10:
            score += 10 + rolls[i + 2]
            i += 2
        else:
            score += rolls[i] + rolls[i + 1]
            i += 2

    return score