
"""
-If a graph is connected then edges >= n-1
-If a graph has more than (n-1)(n-2)/2 edges, then it is connected.
#G = nx.gnm_random_graph(n,(2*n)-1) # a graph is chosen uniformly at random from the set of all graphs with n nodes and m edges
barabasi_albert_graph returns a random graph according to the Barabasi-Albert preferential attachment model
A graph of n nodes is grown by attaching new nodes each with m edges that are preferentially attached to existing nodes with high degree. 1 <= m < n
"""
import json
import networkx as nx
import random
import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt
from itertools import islice


weight = (1,100) 


def ba_graph(name,n):
    print("***")
    # n = random.randint(10,15)    
    G = nx.barabasi_albert_graph(n,2) #n:Number of nodes m:Number of edges to attach from a new node to existing nodes

    for l in G.edges():
        G.edges[l]["weight"] = random.randint(weight[0],weight[1])
        G.edges[l]["sp"] = 1
    mapping=dict(zip(G.nodes(),range(1,n+1)))
    G1=nx.relabel_nodes(G,mapping) # nodes 1..26
    nx.draw(G1, with_labels=True, font_weight='bold')    
    plt.savefig("graph_"+name+".png") # save as png    
    plt.close()
    print(G1.nodes())
    print(G1.nodes().data())     
    G1_nl_format = nx.node_link_data(G1) 
    G1_ad_format = nx.adjacency_data(G1) # returns the graph in a node-link format
     
    print("G1_nl_format:",G1_nl_format)
    print("G1_adj_format:",G1_ad_format)
    with open('topo_'+name+'.json', 'w') as json_file:
        json.dump(G1_ad_format, json_file)    
    return G1

def k_shortest_paths(graph, src, dst, k, weight='sp'):
    return list(islice(nx.shortest_simple_paths(graph, src, dst, weight=weight), k))

def all_k_shortest_paths(graph, number_nodes, weight='sp', k=20):
    """
        Get all K shortest paths between datapaths.
        paths = {dp1:{dp2:[[path1], [path2],...,[pathk]]},}
    """
    _graph = graph.copy()
    paths = {}
    # Find k shortest paths in graph.
    for src in _graph.nodes():
        paths.setdefault(src, {})
        for dst in _graph.nodes():
            if src != dst:
                paths[src].setdefault(dst, [])
                paths[src][dst] = k_shortest_paths(_graph, src, dst, weight=weight, k=k)
    with open('topo_'+str(number_nodes)+'_nodes_k_'+str(k)+'_paths.json','w') as json_file:
        json.dump(paths, json_file, indent=2) 
    return paths    
number_nodes = 48
graph = ba_graph(str(number_nodes),number_nodes)
all_k_shortest_paths(graph,number_nodes)