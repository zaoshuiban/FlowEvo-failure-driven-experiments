You are given an array A consisting of N distinct positive integers.

Find the smallest positive integer d such that there exists no pair of integers (i, j) (1≤ i< j ≤ N) where abs(A_{i} - A_{j}) is divisible by d. 

In other words, d \nmid abs(A_{i} - A_{j}) for all (1≤ i < j≤ N). 

------ Input Format ------ 

- The first line of input will contain a single integer T, denoting the number of test cases.
- Each test case consists of multiple lines of input.
- The first line of each test case contains an integers N — the number of the array A.
- The second line of each test case contains N space-separated distinct integers A_{1}, A_{2}, \ldots , A_{N} denoting the array A.

------ Output Format ------ 

For each test case, output the smallest positive integer d such that d \nmid (A_{i} - A_{j}) for all (1≤ i < j≤ N). 

------ Constraints ------ 

$1 ≤ T ≤ 1000$ 
$2 ≤ N ≤ 2 \cdot 10^{5}$
$1 ≤ A_{i} ≤ 2 \cdot 10^{5}$
- The sums of $N$ and $max(A)$ over all test cases does not exceed $3 \cdot 10 ^ 5$.

----- Sample Input 1 ------ 
3
3
1 2 3
3
1 2 10
3
1 3 10
----- Sample Output 1 ------ 
3
5
4
----- explanation 1 ------ 
Test case $1$: The possible differences are $abs(A_{1} - A_{2}) = 1, abs(A_{1} - A_{3}) = 2, abs(A_{2} - A_{3}) = 1$. The smallest positive integer not dividing any of these differences is $3$.

Test case $2$: The possible differences are $abs(A_{1} - A_{2}) = 1, abs(A_{1} - A_{3}) = 9, abs(A_{2} - A_{3}) = 8$. The smallest positive integer not dividing any of these differences is $5$.

Test case $3$: The possible differences are $abs(A_{1} - A_{2}) = 2, abs(A_{1} - A_{3}) = 9, abs(A_{2} - A_{3}) = 7$. The smallest positive integer not dividing any of these differences is $4$.