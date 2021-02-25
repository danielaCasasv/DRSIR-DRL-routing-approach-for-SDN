import json, ast
import csv
import time

def get_paths_dijkstra():
    file_dijkstra = '/home/controlador/ryu/ryu/app/OSPF/Proac/paths_delay.json'
    with open(file_dijkstra,'r') as json_file:
        paths_dict = json.load(json_file)
        paths_dijkstra = ast.literal_eval(json.dumps(paths_dict))
        return paths_dijkstra

def get_paths_base():
    file_base = '/home/controlador/ryu/ryu/app/OSPF/Proac/paths_weight.json'
    with open(file_base,'r') as json_file:
        paths_dict = json.load(json_file)
        paths_base = ast.literal_eval(json.dumps(paths_dict))
        return paths_base

def stretch(paths, paths_base, src, dst):
    
    print (paths.get(str(src)).get(str(dst)),'----', paths_base.get(str(src)).get(str(dst)))
    add_stretch = len(paths.get(str(src)).get(str(dst))) - len(paths_base.get(str(src)).get(str(dst)))
    mul_stretch = len(paths.get(str(src)).get(str(dst))) / len(paths_base.get(str(src)).get(str(dst)))
    return add_stretch, mul_stretch

def calc_stretch():
    count = 1
    cont_dijkstra = 0
    paths_base = get_paths_base()
    paths_dijkstra = get_paths_dijkstra()
    total_paths = 0
    a = time.time()
    sw = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    print(sw)
    print('enter stretch call')
    with open('/home/controlador/ryu/ryu/app/OSPF/Proac/stretch/'+str(count)+'_stretch.csv','wb') as csvfile:
        header = ['src','dst','add_st','mul_st']
        file = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
        file.writerow(header)
        for src in sw:
            for dst in sw:
                print(src,dst)
                if src != dst:
                    total_paths += 1
                    print(total_paths)
                    add_stretch_dijkstra, mul_stretch_dijkstra = stretch(paths_dijkstra, paths_base, src, dst)
                    if add_stretch_dijkstra != 0:
                        cont_dijkstra += 1
                    print('Additive stretch djikstra: ', add_stretch_dijkstra)
                    print('Multi stretch djikstra: ', mul_stretch_dijkstra)
                    file.writerow([src,dst,add_stretch_dijkstra,mul_stretch_dijkstra])
    total_time = time.time() - a

calc_stretch()