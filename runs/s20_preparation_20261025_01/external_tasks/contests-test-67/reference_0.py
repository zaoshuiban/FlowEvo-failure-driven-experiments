
n,target = map(float,input().split())
n = int(n)



def getprob(study):

    tot = n*(n-1)*(n-2)//6
    case1 = study*(study-1)*(study-2)//6
    case2 = study*(study-1)*(n-study)//2
    case3 = study*(n-study)*(n-study-1)//2

    return (case1+case2+case3*0.5)*1.0/tot



front = 0
rear = n


while front<rear:

    mid = (front+rear)//2
    p = getprob(mid)

#    print(mid,p)

    if p < target:   front = mid + 1
    else:  rear = mid 


print(front)
