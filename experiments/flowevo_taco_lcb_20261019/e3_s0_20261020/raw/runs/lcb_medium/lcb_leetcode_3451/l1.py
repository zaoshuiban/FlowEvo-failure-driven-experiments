class Solution:
    def compressedString(self, word: str) -> str:
        comp = []
        i = 0
        n = len(word)

        while i < n:
            c = word[i]
            j = i

            while j < n and word[j] == c:
                j += 1

            count = j - i

            while count > 0:
                take = min(9, count)
                comp.append(str(take))
                comp.append(c)
                count -= take

            i = j

        return ''.join(comp)