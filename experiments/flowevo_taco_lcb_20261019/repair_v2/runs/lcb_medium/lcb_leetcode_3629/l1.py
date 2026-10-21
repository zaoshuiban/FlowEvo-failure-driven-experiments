class Solution:
    def lengthAfterTransformations(self, s: str, t: int) -> int:
        MOD = 10**9 + 7
        cnt = [0] * 26

        for ch in s:
            cnt[ord(ch) - ord('a')] += 1

        for _ in range(t):
            new_cnt = [0] * 26
            z = cnt[25]

            new_cnt[0] = z
            new_cnt[1] = (cnt[0] + z) % MOD

            for i in range(1, 25):
                new_cnt[i + 1] = cnt[i]

            cnt = new_cnt

        return sum(cnt) % MOD