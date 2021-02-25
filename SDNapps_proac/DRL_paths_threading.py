
import sys
sys.path.insert(0,'/home/controlador/ryu/ryu/app/SDNapps_proac/RoutingGeant/DRL/dRSIR/23nodos')
# sys.path.insert(0,'/home/controlador/ryu/ryu/app/SDNapps_proac/RoutingGeant/DRL/dRSIR/32nodos')
# sys.path.insert(0,'/home/controlador/ryu/ryu/app/SDNapps_proac/RoutingGeant/DRL/dRSIR/64nodos')
# sys.path.insert(0,'/home/controlador/ryu/ryu/app/SDNapps_proac/RoutingGeant/DRL/dRSIR/48nodos')
import time
import bot
import json,ast
import csv
import os
import setting
import agent
import numpy as np
# import environment_test_23nodes
# import environment_test_32nodes
import environment_test_48nodes
# import environment_test_64nodes
# import environment_test_100nodes

num_nodes = 48

def call_bot(msg):
        bot.sendMessage(msg)
    
def append_multiple_lines(file_name, lines_to_append):
    # Open the file in append & read mode ('a+')
    with open(file_name, "a+") as file_object:
        appendEOL = False
        # Move read cursor to the start of file.
        file_object.seek(0)
        # Check if file is not empty
        data = file_object.read(100)
        if len(data) > 0:
            appendEOL = True
        # Iterate over each string in the list
        for line in lines_to_append:
            # If file is not empty then append '\n' before first line for
            # other lines always append '\n' before appending line
            if appendEOL == True:
                file_object.write("\n")
            else:
                appendEOL = True
            # Append element at the end of file
            file_object.write(line)

def get_paths_base():
    file_base = '/home/controlador/ryu/ryu/app/SDNapps_proac/RoutingGeant/DRL/dRSIR/'+str(num_nodes)+'nodos/paths_weight.json'
    with open(file_base,'r') as json_file:
        paths_dict = json.load(json_file)
        paths_base = ast.literal_eval(json.dumps(paths_dict))
        return paths_base

def get_paths_DRL():
    file_DRL = '/home/controlador/ryu/ryu/app/SDNapps_proac/drl_paths.json'
    with open(file_DRL,'r') as json_file:
        paths_dict = json.load(json_file)
        paths_DRL = ast.literal_eval(json.dumps(paths_dict))
        return paths_DRL

def stretch(paths, paths_base, src, dst):
   
    if isinstance(paths.get(str(src)).get(str(dst))[0],list):
        # print (paths.get(str(src)).get(str(dst))[0],'----', paths_base.get(str(src)).get(str(dst)))
        add_stretch = float(len(paths.get(str(src)).get(str(dst))[0])) - float(len(paths_base.get(str(src)).get(str(dst))))
        mul_stretch = float(len(paths.get(str(src)).get(str(dst))[0])) / float(len(paths_base.get(str(src)).get(str(dst))))
        return add_stretch, mul_stretch
    else:
        # print (paths.get(str(src)).get(str(dst)),'----', paths_base.get(str(src)).get(str(dst)))
        add_stretch = float(len(paths.get(str(src)).get(str(dst)))) - float(len(paths_base.get(str(src)).get(str(dst))))
        mul_stretch = float(len(paths.get(str(src)).get(str(dst)))) / float(len(paths_base.get(str(src)).get(str(dst))))
        return add_stretch, mul_stretch

def calc_all_stretch(cont):
    paths_base = get_paths_base()
    paths_DRL = get_paths_DRL()
    cont_DRL = 0
    total_paths = 0
    switches = [i for i in range(1,num_nodes+1)]
    a = time.time()
    with open('/home/controlador/ryu/ryu/app/SDNapps_proac/stretch/'+str(cont)+'_stretch.csv','w') as csvfile:
        header = ['src','dst','add_st','mul_st']
        file = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
        file.writerow(header)
        for src in switches:
            for dst in switches:
                if src != dst:
                    total_paths += 1
                    add_stretch_DRL, mul_stretch_DRL = stretch(paths_DRL, paths_base, src, dst)
                    if add_stretch_DRL != 0:
                        cont_DRL += 1
                    # print('Additive stretch RL: ', add_stretch_DRL)
                    # print('Multi stretch RL: ', mul_stretch_DRL)
                    file.writerow([src,dst,add_stretch_DRL,mul_stretch_DRL])
    total_time = time.time() - a
    return total_time

