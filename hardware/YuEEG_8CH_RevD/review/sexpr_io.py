import re
def loads(s):
    stack=[];out=None
    for t in re.findall(r'"(?:\\.|[^"\\])*"|[^\s()]+|[()]',s):
        if t=='(':stack.append([])
        elif t==')':
            n=stack.pop()
            if stack:stack[-1].append(n)
            else:out=n
        else:stack[-1].append(t)
    return out
def sub(n,k):return next((x for x in n if isinstance(x,list) and x[0]==k),None)
def dumps(n):return '('+'\n'.join(dumps(x) if isinstance(x,list) else str(x) for x in n)+')'
