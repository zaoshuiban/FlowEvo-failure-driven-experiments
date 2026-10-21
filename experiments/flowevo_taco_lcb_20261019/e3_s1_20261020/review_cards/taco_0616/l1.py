def animals(heads, legs):
    if heads < 0 or legs < 0:
        return "No solutions"
    
    if heads == 0 and legs == 0:
        return (0, 0)
    
    if (legs - 2 * heads) % 2 != 0:
        return "No solutions"
    
    cows = (legs - 2 * heads) // 2
    chickens = heads - cows
    
    if chickens < 0 or cows < 0:
        return "No solutions"
    
    return (chickens, cows)