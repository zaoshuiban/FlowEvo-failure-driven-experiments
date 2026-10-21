from collections import deque

def tree_by_levels(node):
    if node is None:
        return []
    
    result = []
    queue = deque([node])
    
    while queue:
        current = queue.popleft()
        result.append(current.value)
        
        if current.left is not None:
            queue.append(current.left)
        if current.right is not None:
            queue.append(current.right)
    
    return result