def get_all_paths(episode_rewards, episode_states_all, episode_duration_all, episodes):
    t = time.time()
    # env = environment_test_23nodes.Environment()
    # env = environment_test_32nodes.Environment()
    env = environment_test_48nodes.Environment()
    # env = environment_test_64nodes.Environment()
    state_space_size = env.obs_pm_size
    action_space_size = env.act_space_size

    target_update_freq=100 #1000, #cada n steps se actualiza la target network
    discount=0.1
    batch_size=15
    max_explore=1
    min_explore=0.05
    anneal_rate=(1/400) #1/100000),
    replay_memory_size = 100000#100000,
    replay_start_size= 400
    lr = 0.01

    agente = agent.Agent(state_space_size, action_space_size,target_update_freq, #1000, #cada n steps se actualiza la target network
                         discount, batch_size, max_explore, min_explore,
                         anneal_rate, replay_memory_size, replay_start_size,lr)
            
    for episode in range(episodes):
        ini_ep = time.time()
        ep = time.time()
        agente.handle_episode_start()
        s = [np.float32(env.reset())] #state inicial
        episode_reward = 0
        episode_state_list = []
        r = 0
        d = False
        while True:   
            a = agente.step(s,r)
            s_, r, d, _ = env.step(a)
            episode_reward += r
            episode_state_list.append(s)

            if d:
                end_ep = time.time()
                episode_rewards[episode].append(episode_reward)
                episode_states_all[episode].append(episode_state_list)
                episode_duration_all[episode].append(end_ep-ini_ep)
                break
            s = [np.float32(s_)]
    # print('\nEpisode rewards',episode_rewards)

    #Recover paths corresponding to each action for states
    file = '/home/controlador/ryu/ryu/app/SDNapps_proac/RoutingGeant/DRL/dRSIR/'+str(len(env.topo_nodes))+'nodos/k_paths.json'
    with open(file,'r') as json_file:
        k_paths = json.load(json_file)
        k_paths_dict = ast.literal_eval(json.dumps(k_paths))

    #Use trained model to find choosen actions
    drl_paths = {src: {dst: [] for dst in range(1,len(env.topo_nodes)+1) if src != dst} for src in range(1,len(env.topo_nodes)+1)}
    for src in range(1,len(env.topo_nodes)+1):
                for dst in range(1,len(env.topo_nodes)+1):
                    if src != dst:
                        state = [np.float32(env.obs_space.index((src,dst)))]
                        action = agente.step(state,0,False)
                        path = k_paths_dict[str(src)][str(dst)][int(action)]
                        drl_paths[src][dst].append(path)

    #write choosen paths
    with open('/home/controlador/ryu/ryu/app/SDNapps_proac/drl_paths.json','w') as json_file:
        json.dump(drl_paths, json_file, indent=2)
    # print('\t Time total: ',time.time()-t)
    # print("tup: {0} \ndisc: {1} \nbs: {2} \nminexp: {3} \nannr: {4} \nrms: {5} \nrss: {6} \nneu: {7}".format(agente.target_update_freq,agente.discount,agente.batch_size, agente.min_explore,agente.anneal_rate))#,agente.replay_memory_size,agente.replay_start_size))
    time_DRL = time.time() - t
    return drl_paths, time_DRL, episode_rewards, episode_states_all, episode_duration_all

def DRL_thread(): #cambiar para que lo llame a drl
    print('Enter thread')
    cont = 0
    # episodes = 40 #23nodos -- 32nodos
    episodes = 50 #48nodos
    # ---------TRAINNING AND RECOVERING OF PATHS----------
    # For running after deciding 

    episode_rewards = [[] for _ in range(episodes)]
    episode_states_all = [[] for _ in range(episodes)]
    episode_duration_all = [[] for _ in range(episodes)]
    iteration_times = []
    # while cont < 28: #23nodos (250s)
    # while cont < 40:  #32nodos (330s)
    while cont < 38:  #48nodos (470s)
    # while cont < 45: #64nodos (620s)
    

        a = time.time()
        cont = cont + 1
        drl_paths, time_DRL, episode_rewards, episode_states_all, episode_duration_all = get_all_paths(episode_rewards, episode_states_all, episode_duration_all, episodes)
        
        # print('time_DRL',time_DRL)
        time_stretch = calc_all_stretch(cont)
        iteration_times.append(time_DRL) # print('time_stretch' , time_stretch)
        sleep = setting.MONITOR_PERIOD - time_DRL - time_stretch
        
        if sleep > 0:
            print("**"+str(cont)+"**time remaining drl and stretch",sleep)
            time.sleep(sleep)
        else:
            print("**"+str(cont)+"**time remaining drl and stretch",sleep)        
            time.sleep(0.2)
        # print(time.time()-a)
    
    file_info_eps = "/home/controlador/ryu/ryu/app/SDNapps_proac/episode_info.txt"
    list_of_lines = ["Episodes: "+str(episodes),"Iterations: "+str(cont),"Time iteration: "+str(iteration_times)+"\n",str(episode_rewards)+"\n",str(episode_states_all)+"\n", str(episode_duration_all)+"\n"]
    append_multiple_lines(file_info_eps, list_of_lines)
    # print("Episode rewards: ", episode_rewards)
DRL_thread()
call_bot("DRL-paths-thread ended")