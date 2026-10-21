Sansa has an array. She wants to find the value obtained by XOR-ing the contiguous subarrays, followed by XOR-ing the values thus obtained. Determine this value.  

Example 

$arr=[3,4,5]$   

Subarray	Operation	Result
3		None		3
4		None		4
5		None		5
3,4		3 XOR 4		7
4,5		4 XOR 5		1
3,4,5		3 XOR 4 XOR 5	2

Now we take the resultant values and XOR them together:

$3\oplus4\oplus5\oplus7\oplus1\oplus2=6$.  Return $\boldsymbol{6}$.   

Function Description  

Complete the sansaXor function in the editor below.  

sansaXor has the following parameter(s):  

int arr[n]:  an array of integers  

Returns   

int: the result of calculations  

Input Format

The first line contains an integer $\boldsymbol{\boldsymbol{t}}$, the number of the test cases.   

Each of the next $\boldsymbol{\boldsymbol{t}}$ pairs of lines is as follows: 

- The first line of each test case contains an integer $n$, the number of elements in $arr$. 

- The second line of each test case contains $n$ space-separated integers $arr[i]$.    

Constraints

$1\leq t\leq5$ 

$2\leq n\leq10^5$ 

$1\leq arr[i]\leq10^8$  

Sample Input 0
2
3
1 2 3
4
4 5 7 5

Sample Output 0
2
0

Explanation 0

Test case 0: 

$1\oplus2\oplus3\oplus(1\oplus2)\oplus(2\oplus3)\oplus(1\oplus2\oplus3)=2$ 

Test case 1: 

$4\oplus5\oplus7\oplus5\oplus(4\oplus5)\oplus(5\oplus7)\oplus(7\oplus5)\oplus(4\oplus5\oplus7)\oplus(5\oplus7\oplus5)\oplus(4\oplus5\oplus7\oplus5)=0$  

Sample Input 1
2
3
98 74 12
3
50 13 2

Sample Output 1
110
48

Explanation 1

Test Case 0:

$98\oplus74\oplus12\oplus(98\oplus74)\oplus(74\oplus12)\oplus(98\oplus74\oplus12)=110$  

Test Case 1:

$50\oplus13\oplus2\oplus(50\oplus13)\oplus(13\oplus2)\oplus(50\oplus13\oplus2)=48$