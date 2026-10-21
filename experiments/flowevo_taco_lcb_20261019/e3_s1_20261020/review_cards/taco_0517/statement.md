We define a $hackonacci$ series as follows:

$hackonacci(n)=1\cdot hackonacci(n-1)+2\cdot hackon acesi(n-2)+3\cdot hackon aci(n-3)$   
$hackonacci(1)=1$  
$hackonacci(2)=2$  
$hackonacci(3)=3$  

We define a Hackonacci Matrix to be an $n\times n$ matrix where the rows and columns are indexed from ${1}$ to $n$, and the top-left cell is $(1,1)$. Each cell $(i,j)$ must contains either the character X or the character Y. If $hackonacci((i\cdot j)^2)$ is even, it's X; otherwise, it's Y.

Next, we want to perform ${q}$ queries where each query ${i}$ consists of an integer, ${angle}_i$. Each ${angle}_i$ is a multiple of ${90}$ degrees and describes the angle by which you must rotate the matrix in the clockwise direction. For each ${angle}_i$, we want to count the number of cells that are different after the rotation. For example, the diagram below depicts the $270^{\circ}$ rotation of a Hackonacci Matrix when $n=2$: 

As you can see, there are two cells whose values change after the rotation. Note that we filled each initial cell using the Hackonacci formula given above:

$(1,1)$: $hagonacci((1\cdot1)^2)=hakenacci(1)=1$ 

Because this is an odd number, we mark this cell with a Y.
$(1,2)$: $\begin{equation}\begin{aligned}hackonacci((1\cdot2)^2)&=hackonocci(4)\\ &\Rightarrow1\cdot hagonacci(3)+2\cdot hackonaccci(2)+3\cdot hackonacci(1)\\ &\Rightarrow1\cdot3+2\cdot2+3\cdot1=3+4+3=10\end{aligned}\end{equation}$ 

Because this is an even number, we mark this cell with an X.
$(2,1)$: $hakenacci((2\cdot1)^2)=hakenacci(4)\Rightarrow10$ 

Because this is an even number, we mark this cell with an X.
$(2,2)$: $hakenaci((2\cdot2)^2)=hakenacci(16)\Rightarrow296578$ 

Because this is an even number, we mark this cell with an X.

Given the value of $n$ and ${q}$ queries, construct a Hackonacci Matrix and answer the queries. For each query ${i}$, print an integer on a new line denoting the number of cells whose values differ from the initial Hackonacci Matrix when it's rotated by ${angle}_i$ degrees in the clockwise direction. 

Input Format

The first line contains two space-separated integers describing the respective values of $n$ and ${q}$. 

Each line ${i}$ of the ${q}$ subsequent lines contains an integer denoting ${angle}_i$.

Constraints

$1\leq n\leq2000$  
$1\leq q\leq10^4$  
$0\leq angle_i\leq10^5$  
It is guaranteed that each ${angle}_i$ is multiple of ${90}$ degrees.

Output Format

For each ${angle}_i$, print a single integer on a new line denoting the number of different cells that differ between the initial matrix and the matrix rotated by ${angle}_i$ degrees.

Sample Input 0
4 3
90
180
270

Sample Output 0
10
6
10

Explanation 0

Because $n=4$, we must build a $4\times4$ Hackonacci matrix and then perform $q=3$ queries, shown below. The following diagrams depict each query rotation, and cells whose values changed after performing a rotation are highlighted in orange:

When we perform a $90^{\circ}$ rotation on the matrix, there are $10$ cells whose  values change: 

Thus, we print $10$ on a new line.
When we perform a ${180^{\circ}}$ rotation on the matrix, there are ${6}$ cells whose  values change:
 
Thus, we print ${6}$ on a new line.
When we perform a $270^{\circ}$ rotation on the matrix, there are $10$ cells whose  values change:
 
Thus, we print $10$ on a new line.