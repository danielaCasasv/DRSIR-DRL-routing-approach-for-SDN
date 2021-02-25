import time
import json

def dijkstra(graph, src, dest, visited=[], distances={}, predecessors={}):
    """ calculates a shortest path tree routed in src
    """

    # a few sanity checks
    if src not in graph:
        raise TypeError('The root of the shortest path tree cannot be found')
    if dest not in graph:
        raise TypeError('The target of the shortest path cannot be found')
    # ending condition
    if src == dest:
        # We build the shortest path and display it
        path = []
        pred = dest
        while pred != None:
            path.append(pred)
            pred = predecessors.get(pred, None)
        
        return list(reversed(path))
    else:
        # if it is the initial  run, initializes the cost
        if not visited:
            distances[src] = 0
        # visit the neighbors
        for neighbor in graph[src]:
            if neighbor not in visited:
                new_distance = distances[src] + graph[src][neighbor]
                if new_distance < distances.get(neighbor, float('inf')):
                    distances[neighbor] = new_distance
                    predecessors[neighbor] = src
        # mark as visited

        visited.append(src)
        # now that all neighbors have been visited: recurse
        # select the non visited node with lowest distance 'x'
        # run Dijskstra with src='x'
        unvisited = {}
        for k in graph:
            if k not in visited:
                unvisited[k] = distances.get(k, float('inf')) #sets the cost of link to the src neighbors with the actual value and inf for the non neighbors
        x = min(unvisited, key=unvisited.get) #find w not in N' such that D(w) is a minimum
        return dijkstra(graph, x, dest, visited, distances, predecessors)


def get_dijkstra_paths():
    delay = {1: {16: 1.5665292739868164, 3: 1.4333724975585938, 7: 0.527091979980469},
             2: {4: 1.563429832458496, 7: 11.860489845275879, 12: 3.2606124877929688, 13: 5.863070487976074, 18: 20.92587947845459, 23: 0},
             3: {1: 11.4333724975585938, 10: 2.487063407897949, 11: 20.771265029907227, 21: 10.647416114807129, 14: 18.436551094055176},
             4: {16: 2.380967140197754, 2: 1.563429832458496},
             5: {8: 1.6372203826904297, 16: 4.123568534851074},
             6: {19: 26.52585506439209, 7: 22.983074188232422},
             7: {1: 0.527091979980469, 2: 11.860489845275879, 6: 22.983074188232422, 17: 9.756088256835938, 19: 20.20549774169922, 21: 3.298044204711914},
             8: {9: 2.446770668029785, 5: 1.6372203826904297},
             9: {8: 2.446770668029785, 16: 1.587510108947754, 15: 3.885626792907715},
             10: {11: 1.579880714416504, 16: 2.0973682403564453, 3: 2.487063407897949, 12: 2.06756591796875, 17: 27.29642391204834},
             11: {10: 1.579880714416504, 3: 20.771265029907227},
             12: {2: 3.2606124877929688, 10: 2.06756591796875, 22: 1.7240047454833984},
             13: {17: 18.70906352996826, 2: 5.863070487976074, 19: 2.756953239440918, 14: 1.7621517181396484},
             14: {3: 18.436551094055176, 13: 1.7621517181396484}, 15: {9: 3.885626792907715, 20: 4.799127578735352},
             16: {1: 1.5665292739868164, 10: 2.0973682403564453, 4: 2.380967140197754, 5: 4.123568534851074, 9: 1.587510108947754},
             17: {10: 27.29642391204834, 23: 2.0564794540405273, 20: 2.272963523864746, 13: 18.70906352996826, 7: 9.756088256835938}, 18: {2: 20.92587947845459, 21: 1.44195556640625},
             19: {13: 2.756953239440918, 6: 26.52585506439209, 7: 20.20549774169922},
             20: {17: 2.272963523864746, 22: 3.540515899658203, 15: 4.799127578735352},
             21: {18: 1.44195556640625, 3: 10.647416114807129, 7: 3.298044204711914},
             22: {20: 3.540515899658203, 12: 1.7240047454833984},
             23: {17: 2.0564794540405273, 2: 0}}
    
    switches = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    a = time.time()
    paths = {}
    for dp in switches:
        paths.setdefault(dp,{})
    for src in switches:
        for dst in switches:
            visited = []
            distances = {}
            predecessors = {}
            paths[src][dst] = dijkstra(delay, src, dst, visited, distances, predecessors)

    with open('paths_delay.json','w') as json_file:
        json.dump(paths, json_file, indent=2)
    end = time.time()-a
    print(end)
    print(dijkstra(delay,23,8))
get_dijkstra_paths()