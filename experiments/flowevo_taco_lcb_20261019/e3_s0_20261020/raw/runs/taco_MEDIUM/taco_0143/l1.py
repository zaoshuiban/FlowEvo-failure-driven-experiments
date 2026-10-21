import sys
import heapq


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0
    t = data[idx]
    idx += 1

    output = []

    for _ in range(t):
        n = data[idx]
        idx += 1
        a = data[idx:idx + n]
        idx += n

        freq = [0] * (n + 1)
        for x in a:
            freq[x] += 1

        zero_heap = [i for i in range(n + 1) if freq[i] == 0]
        heapq.heapify(zero_heap)

        current_mex = zero_heap[0]
        seen = [False] * (n + 1)

        ans = []
        left = 0

        while left < n:
            mex = current_mex

            if mex == 0:
                ans.append(0)
                x = a[left]
                freq[x] -= 1
                if freq[x] == 0:
                    heapq.heappush(zero_heap, x)
                left += 1
            else:
                distinct = 0
                right = left

                while right < n:
                    x = a[right]

                    if x < mex and not seen[x]:
                        seen[x] = True
                        distinct += 1

                    freq[x] -= 1
                    if freq[x] == 0:
                        heapq.heappush(zero_heap, x)

                    if distinct == mex:
                        break

                    right += 1

                ans.append(mex)
                current_mex = zero_heap[0]

                for value in range(mex):
                    seen[value] = False

                left = right + 1

        output.append(str(len(ans)) + " " + " ".join(map(str, ans)))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()