from typing import List
from array import array


class Solution:
    def canMakePalindromeQueries(self, s: str, queries: List[List[int]]) -> List[bool]:
        n = len(s)
        m = n // 2

        A = s[:m]
        B = s[m:][::-1]

        def build_pref(t: str):
            seq = [ord(ch) - 97 for ch in t]
            pref = []

            for target in range(26):
                arr = array('I', [0])
                cnt = 0
                append = arr.append

                for v in seq:
                    if v == target:
                        cnt += 1
                    append(cnt)

                pref.append(arr)

            return pref

        prefA = build_pref(A)
        prefB = build_pref(B)

        prefMis = array('I', [0])
        mismatch = 0
        append_mis = prefMis.append

        for i in range(m):
            if A[i] != B[i]:
                mismatch += 1
            append_mis(mismatch)

        total_mismatch = mismatch
        answers = []

        for a, b, c0, d0 in queries:
            c = n - 1 - d0
            d = n - 1 - c0

            left = max(a, c)
            right = min(b, d)
            overlap = left <= right

            union_mismatch = (
                prefMis[b + 1] - prefMis[a] +
                prefMis[d + 1] - prefMis[c]
            )

            if overlap:
                union_mismatch -= prefMis[right + 1] - prefMis[left]

            if total_mismatch != union_mismatch:
                answers.append(False)
                continue

            valid = True

            for ch in range(26):
                pa = prefA[ch]
                pb = prefB[ch]

                countA_IA = pa[b + 1] - pa[a]
                countB_IB = pb[d + 1] - pb[c]

                countB_IA = pb[b + 1] - pb[a]
                countA_IB = pa[d + 1] - pa[c]

                if overlap:
                    countB_overlap = pb[right + 1] - pb[left]
                    countA_overlap = pa[right + 1] - pa[left]
                else:
                    countB_overlap = 0
                    countA_overlap = 0

                required_from_A = countB_IA - countB_overlap
                required_from_B = countA_IB - countA_overlap

                if countA_IA < required_from_A or countB_IB < required_from_B:
                    valid = False
                    break

                remaining_A = countA_IA - required_from_A
                remaining_B = countB_IB - required_from_B

                if remaining_A != remaining_B:
                    valid = False
                    break

            answers.append(valid)

        return answers