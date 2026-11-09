"""UV islands require a shared continuous edge, with native topology when known."""
def island_groups(triangles, vertex_ids=None):
    parents=list(range(len(triangles)));edges={}
    def root(i):
        while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
        return i
    for index,triangle in enumerate(triangles):
        keys=[(vertex_ids[index][corner] if vertex_ids is not None else None,tuple(uv)) for corner,uv in enumerate(triangle)]
        for a,b in ((0,1),(1,2),(2,0)):
            if keys[a]==keys[b]:continue
            edge=frozenset((keys[a],keys[b]))
            if edge in edges:parents[root(index)]=root(edges[edge])
            else:edges[edge]=index
    groups={}
    for index in range(len(triangles)):groups.setdefault(root(index),[]).append(index)
    return list(groups.values())
