def dijkstra(graph,src):
    if graph == None:
        return None
    length = len(graph)
    type_ = type(graph)
    nodes = graph.keys()
    print 'inicio',nodes

    visited = [src]
    path = {src:{src:[src]}}
    if src not in nodes:
        return None
    else:
        nodes.remove(src)
    print 'segundo',nodes
    cost_graph = {src:0}
    prev = next_ = src
    print prev, next_, src
    # nodes.remove(next_)
    while nodes:
        cost = float('inf')

        print visited

        for v in visited:
             for d in nodes:
                new_dist = graph[src][v] + graph[v][d]
                if new_dist < cost: 
                    cost = new_dist
                    next_ = d
                    prev = v
                    graph[src][d] = new_dist

        path[src][next_] = [i for i in path[src][prev]]
        path[src][next_].append(next_)
        cost_graph[next_] = cost
        visited.append(next_)
        nodes.remove(next_)

    return cost_graph, path

if __name__ == '__main__':
    
    topo = {1: {1: 0, 2: float('inf'), 3: 1.4333724975585938, 4: float('inf'), 5: float('inf'), 6: float('inf'), 7: 4.527091979980469, 8: float('inf'), 9: float('inf'), 10: float('inf'), 11: float('inf'), 12: float('inf'), 13: float('inf'), 14: float('inf'), 15: float('inf'), 16: 1.5665292739868164, 17: float('inf'), 18: float('inf'), 19: float('inf'), 20: float('inf'), 21: float('inf'), 22: float('inf'), 23: float('inf')},
            2: {1: float('inf'), 2: 0, 3: float('inf'), 4: 1.563429832458496, 5: float('inf'), 6: float('inf'), 7: 11.860489845275879, 8: float('inf'), 9: float('inf'), 10: float('inf'), 11: float('inf'), 12: 3.2606124877929688, 13: 5.863070487976074, 14: float('inf'), 15: float('inf'), 16: float('inf'), 17: float('inf'), 18: 20.92587947845459, 19: float('inf'), 20: float('inf'), 21: float('inf'), 22: float('inf'), 23: 3.605484962463379}, 
            3: {1: 1.4333724975585938, 2: float('inf'), 3: 0, 4: float('inf'), 5: float('inf'), 6: float('inf'), 7: float('inf'), 8: float('inf'), 9: float('inf'), 10: 2.487063407897949, 11: 20.771265029907227, 12: float('inf'), 13: float('inf'), 14: 18.436551094055176, 15: float('inf'), 16: float('inf'), 17: float('inf'), 18: float('inf'), 19: float('inf'), 20: float('inf'), 21: 10.647416114807129, 22: float('inf'), 23: float('inf')}, 
            4: {1: float('inf'), 2: 1.563429832458496, 3: float('inf'), 4: 0, 5: float('inf'), 6: float('inf'), 7: float('inf'), 8: float('inf'), 9: float('inf'), 10: float('inf'), 11: float('inf'), 12: float('inf'), 13: float('inf'), 14: float('inf'), 15: float('inf'), 16: 2.380967140197754, 17: float('inf'), 18: float('inf'), 19: float('inf'), 20: float('inf'), 21: float('inf'), 22: float('inf'), 23: float('inf')},
            5: {1: float('inf'), 2: float('inf'), 3: float('inf'), 4: float('inf'), 5: 0, 6: float('inf'), 7: float('inf'), 8: 1.6372203826904297, 9: float('inf'), 10: float('inf'), 11: float('inf'), 12: float('inf'), 13: float('inf'), 14: float('inf'), 15: float('inf'), 16: 4.123568534851074, 17: float('inf'), 18: float('inf'), 19: float('inf'), 20: float('inf'), 21: float('inf'), 22: float('inf'), 23: float('inf')}, 
            6: {1: float('inf'), 2: float('inf'), 3: float('inf'), 4: float('inf'), 5: float('inf'), 6: 0, 7: 22.983074188232422, 8: float('inf'), 9: float('inf'), 10: float('inf'), 11: float('inf'), 12: float('inf'), 13: float('inf'), 14: float('inf'), 15: float('inf'), 16: float('inf'), 17: float('inf'), 18: float('inf'), 19: 26.52585506439209, 20: float('inf'), 21: float('inf'), 22: float('inf'), 23: float('inf')}, 
            7: {1: 4.527091979980469, 2: 11.860489845275879, 3: float('inf'), 4: float('inf'), 5: float('inf'), 6: 22.983074188232422, 7: 0, 8: float('inf'), 9: float('inf'), 10: float('inf'), 11: float('inf'), 12: float('inf'), 13: float('inf'), 14: float('inf'), 15: float('inf'), 16: float('inf'), 17: 9.756088256835938, 18: float('inf'), 19: 20.20549774169922, 20: float('inf'), 21: 3.298044204711914, 22: float('inf'), 23: float('inf')}, 
            8: {1: float('inf'), 2: float('inf'), 3: float('inf'), 4: float('inf'), 5: 1.6372203826904297, 6: float('inf'), 7: float('inf'), 8: 0, 9: 2.446770668029785, 10: float('inf'), 11: float('inf'), 12: float('inf'), 13: float('inf'), 14: float('inf'), 15: float('inf'), 16: float('inf'), 17: float('inf'), 18: float('inf'), 19: float('inf'), 20: float('inf'), 21: float('inf'), 22: float('inf'), 23: float('inf')}, 
            9: {1: float('inf'), 2: float('inf'), 3: float('inf'), 4: float('inf'), 5: float('inf'), 6: float('inf'), 7: float('inf'), 8: 2.446770668029785, 9: 0, 10: float('inf'), 11: float('inf'), 12: float('inf'), 13: float('inf'), 14: float('inf'), 15: 3.885626792907715, 16: 1.587510108947754, 17: float('inf'), 18: float('inf'), 19: float('inf'), 20: float('inf'), 21: float('inf'), 22: float('inf'), 23: float('inf')}, 
            10: {1: float('inf'), 2: float('inf'), 3: 2.487063407897949, 4: float('inf'), 5: float('inf'), 6: float('inf'), 7: float('inf'), 8: float('inf'), 9: float('inf'), 10: 0, 11: 1.579880714416504, 12: 2.06756591796875, 13: float('inf'), 14: float('inf'), 15: float('inf'), 16: 2.0973682403564453, 17: 27.29642391204834, 18: float('inf'), 19: float('inf'), 20: float('inf'), 21: float('inf'), 22: float('inf'), 23: float('inf')}, 
            11: {1: float('inf'), 2: float('inf'), 3: 20.771265029907227, 4: float('inf'), 5: float('inf'), 6: float('inf'), 7: float('inf'), 8: float('inf'), 9: float('inf'), 10: 1.579880714416504, 11: 0, 12: float('inf'), 13: float('inf'), 14: float('inf'), 15: float('inf'), 16: float('inf'), 17: float('inf'), 18: float('inf'), 19: float('inf'), 20: float('inf'), 21: float('inf'), 22: float('inf'), 23: float('inf')}, 
            12: {1: float('inf'), 2: 3.2606124877929688, 3: float('inf'), 4: float('inf'), 5: float('inf'), 6: float('inf'), 7: float('inf'), 8: float('inf'), 9: float('inf'), 10: 2.06756591796875, 11: float('inf'), 12: 0, 13: float('inf'), 14: float('inf'), 15: float('inf'), 16: float('inf'), 17: float('inf'), 18: float('inf'), 19: float('inf'), 20: float('inf'), 21: float('inf'), 22: 1.7240047454833984, 23: float('inf')}, 
            13: {1: float('inf'), 2: 5.863070487976074, 3: float('inf'), 4: float('inf'), 5: float('inf'), 6: float('inf'), 7: float('inf'), 8: float('inf'), 9: float('inf'), 10: float('inf'), 11: float('inf'), 12: float('inf'), 13: 0, 14: 1.7621517181396484, 15: float('inf'), 16: float('inf'), 17: 18.70906352996826, 18: float('inf'), 19: 2.756953239440918, 20: float('inf'), 21: float('inf'), 22: float('inf'), 23: float('inf')}, 
            14: {1: float('inf'), 2: float('inf'), 3: 18.436551094055176, 4: float('inf'), 5: float('inf'), 6: float('inf'), 7: float('inf'), 8: float('inf'), 9: float('inf'), 10: float('inf'), 11: float('inf'), 12: float('inf'), 13: 1.7621517181396484, 14: 0, 15: float('inf'), 16: float('inf'), 17: float('inf'), 18: float('inf'), 19: float('inf'), 20: float('inf'), 21: float('inf'), 22: float('inf'), 23: float('inf')}, 
            15: {1: float('inf'), 2: float('inf'), 3: float('inf'), 4: float('inf'), 5: float('inf'), 6: float('inf'), 7: float('inf'), 8: float('inf'), 9: 3.885626792907715, 10: float('inf'), 11: float('inf'), 12: float('inf'), 13: float('inf'), 14: float('inf'), 15: 0, 16: float('inf'), 17: float('inf'), 18: float('inf'), 19: float('inf'), 20: 4.799127578735352, 21: float('inf'), 22: float('inf'), 23: float('inf')}, 
            16: {1: 1.5665292739868164, 2: float('inf'), 3: float('inf'), 4: 2.380967140197754, 5: 4.123568534851074, 6: float('inf'), 7: float('inf'), 8: float('inf'), 9: 1.587510108947754, 10: 2.0973682403564453, 11: float('inf'), 12: float('inf'), 13: float('inf'), 14: float('inf'), 15: float('inf'), 16: 0, 17: float('inf'), 18: float('inf'), 19: float('inf'), 20: float('inf'), 21: float('inf'), 22: float('inf'), 23: float('inf')}, 
            17: {1: float('inf'), 2: float('inf'), 3: float('inf'), 4: float('inf'), 5: float('inf'), 6: float('inf'), 7: 9.756088256835938, 8: float('inf'), 9: float('inf'), 10: 27.29642391204834, 11: float('inf'), 12: float('inf'), 13: 18.70906352996826, 14: float('inf'), 15: float('inf'), 16: float('inf'), 17: 0, 18: float('inf'), 19: float('inf'), 20: 2.272963523864746, 21: float('inf'), 22: float('inf'), 23: 2.0564794540405273}, 
            18: {1: float('inf'), 2: 20.92587947845459, 3: float('inf'), 4: float('inf'), 5: float('inf'), 6: float('inf'), 7: float('inf'), 8: float('inf'), 9: float('inf'), 10: float('inf'), 11: float('inf'), 12: float('inf'), 13: float('inf'), 14: float('inf'), 15: float('inf'), 16: float('inf'), 17: float('inf'), 18: 0, 19: float('inf'), 20: float('inf'), 21: 1.44195556640625, 22: float('inf'), 23: float('inf')}, 
            19: {1: float('inf'), 2: float('inf'), 3: float('inf'), 4: float('inf'), 5: float('inf'), 6: 26.52585506439209, 7: 20.20549774169922, 8: float('inf'), 9: float('inf'), 10: float('inf'), 11: float('inf'), 12: float('inf'), 13: 2.756953239440918, 14: float('inf'), 15: float('inf'), 16: float('inf'), 17: float('inf'), 18: float('inf'), 19: 0, 20: float('inf'), 21: float('inf'), 22: float('inf'), 23: float('inf')}, 
            20: {1: float('inf'), 2: float('inf'), 3: float('inf'), 4: float('inf'), 5: float('inf'), 6: float('inf'), 7: float('inf'), 8: float('inf'), 9: float('inf'), 10: float('inf'), 11: float('inf'), 12: float('inf'), 13: float('inf'), 14: float('inf'), 15: 4.799127578735352, 16: float('inf'), 17: 2.272963523864746, 18: float('inf'), 19: float('inf'), 20: 0, 21: float('inf'), 22: 3.540515899658203, 23: float('inf')}, 
            21: {1: float('inf'), 2: float('inf'), 3: 10.647416114807129, 4: float('inf'), 5: float('inf'), 6: float('inf'), 7: 3.298044204711914, 8: float('inf'), 9: float('inf'), 10: float('inf'), 11: float('inf'), 12: float('inf'), 13: float('inf'), 14: float('inf'), 15: float('inf'), 16: float('inf'), 17: float('inf'), 18: 1.44195556640625, 19: float('inf'), 20: float('inf'), 21: 0, 22: float('inf'), 23: float('inf')}, 
            22: {1: float('inf'), 2: float('inf'), 3: float('inf'), 4: float('inf'), 5: float('inf'), 6: float('inf'), 7: float('inf'), 8: float('inf'), 9: float('inf'), 10: float('inf'), 11: float('inf'), 12: 1.7240047454833984, 13: float('inf'), 14: float('inf'), 15: float('inf'), 16: float('inf'), 17: float('inf'), 18: float('inf'), 19: float('inf'), 20: 3.540515899658203, 21: float('inf'), 22: 0, 23: float('inf')}, 
            23: {1: float('inf'), 2: 3.605484962463379, 3: float('inf'), 4: float('inf'), 5: float('inf'), 6: float('inf'), 7: float('inf'), 8: float('inf'), 9: float('inf'), 10: float('inf'), 11: float('inf'), 12: float('inf'), 13: float('inf'), 14: float('inf'), 15: float('inf'), 16: float('inf'), 17: 2.0564794540405273, 18: float('inf'), 19: float('inf'), 20: float('inf'), 21: float('inf'), 22: float('inf'), 23: 0}}
    
    graph_dict = {  "s1":{"s1": 0, "s2": 1, "s3": 1, "s4": float('inf'), "s5": float('inf')},
                    "s2":{"s1": 1, "s2": 0, "s3": 1, "s4": float('inf'), "s5":1},
                    "s3":{"s1": 1, "s2": 1, "s3": 0, "s4": 1, "s5": float('inf')},
                    "s4":{"s1": float('inf'), "s2": float('inf'), "s3": 1, "s4": 0, "s5": 1},
                    "s5":{"s1": float('inf'), "s2": 1, "s3": float('inf'), "s4": 1, "s5": 0}
                }
    # delay = {1: {16: 1.5665292739868164, 3: 1.4333724975585938, 7: 4.527091979980469}, 2: {4: 1.563429832458496, 7: 11.860489845275879, 12: 3.2606124877929688, 13: 5.863070487976074, 18: 20.92587947845459, 23: 3.605484962463379}, 3: {1: 1.4333724975585938, 10: 2.487063407897949, 11: 20.771265029907227, 21: 10.647416114807129, 14: 18.436551094055176}, 4: {16: 2.380967140197754, 2: 1.563429832458496}, 5: {8: 1.6372203826904297, 16: 4.123568534851074}, 6: {19: 26.52585506439209, 7: 22.983074188232422}, 7: {1: 4.527091979980469, 2: 11.860489845275879, 6: 22.983074188232422, 17: 9.756088256835938, 19: 20.20549774169922, 21: 3.298044204711914}, 8: {9: 2.446770668029785, 5: 1.6372203826904297}, 9: {8: 2.446770668029785, 16: 1.587510108947754, 15: 3.885626792907715}, 10: {11: 1.579880714416504, 16: 2.0973682403564453, 3: 2.487063407897949, 12: 2.06756591796875, 17: 27.29642391204834}, 11: {10: 1.579880714416504, 3: 20.771265029907227}, 12: {2: 3.2606124877929688, 10: 2.06756591796875, 22: 1.7240047454833984}, 13: {17: 18.70906352996826, 2: 5.863070487976074, 19: 2.756953239440918, 14: 1.7621517181396484}, 14: {3: 18.436551094055176, 13: 1.7621517181396484}, 15: {9: 3.885626792907715, 20: 4.799127578735352}, 16: {1: 1.5665292739868164, 10: 2.0973682403564453, 4: 2.380967140197754, 5: 4.123568534851074, 9: 1.587510108947754}, 17: {10: 27.29642391204834, 23: 2.0564794540405273, 20: 2.272963523864746, 13: 18.70906352996826, 7: 9.756088256835938}, 18: {2: 20.92587947845459, 21: 1.44195556640625}, 19: {13: 2.756953239440918, 6: 26.52585506439209, 7: 20.20549774169922}, 20: {17: 2.272963523864746, 22: 3.540515899658203, 15: 4.799127578735352}, 21: {18: 1.44195556640625, 3: 10.647416114807129, 7: 3.298044204711914}, 22: {20: 3.540515899658203, 12: 1.7240047454833984}, 23: {17: 2.0564794540405273, 2: 3.605484962463379}} 
    # switches = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    # link_to_port = {(16, 4): (5, 3), (1, 3): (3, 6), (10, 11): (3, 2), (10, 17): (5, 5), (17, 7): (2, 3), (16, 9): (6, 4), (9, 8): (2, 3), (19, 13): (3, 2), (3, 11): (4, 3), (14, 13): (3, 3), (3, 21): (5, 2), (8, 9): (3, 2), (13, 17): (5, 3), (7, 21): (6, 3), (1, 16): (4, 3), (2, 12): (7, 4), (4, 2): (2, 3), (10, 3): (2, 2), (3, 14): (3, 2), (12, 2): (4, 7), (11, 10): (2, 3), (3, 1): (6, 3), (6, 7): (3, 5), (16, 10): (2, 4), (23, 17): (3, 6), (8, 5): (2, 2), (3, 10): (2, 2), (2, 18): (4, 2), (10, 12): (6, 3), (23, 2): (2, 5), (2, 23): (5, 2), (7, 19): (2, 2), (2, 13): (2, 4), (5, 8): (2, 2), (17, 23): (6, 3), (19, 7): (2, 2), (12, 10): (3, 6), (18, 2): (2, 4), (7, 6): (5, 3), (13, 2): (4, 2), (20, 22): (2, 2), (19, 6): (4, 2), (22, 20): (2, 2), (17, 10): (5, 5), (7, 17): (3, 2), (7, 1): (4, 2), (15, 9): (3, 3), (9, 16): (4, 6), (17, 20): (4, 4), (13, 19): (2, 3), (17, 13): (3, 5), (18, 21): (3, 4), (4, 16): (3, 5), (21, 18): (4, 3), (12, 22): (2, 3), (2, 7): (6, 7), (16, 5): (4, 3), (5, 16): (3, 4), (20, 17): (4, 4), (13, 14): (3, 3), (22, 12): (3, 2), (9, 15): (3, 3), (11, 3): (3, 4), (7, 2): (7, 6), (21, 3): (2, 5), (16, 1): (3, 4), (15, 20): (2, 3), (6, 19): (2, 4), (1, 7): (2, 4), (14, 3): (2, 3), (20, 15): (3, 2), (21, 7): (3, 6), (2, 4): (3, 2), (10, 16): (4, 2)}
    # for src in switches:
    #     for dst in switches:
    #         if (src, dst) not in link_to_port.keys():
    #             delay[src][dst] = float('inf')
    
    src = input()
    cost, path = dijkstra(graph_dict, src)
    print ('costs: {0} \npath: {1}'.format(cost, path))