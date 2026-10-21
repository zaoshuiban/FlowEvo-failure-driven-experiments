def pig_latin(word):
    if len(word) > 3:
        return word[1:] + word[0] + "ay"
    return word