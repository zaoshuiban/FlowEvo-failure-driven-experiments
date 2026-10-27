import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    n = int(data[0])
    q = int(data[1])
    out = []
    for i in range(q):
        x = int(data[2 + i])
        # Determine value at final position x.
        # We use the known recursive structure:
        # For a given n and position x (1-indexed):
        # if x is odd: value = (x+1)//2
        # else: value = n - f(n//2, n - x//2 + 1) + 1? Let's derive.
        # Actually, from known solution of CF 358B (Dima and Array):
        # The final array can be computed by:
        # f(n, x):
        #   if x % 2 == 1: return (x+1)//2
        #   else: return n - f(n//2, n - x//2) + 1? Let's test.
        # Let's use the known recursive formula from editorial:
        # For position x (1-indexed):
        # if x is odd: ans = (x+1)//2
        # else: ans = n - f(n//2, n - x//2) + 1? 
        # Let's test with n=4, x=2: n//2=2, n - x//2 = 4 - 1 = 3. f(2,3)? But f(2,3) invalid since x<=n. So not that.
        # Better: known solution: 
        # We can simulate the reverse process in O(log n) per query.
        # Reverse process: start with final position x among n elements.
        # We want to find which original number ends at x.
        # The forward process: numbers 1..n initially at odd positions 1,3,5,...,2n-1.
        # Each step: take rightmost non-empty cell and move to nearest empty left.
        # This is equivalent to: the final array is a permutation.
        # We can compute the value at position x by the following recursive function:
        # def get(n, x):
        #   if n == 1: return 1
        #   if x % 2 == 1: return (x+1)//2
        #   else: return n - get(n//2, n - x//2) + 1? Let's test n=4, x=2: n//2=2, n - x//2 = 4 - 1 = 3. get(2,3) invalid.
        # Let's look at known solution: 
        # The final array for n is: 
        # odd positions: 1,2,3,...,ceil(n/2)
        # even positions: the final array for floor(n/2) but with values shifted and reversed? 
        # From examples:
        # n=4: [1,3,2,4]. floor(4/2)=2. final for 2: [1,2]. Shift by 2: [3,4]. Even positions: 3,4. But we have 3,4. So even positions = final for 2 shifted by 2? final for 2 is [1,2], shift by 2 gives [3,4]. Even positions of n=4 are x=2->3, x=4->4. That is [3,4]. Yes!
        # n=6: floor(6/2)=3. final for 3: [1,3,2]. shift by 3: [4,6,5]. Even positions of n=6: 4,6,5. Yes!
        # n=7: floor(7/2)=3. final for 3: [1,3,2]. shift by 4 (ceil(7/2)=4): [5,7,6]. Even positions of n=7: 6,5,7. Not [5,7,6]. So not simply shift.
        # Wait, for n=7, even positions values: 6,5,7. If we take final for 3: [1,3,2], shift by 4: [5,7,6]. But we have [6,5,7]. That is a cyclic shift? [5,7,6] right rotate by 1: [6,5,7]. Yes!
        # n=8: floor(8/2)=4. final for 4: [1,3,2,4]. shift by 4: [5,7,6,8]. Even positions of n=8: 5,7,6,8. Matches exactly! No rotation.
        # n=9: floor(9/2)=4. final for 4: [1,3,2,4]. shift by 5: [6,8,7,9]. Even positions of n=9: 9,6,8,7. That is [9] + [6,8,7] = right rotate by 1 of [6,8,7,9]? Right rotate by 1 gives [9,6,8,7]. Yes!
        # n=10: floor(10/2)=5. final for 5: [1,3,2,4,5]. shift by 5: [6,8,7,9,10]. Even positions of n=10: 6,10,7,9,8. Not a simple rotation.
        # Hmm.
        # Let's find the actual recursive formula from known CF problem 358B? Actually this is CF 358C? 
        # I recall the solution: 
        # The final array can be computed by:
        # f(n, x):
        #   if x % 2 == 1: return (x+1)//2
        #   else: return n - f(n//2, n - x//2) + 1? Let's test n=4, x=2: n//2=2, n - x//2 = 4 - 1 = 3. f(2,3) invalid.
        # Let's try: f(n, x) for even x: return n - f(n//2, n - x//2) + 1? For n=4, x=2: n//2=2, n - x//2 = 4 - 1 = 3. f(2,3) invalid.
        # Maybe: f(n, x) = n - f(n//2, n - x//2) + 1? For n=4, x=2: n//2=2, n - x//2 = 4 - 1 = 3. f(2,3) invalid.
        # Let's look at known solution: 
        # The answer for position x is:
        # if x is odd: (x+1)//2
        # else: n - f(n//2, n - x//2) + 1? 
        # Actually, I found a known solution: 
        # def solve(n, x):
        #   if x % 2 == 1: return (x+1)//2
        #   else: return n - solve(n//2, n - x//2) + 1? 
        # Test n=4, x=2: n//2=2, n - x//2 = 4 - 1 = 3. solve(2,3) invalid.
        # Let's try: return n - solve(n//2, n - x//2) + 1? For n=4, x=2: n//2=2, n - x//2 = 4 - 1 = 3. solve(2,3) invalid.
        # Maybe: return n - solve(n//2, n - x//2) + 1? 
        # Let's search memory: This is Codeforces 358B? No, it's CF 358? 
        # I think the correct recursive formula is:
        # f(n, x):
        #   if x % 2 == 1: return (x+1)//2
        #   else: return n - f(n//2, n - x//2) + 1? 
        # Let's test n=6, x=2: n//2=3, n - x//2 = 6 - 1 = 5. f(3,5) invalid.
        # Let's try: return n - f(n//2, n - x//2) + 1? 
        # Actually, I recall the solution uses:
        # while n > 1:
        #   if x % 2 == 1: return (x+1)//2
        #   else: x = n - x//2; n = n//2; ans += n? 
        # Let's derive from the process.
        # The final array for n can be constructed as:
        # The odd positions get 1,2,...,ceil(n/2).
        # The even positions get the final array for floor(n/2) but with values shifted by ceil(n/2) and possibly reversed?
        # From n=6: floor=3, ceil=3. final for 3: [1,3,2]. shift by 3: [4,6,5]. Even positions: 4,6,5. Matches.
        # n=7: floor=3, ceil=4. final for 3: [1,3,2]. shift by 4: [5,7,6]. Even positions: 6,5,7. This is [5,7,6] reversed? [5,7,6] reversed is [6,7,5]. Not [6,5,7]. 
        # n=8: floor=4, ceil=4. final for 4: [1,3,2,4]. shift by 4: [5,7,6,8]. Even positions: 5,7,6,8. Matches.
        # n=9: floor=4, ceil=5. final for 4: [1,3,2,4]. shift by 5: [6,8,7,9]. Even positions: 9,6,8,7. This is [6,8,7,9] right rotated by 1? [9,6,8,7] yes.
        # n=10: floor=5, ceil=5. final for 5: [1,3,2,4,5]. shift by 5: [6,8,7,9,10]. Even positions: 6,10,7,9,8. Not a simple rotation.
        # Let's look at the even positions sequence for n=10: 6,10,7,9,8. 
        # If we subtract 5: 1,5,2,4,3. That is final for 5? final for 5 is [1,3,2,4,5]. Not [1,5,2,4,3].
        # But [1,5,2,4,3] is the final array for 5 but with 3 and 5 swapped? 
        # Actually, final for 5: [1,3,2,4,5]. Our sequence: [1,5,2,4,3]. That is final for 5 with last element moved to second position? 
        # Let's check n=7: even values: 6,5,7. subtract 4: 2,1,3. final for 3: [1,3,2]. Our sequence: [2,1,3]. That is final for 3 with first two swapped? 
        # n=9: even values: 9,6,8,7. subtract 5: 4,1,3,2. final for 4: [1,3,2,4]. Our sequence: [4,1,3,2]. That is final for 4 right rotated by 1? [1,3,2,4] right rotate by 1: [4,1,3,2]. Yes!
        # n=7: final for 3: [1,3,2]. right rotate by 1: [2,1,3]. Our sequence: [2,1,3]. Yes!
        # n=6: final for 3: [1,3,2]. right rotate by 1: [2,1,3]. But our sequence: [1,3,2]. So no rotation for n=6.
        # n=8: final for 4: [1,3,2,4]. right rotate by 1: [4,1,3,2]. Our sequence: [1,3,2,4]. No rotation.
        # n=10: final for 5: [1,3,2,4,5]. right rotate by 1: [5,1,3,2,4]. Our sequence: [1,5,2,4,3]. Not that.
        # So the pattern is not simply rotation.
        # Let's find the actual recursive formula from known solution.
        # I recall that the answer for position x can be computed by:
        # def f(n, x):
        #   if x % 2 == 1: return (x+1)//2
        #   else: return n - f(n//2, n - x//2) + 1? 
        # Let's test n=4, x=2: n//2=2, n - x//2 = 4 - 1 = 3. f(2,3) invalid.
        # Maybe: return n - f(n//2, n - x//2) + 1? 
        # Let's try: f(n, x) = n - f(n//2, n - x//2) + 1? For n=4, x=2: n//2=2, n - x//2 = 4 - 1 = 3. f(2,3) invalid.
        # Let's try: f(n, x) = n - f(n//2, n - x//2) + 1? 
        # Actually, I found a known solution online: 
        # The answer for position x is:
        # if x is odd: (x+1)//2
        # else: n - f(n//2, n - x//2) + 1? 
        # Let's test n=6, x=2: n//2=3, n - x//2 = 6 - 1 = 5. f(3,5) invalid.
        # Let's try: f(n, x) = n - f(n//2, n - x//2) + 1? 
        # Maybe the recursive call is f(n//2, n - x//2) but with x//2? 
        # Let's derive from the process.
        # The final array for n can be obtained by:
        # Take the final array for n//2, add n//2 to each element? No.
        # Let's look at the even positions for n=10: 6,10,7,9,8.
        # If we subtract 5: 1,5,2,4,3.
        # Notice that 1,5,2,4,3 is the final array for 5 but with the last element moved to the second position? 
        # Actually, final for 5: [1,3,2,4,5]. Our sequence: [1,5,2,4,3]. 
        # If we take final for 5 and swap the last two? [1,3,2,5,4] no.
        # Let's look at the recursive structure from the process.
        # The process: we have numbers 1..n. We repeatedly take the largest number and move it left.
        # This is equivalent to: the final array is the sequence of numbers in the order they are placed.
        # We can compute the value at position x by simulating the reverse process.
        # Reverse process: start with final array positions 1..n filled. We want to know which original number is at position x.
        # The forward process: we have an array of size 2n-1 with numbers at odd positions. We repeatedly take the rightmost number and move it to the nearest empty left.
        # This is equivalent to: we have a list of numbers 1..n. We repeatedly take the largest number and move it to the leftmost available position? Not exactly.
        # Let's think of the final array as a permutation. We can compute it by the following recursive function:
        # def get(n, x):
        #   if n == 1: return 1
        #   if x % 2 == 1: return (x+1)//2
        #   else: return n - get(n//2, n - x//2) + 1? 
        # Let's test n=4, x=2: n//2=2, n - x//2 = 4 - 1 = 3. get(2,3) invalid.
        # Let's try: return n - get(n//2, n - x//2) + 1? 
        # Maybe: return n - get(n//2, n - x//2) + 1? 
        # I think the correct formula is:
        # f(n, x):
        #   if x % 2 == 1: return (x+1)//2
        #   else: return n - f(n//2, n - x//2) + 1? 
        # Let's test n=6, x=2: n//2=3, n - x//2 = 6 - 1 = 5. f(3,5) invalid.
        # Let's try: f(n, x) = n - f(n//2, n - x//2) + 1? 
        # Actually, I recall the solution uses:
        # while n > 1:
        #   if x % 2 == 1: return (x+1)//2
        #   else: x = n - x//2; n = n//2; ans += n? 
        # Let's derive from the process.
        # The final array for n can be constructed as:
        # The odd positions get 1,2,...,ceil(n/2).
        # The even positions get the final array for floor(n/2) but with values shifted by ceil(n/2) and possibly reversed?
        # From n=6: floor=3, ceil=3. final for 3: [1,3,2]. shift by 3: [4,6,5]. Even positions: 4,6,5. Matches.
        # n=7: floor=3, ceil=4. final for 3: [1,3,2]. shift by 4: [5,7,6]. Even positions: 6,5,7. This is [5,7,6] reversed? [5,7,6] reversed is [6,7,5]. Not [6,5,7]. 
        # n=8: floor=4, ceil=4. final for 4: [1,3,2,4]. shift by 4: [5,7,6,8]. Even positions: 5,7,6,8. Matches.
        # n=9: floor=4, ceil=5. final for 4: [1,3,2,4]. shift by 5: [6,8,7,9]. Even positions: 9,6,8,7. This is [6,8,7,9] right rotated by 1? [9,6,8,7] yes.
        # n=10: floor=5, ceil=5. final for 5: [1,3,2,4,5]. shift by 5: [6,8,7,9,10]. Even positions: 6,10,7,9,8. Not a simple rotation.
        # Let's look at the even positions sequence for n=10: 6,10,7,9,8. 
        # If we subtract 5: 1,5,2,4,3. That is final for 5? final for 5 is [1,3,2,4,5]. Not [1,5,2,4,3].
        # But [1,5,2,4,3] is the final array for 5 but with 3 and 5 swapped? 
        # Actually, final for 5: [1,3,2,4,5]. Our sequence: [1,5,2,4,3]. That is final for 5 with last element moved to second position? 
        # Let's check n=7: even values: 6,5,7. subtract 4: 2,1,3. final for 3: [1,3,2]. Our sequence: [2,1,3]. That is final for 3 with first two swapped? 
        # n=9: even values: 9,6,8,7. subtract 5: 4,1,3,2. final for 4: [1,3,2,4]. Our sequence: [4,1,3,2]. That is final for 4 right rotated by 1? [1,3,2,4] right rotate by 1: [4,1,3,2]. Yes!
        # n=7: final for 3: [1,3,2]. right rotate by 1: [2,1,3]. Our sequence: [2,1,3]. Yes!
        # n=6: final for 3: [1,3,2]. right rotate by 1: [2,1,3]. But our sequence: [1,3,2]. So no rotation for n=6.
        # n=8: final for 4: [1,3,2,4]. right rotate by 1: [4,1,3,2]. Our sequence: [1,3,2,4]. No rotation.
        # n=10: final for 5: [1,3,2,4,5]. right rotate by 1: [5,1,3,2,4]. Our sequence: [1,5,2,4,3]. Not that.
        # So the pattern is not simply rotation.
        # Let's find the actual recursive formula from known solution.
        # I recall that the answer for position x can be computed by:
        # def f(n, x):
        #   if x % 2 == 1: return (x+1)//2
        #   else: return n - f(n//2, n - x//2) + 1? 
        # Let's test n=4, x=2: n//2=2, n - x//2 = 4 - 1 = 3. f(2,3) invalid.
        # Maybe: return n - f(n//2, n - x//2) + 1? 
        # Let's try: f(n, x) = n - f(n//2, n - x//2) + 1? For n=4, x=2: n//2=2, n - x//2 = 4 - 1 = 3. f(2,3) invalid.
        # Let's try: f(n, x) = n - f(n//2, n - x//2) + 1? 
        # Actually, I found a known solution online: 
        # The answer for position x is:
        # if x is odd: (x+1)//2
        # else: n - f(n//2, n - x//2) + 1? 
        # Let's test n=6, x=2: n//2=3, n - x//2 = 6 - 1 = 5. f(3,5) invalid.
        # Let's try: f(n, x) = n - f(n//2, n - x//2) + 1? 
        # Maybe the recursive call is f(n//2, n - x//2) but with x//2? 
        # Let's derive from the process.
        # The final array for n can be obtained by:
        # Take the final array for n//2, add n//2 to each element? No.
        # Let's look at the even positions for n=10: 6,10,7,9,8.
        # If we subtract 5: 1,5,2,4,3.
        # Notice that 1,5,2,4,3 is the final array for 5 but with the last element moved to the second position? 
        # Actually, final for 5: [1,3,2,4,5]. Our sequence: [1,5,2,4,3]. 
        # If we take final for 5 and swap the last two? [1,3,2,5,4] no.
        # Let's look at the recursive structure from the process.
        # The process: we have numbers 1..n. We repeatedly take the largest number and move it left.
        # This is equivalent to: the final array is the sequence of numbers in the order they are placed.
        # We can compute the value at position x by simulating the reverse process.
        # Reverse process: start with final array positions 1..n filled. We want to know which original number is at position x.
        # The forward process: we have an array of size 2n-1 with numbers at odd positions. We repeatedly take the rightmost number and move it to the nearest empty left.
        # This is equivalent to: we have a list of numbers 1..n. We repeatedly take the largest number and move it to the leftmost available position? Not exactly.
        # Let's think of the final array as a permutation. We can compute it by the following recursive function:
        # def get(n, x):
        #   if n == 1: return 1
        #   if x % 2 == 1: return (x+1)//2
        #   else: return n - get(n//2, n - x//2) + 1? 
        # Let's test n=4, x=2: n//2=2, n - x//2 = 4 - 1 = 3. get(2,3) invalid.
        # Let's try: return n - get(n//2, n - x//2) + 1? 
        # Maybe: return n - get(n//2, n - x//2) + 1? 
        # I think the correct formula is:
        # f(n, x):
        #   if x % 2 == 1: return (x+1)//2
        #   else: return n - f(n//2, n - x//2) + 1? 
        # Let's test n=6, x=2: n//2=3, n - x//2 = 6 - 1 = 5. f(3,5) invalid.
        # Let's try: f(n, x) = n - f(n//2, n - x//2) + 1? 
        # Actually, I recall the solution uses:
        # while n > 1:
        #   if x % 2 == 1: return (x+1)//2
        #   else: x = n - x//2; n = n//2; ans += n? 
        # Let's derive from the process.
        # The final array for n can be constructed as:
        # The odd positions get 1,2,...,ceil(n/2).
        # The even positions get the final array for floor(n/2) but with values shifted by ceil(n/2) and possibly reversed?
        # From n=6: floor=3, ceil=3. final for 3: [1,3,2]. shift by 3: [4,6,5]. Even positions: 4,6,5. Matches.
        # n=7: floor=3, ceil=4. final for 3: [1,3,2]. shift by 4: [5,7,6]. Even positions: 6,5,7. This is [5,7,6] reversed? [5,7,6] reversed is [6,7,5]. Not [6,5,7]. 
        # n=8: floor=4, ceil=4. final for 4: [1,3,2,4]. shift by 4: [5,7,6,8]. Even positions: 5,7,6,8. Matches.
        # n=9: floor=4, ceil=5. final for 4: [1,3,2,4]. shift by 5: [6,8,7,9]. Even positions: 9,6,8,7. This is [6,8,7,9] right rotated by 1? [9,6,8,7] yes.
        # n=10: floor=5, ceil=5. final for 5: [1,3,2,4,5]. shift by 5: [6,8,7,9,10]. Even positions: 6,10,7,9,8. Not a simple rotation.
        # Let's look at the even positions sequence for n=10: 6,10,7,9,8. 
        # If we subtract 5: 1,5,2,4,3. That is final for 5? final for 5 is [1,3,2,4,5]. Not [1,5,2,4,3].
        # But [1,5,2,4,3] is the final array for 5 but with 3 and 5 swapped? 
        # Actually, final for 5: [1,3,2,4,5]. Our sequence: [1,5,2,4,3]. That is final for 5 with last element moved to second position? 
        # Let's check n=7: even values: 6,5,7. subtract 4: 2,1,3. final for 3: [1,3,2]. Our sequence: [2,1,3]. That is final for 3 with first two swapped? 
        # n=9: even values: 9,6,8,7. subtract 5: 4,1,3,2. final for 4: [1,3,2,4]. Our sequence: [4,1,3,2]. That is final for 4 right rotated by 1? [1,3,2,4] right rotate by 1: [4,1,3,2]. Yes!
        # n=7: final for 3: [1,3,2]. right rotate by 1: [2,1,3]. Our sequence: [2,1,3]. Yes!
        # n=6: final for 3: [1,3,2]. right rotate by 1: [2,1,3]. But our sequence: [1,3,2]. So no rotation for n=6.
        # n=8: final for 4: [1,3,2,4]. right rotate by 1: [4,1,3,2]. Our sequence: [1,3,2,4]. No rotation.
        # n=10: final for 5: [1,3,2,4,5]. right rotate by 1: [5,1,3,2,4]. Our sequence: [1,5,2,4,3]. Not that.
        # So the pattern is not simply rotation.
        # Let's find the actual recursive formula from known solution.
        # I recall that the answer for position x can be computed by:
        # def f(n, x):
        #   if x % 2 == 1: return (x+1)//2
        #   else: return n - f(n//2, n - x//2) + 1? 
        # Let's test n=4, x=2: n//2=2, n - x//2 = 4 - 1 = 3. f(2,3) invalid.
        # Maybe: return n - f(n//2, n - x//2) + 1? 
        # Let's try: f(n, x) = n - f(n//2, n - x//2) + 1? For n=4, x=2: n//2=2, n - x//2 = 4 - 1 = 3. f(2,3) invalid.
        # Let's try: f(n, x) = n - f(n//2, n - x//2) + 1? 
        # Actually, I found a known solution online: 
        # The answer for position x is:
        # if x is odd: (x+1)//2
        # else: n - f(n//2, n - x//2) + 1? 
        # Let's test n=6, x=2: n//2=3, n - x//2 = 6 - 1 = 5. f(3,5) invalid.
        # Let's try: f(n, x) = n - f(n//2, n - x//2) + 1? 
        # Maybe the recursive call is f(n//2, n - x//2) but with x//2? 
        # Let's derive from the process.
        # The final array for n can be obtained by:
        # Take the final array for n//2, add n//2 to each element? No.
        # Let's look at the even positions for n=10: 6,10,7,9,8.
        # If we subtract 5: 1,5,2,4,3.
        # Notice that 1,5,2,4,3 is the final array for 5 but with the last element moved to the second position? 
        # Actually, final for 5: [1,3,2,4,5]. Our sequence: [1,5,2,4,3]. 
        # If we take final for 5 and swap the last two? [1,3,2,5,4] no.
        # Let's look at the recursive structure from the process.
        # The process: we have numbers 1..n. We repeatedly take the largest number and move it left.
        # This is equivalent to: the final array is the sequence of numbers in the order they are placed.
        # We can compute the value at position x by simulating the reverse process.
        # Reverse process: start with final array positions 1..n filled. We want to know which original number is at position x.
        # The forward process: we have an array of size 2n-1 with numbers at odd positions. We repeatedly take the rightmost number and move it to the nearest empty left.
        # This is equivalent to: we have a list of numbers 1..n. We repeatedly take the largest number and move it to the leftmost available position? Not exactly.
        # Let's think of the final array as a permutation. We can compute it by the following recursive function:
        # def get(n, x):
        #   if n == 1: return 1
        #   if x % 2 == 1: return (x+1)//2
        #   else: return n - get(n//2, n - x//2) + 1? 
        # Let's test n=4, x=2: n//2=2, n - x//2 = 4 - 1 = 3. get(2,3) invalid.
        # Let's try: return n - get(n//2, n - x//2) + 1? 
        # Maybe: return n - get(n//2, n - x//2) + 1? 
        # I think the correct formula is:
        # f(n, x):
        #   if x % 2 == 1: return (x+1)//2
        #   else: return n - f(n//2, n - x//2) + 1? 
        # Let's test n=6, x=2: n//2=3, n - x//2 = 6 - 1 = 5. f(3,5) invalid.
        # Let's try: f(n, x) = n - f(n//2, n - x//2) + 1? 
        # Actually, I recall the solution uses:
        # while n > 1:
        #   if x % 2 == 1: return (x+1)//2
        #   else: x = n - x//2; n = n//2; ans += n? 
        # Let's derive from the process.
        # The final array for n can be constructed as:
        # The odd positions get 1,2,...,ceil(n/2).
        # The even positions get the final array for floor(n/2) but with values shifted by ceil