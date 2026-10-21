Read problems statements in Mandarin chinese, Russian andVietnamese as well. 

Chef lives in the Universe in which only planets are present. Every planet is identified by 3 integers [p, q, r]. Chef lives on the planet [0, 0, 0] and wants to go to planet [X, Y, Z] with minimum energy loss.

The energy loss is determined by the following rules:

If Chef goes from [p, q, r] to [p+1, q, r] or [p, q+1, r] or [p, q, r+1], then A units of energy are lost.
If Chef goes from [p, q, r] to [p+1, q+1, r] or [p, q+1, r+1] or [p+1, q, r+1], then B units of energy are lost.
If Chef goes from [p, q, r] to [p+1, q+1, r+1], then C units of energy are lost.

Your task is to calculate the minimum energy loss possible when Chef goes from planet [0, 0, 0] to planet [X, Y, Z].

------ Input ------ 

The first line of the input contains a single integer T denoting the number of test cases. The description of T test cases follows.
The only line of each test case contains 6 space-separated integers denoting the values of X, Y, Z, A, B and C respectively.

------ Output ------ 

For each test case, output a single line containing one integer — the minimum energy loss.

------ Constraints ------ 

$1 ≤  T  ≤ 10^{5}$ 
$1 ≤ X, Y, Z ≤ 10^{5}$ 
$1 ≤ A, B, C ≤ 10^{3}$ 

------ Subtasks ------ 

Subtask #1 (20 points):

$1 ≤ T ≤ 50$ 
$1 ≤ X, Y, Z ≤ 100$ 

Subtask #2 (80 points): original constraints

----- Sample Input 1 ------ 
2
1 2 3 10 1 5
2 2 1 1 2 3
----- Sample Output 1 ------ 
3
5
----- explanation 1 ------ 
Example case 1: One of the possible solutions is [0, 0, 0] -->  [1, 0, 1]  -->  [1, 1, 2]  -->  [1, 2, 3]. The minimum energy loss is B + B + B = 3 · B = 3 · 1 = 3.
Example case 2: One of the possible solutions is [0, 0, 0] -->  [1, 1, 1]  -->  [2, 2, 1]. The minimum energy loss is C + B = 3 + 2 = 5.