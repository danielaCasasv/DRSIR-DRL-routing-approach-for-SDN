import json
file_k_paths = '/home/controlador/ryu/ryu/app/SDNapps_proac/RoutingGeant/DRL/dRSIR/23nodos/k_paths.json'
# file_k_paths = '/home/controlador/ryu/ryu/app/SDNapps_proac/RoutingGeant/DRL/dRSIR/topos/topo_32_nodes_k_20_paths.json'

with open(file_k_paths,'r+') as json_file:
    k_paths_dict = json.load(json_file)

paths_weight = {}
for i in k_paths_dict.keys():
    paths_weight.setdefault(i,{})
    for j in k_paths_dict.keys():
        paths_weight.setdefault(j,{})
        if i != j:
            paths_weight[i][j] = k_paths_dict[i][j][0]

with open('paths_weight.json','w') as json_file:
    json.dump(paths_weight, json_file, indent=2) 
        