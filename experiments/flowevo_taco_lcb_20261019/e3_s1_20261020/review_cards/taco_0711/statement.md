Today is Vasya's birthday. On this special occasion, he has organized a party for all of his friends. These friends are enumerated by integers from 1 to N. Each of Vasya's friends has a Knowledge Level. In addition, each of them knows an arbitrary number of other people at the party. This friendship is bidirectional and transitive in nature, i.e if person A knows person B and person B knows person C, then we consider that person A knows person C. All these people who know each other come together and form a single group of friends.  

Now, they decide to play a game. In this game, among all groups of friends, the one with the highest knowledge level within each group is elected to represent the group during the game. Let's call this person the leader of the group.  If there are multiple candidates to be the leader of a group, you can select any of them arbitrarily. The game is then played after selecting these leaders.

Now, Vasya wants to find the number of distinct ways the game can be played. He finds this task too hard and wants you to help him. As this number can be large, print it Modulo 10^9+7.   

Input Format:

The first line contains two integers N and M denoting the number of people Vasya has invited to the party and the number of relations between these people. The next line contains N space separated integers denoting the where the i^{th} integer denotes the knowledge level of person i. Each of the next M lines contains 2 space separated integers u and v denoting that person u knows person v and vice-versa.  

Output Format

Print the required answer on a single line. As the answer may be large, print it Modulo 10^9+7 

Constraints

 1 ≤ N ≤ 10^5 

 0 ≤ M ≤ 10^5 

 0 ≤ A[i] ≤ 10^9  

 1 ≤ u,v ≤ N   

 M ≤ (N*(N-1))/2     

Note:

There can be self loops, i.e edges from and to the same person and multple edges from one person to another. 

SAMPLE INPUT
5 4
1 2 3 4 5
1 2
2 3
3 4
4 5

SAMPLE OUTPUT
1

Explanation

Here, all the people at the party know each other. Among this group the person with the highest knowledge is person 5. Hence, there is only one way.