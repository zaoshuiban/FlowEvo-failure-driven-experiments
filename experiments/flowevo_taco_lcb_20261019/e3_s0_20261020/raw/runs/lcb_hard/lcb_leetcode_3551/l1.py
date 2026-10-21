from typing import List

class Solution:
    def maximumSubarrayXor(self, nums: List[int], queries: List[List[int]]) -> List[int]:
        n = len(nums)
        q = len(queries)

        queries_by_length = [[] for _ in range(n + 1)]
        for idx, (l, r) in enumerate(queries):
            length = r - l + 1
            queries_by_length[length].append((l, idx))

        answer = [0] * q

        # For intervals of length 1
        prev_score = nums[:]
        prev_max = nums[:]

        for l, idx in queries_by_length[1]:
            answer[idx] = prev_max[l]

        # Process interval lengths from 2 to n
        for length in range(2, n + 1):
            size = n - length + 1

            cur_score = [0] * size
            cur_max = [0] * size

            for l in range(size):
                score = prev_score[l] ^ prev_score[l + 1]
                cur_score[l] = score

                best = prev_max[l]
                if prev_max[l + 1] > best:
                    best = prev_max[l + 1]
                if score > best:
                    best = score

                cur_max[l] = best

            for l, idx in queries_by_length[length]:
                answer[idx] = cur_max[l]

            prev_score = cur_score
            prev_max = cur_max

        return answer