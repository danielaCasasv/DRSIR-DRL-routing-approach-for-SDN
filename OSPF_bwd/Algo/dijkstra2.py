def minimum_distance(distance, Q):
    min = float('Inf')
    node = None
    for v in Q:
        if distance[v] < min:
            min = distance[v]
            node = v
    return node

def get_path (src,dst,switches):
    #Dijkstra's algorithm
    print "get_path is called, src=",src," dst=",dst
    adjacency = {}
    for dp in switches:
        adjacency.setdefault(dp,{})
    link_to_port = {(16, 4): (5, 3), (1, 3): (3, 6), (10, 11): (3, 2), (10, 17): (5, 5), (17, 7): (2, 3), (16, 9): (6, 4), (9, 8): (2, 3), (19, 13): (3, 2), (3, 11): (4, 3), (14, 13): (3, 3), (3, 21): (5, 2), (8, 9): (3, 2), (13, 17): (5, 3), (7, 21): (6, 3), (1, 16): (4, 3), (2, 12): (7, 4), (4, 2): (2, 3), (10, 3): (2, 2), (3, 14): (3, 2), (12, 2): (4, 7), (11, 10): (2, 3), (3, 1): (6, 3), (6, 7): (3, 5), (16, 10): (2, 4), (23, 17): (3, 6), (8, 5): (2, 2), (3, 10): (2, 2), (2, 18): (4, 2), (10, 12): (6, 3), (23, 2): (2, 5), (2, 23): (5, 2), (7, 19): (2, 2), (2, 13): (2, 4), (5, 8): (2, 2), (17, 23): (6, 3), (19, 7): (2, 2), (12, 10): (3, 6), (18, 2): (2, 4), (7, 6): (5, 3), (13, 2): (4, 2), (20, 22): (2, 2), (19, 6): (4, 2), (22, 20): (2, 2), (17, 10): (5, 5), (7, 17): (3, 2), (7, 1): (4, 2), (15, 9): (3, 3), (9, 16): (4, 6), (17, 20): (4, 4), (13, 19): (2, 3), (17, 13): (3, 5), (18, 21): (3, 4), (4, 16): (3, 5), (21, 18): (4, 3), (12, 22): (2, 3), (2, 7): (6, 7), (16, 5): (4, 3), (5, 16): (3, 4), (20, 17): (4, 4), (13, 14): (3, 3), (22, 12): (3, 2), (9, 15): (3, 3), (11, 3): (3, 4), (7, 2): (7, 6), (21, 3): (2, 5), (16, 1): (3, 4), (15, 20): (2, 3), (6, 19): (2, 4), (1, 7): (2, 4), (14, 3): (2, 3), (20, 15): (3, 2), (21, 7): (3, 6), (2, 4): (3, 2), (10, 16): (4, 2)}
    for src in switches:
        for dst in switches:
            if (src, dst) in link_to_port.keys():
                    adjacency[src][dst] = link_to_port[(src,dst)]
            else:
                adjacency[src][dst] = None
                    
    # adjacency = {1: {1:None, 2: 1, 3: None, 4: None, 5: 2, 6: None, 7: None}, 2: {1: 3, 2: None, 3: 1, 4: 2, 5: None, 6: None, 7: None}, 3: {1: None, 2: 3, 3: None, 4: None, 5: None, 6: None, 7: None}, 4: {1: None, 2: 3, 3: None, 4: None, 5: None, 6: None, 7: None}, 5: {1: 3, 2: None, 3: None, 4: None, 5: None, 6: 1, 7: 2}, 6: {1: None, 2: None, 3: None, 4: None, 5: 3, 6: None, 7: None}, 7: {1: None, 2: None, 3: None, 4: None, 5: 3, 6: None, 7: None}}
    # adjacency = {1: {1:None, 2: 1, 3: None, 4: None, 5: 2, 6: None, 7: None}, 2: {1: 3, 2: None, 3: 1, 4: 2, 5: None, 6: None, 7: None}, 3: {1: None, 2: 3, 3: None, 4: None, 5: None, 6: None, 7: None}, 4: {1: None, 2: 3, 3: None, 4: None, 5: None, 6: None, 7: None}, 5: {1: 3, 2: None, 3: None, 4: None, 5: None, 6: 1, 7: 2}, 6: {1: None, 2: None, 3: None, 4: None, 5: 3, 6: None, 7: None}, 7: {1: None, 2: None, 3: None, 4: None, 5: 3, 6: None, 7: None}}
    
    distance = {}
    previous = {}
    for dpid in switches:
        distance[dpid] = float('Inf')
        previous[dpid] = None
    distance[src]= 0

    Q=set(switches)
    print "Q=", Q
    while len(Q) > 0:
        u = minimum_distance(distance, Q)
        Q.remove(u) 

        for p in switches:
            if adjacency[u][p] != None: #If p neighbor of u
                w = 1
                if distance[u] + w < distance[p]:
                    distance[p] = distance[u] + w
                    previous[p] = u
    r=[]
    p=dst
    r.append(p)
    q=previous[p]
    while q is not None:
        if q == src:
            r.append(q)
            break
        p=q
        r.append(p)
        q=previous[p]

    r.reverse()
    if src==dst:
        path=[src]
    else:
        path=r

    # Now add the ports
    # r = []
    # in_port = first_port
    # for s1,s2 in zip(path[:-1],path[1:]):
    #     out_port = adjacency[s1][s2]
    #     r.append((s1,in_port,out_port))
    #     in_port = adjacency[s2][s1]
    # r.append((dst,in_port,final_port))

    return path

switches = [1, 2, 3, 4, 5, 6, 7]
paths = {}
for i in switches:
    paths.setdefault(i,{})
    for j in switches:
        if i != j:
            print('i,j', i,j)
            p = get_path(i,j,switches)
            paths[i][j] = p
print paths
