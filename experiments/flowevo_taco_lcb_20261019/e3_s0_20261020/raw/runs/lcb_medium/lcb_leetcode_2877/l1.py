from itertools import permutations

class Solution:
    def minimumString(self, a: str, b: str, c: str) -> str:
        def merges(cur: str, nxt: str):
            res = set()

            if nxt in cur:
                res.add(cur)
            if cur in nxt:
                res.add(nxt)

            # No overlap: append nxt after cur
            res.add(cur + nxt)

            # Try every suffix-prefix overlap
            for k in range(1, min(len(cur), len(nxt)) + 1):
                if cur.endswith(nxt[:k]):
                    res.add(cur + nxt[k:])

            return res

        # Remove duplicate strings
        raw = []
        for s in (a, b, c):
            if s not in raw:
                raw.append(s)

        # Remove strings contained in another string
        needed = []
        for i, s in enumerate(raw):
            if any(i != j and s in t for j, t in enumerate(raw)):
                continue
            needed.append(s)

        best = None

        for p in set(permutations(needed)):
            candidates = {p[0]}

            for nxt in p[1:]:
                new_candidates = set()
                for cur in candidates:
                    new_candidates.update(merges(cur, nxt))
                candidates = new_candidates

            for cand in candidates:
                if (
                    best is None
                    or len(cand) < len(best)
                    or (len(cand) == len(best) and cand < best)
                ):
                    best = cand

        return best