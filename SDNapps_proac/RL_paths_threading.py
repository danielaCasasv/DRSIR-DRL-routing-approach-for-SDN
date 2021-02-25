import sys
sys.path.insert(0,'/home/controlador/ryu/ryu/app/SDNapps_proac/RoutingGeant/DRL/dRSIR/23nodos')
# sys.path.insert(0,'/home/controlador/ryu/ryu/app/SDNapps_proac/RoutingGeant/DRL/dRSIR/32nodos')
# sys.path.insert(0,'/home/controlador/ryu/ryu/app/SDNapps_proac/RoutingGeant/DRL/dRSIR/48nodos')
# sys.path.insert(0,'/home/controlador/ryu/ryu/app/SDNapps_proac/RoutingGeant/DRL/dRSIR/64nodos')
import time
import bot
import json,ast
import csv
import os
import setting
import qlearning
import environment_test_23nodes
# import environment_test_32nodes
# import environment_test_48nodes
# import environment_test_64nodes
# import environment_test_100nodes

num_nodes = 23

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
        paths_base = json.load(json_file)
        paths_base = ast.literal_eval(json.dumps(paths_base))
        return paths_base

def get_paths_RL():
    file_RL = '/home/controlador/ryu/ryu/app/SDNapps_proac/rl_paths.json'
    with open(file_RL,'r') as json_file:
        paths_dict = json.load(json_file)
        paths_RL = ast.literal_eval(json.dumps(paths_dict))
        return paths_RL

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
    paths_RL = get_paths_RL()
    cont_RL = 0
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
                    add_stretch_RL, mul_stretch_RL = stretch(paths_RL, paths_base, src, dst)
                    if add_stretch_RL != 0:
                        cont_RL += 1
                    # print('Additive stretch RL: ', add_stretch_RL)
                    # print('Multi stretch RL: ', mul_stretch_RL)
                    file.writerow([src,dst,add_stretch_RL,mul_stretch_RL])
    total_time = time.time() - a
    return total_time

def get_all_paths(episode_rewards, episode_states_all, episode_duration_all, episodes):
    t = time.time()
    env = environment_test_23nodes.Environment()
    # env = environment_test_32nodes.Environment()
    # env = environment_test_48nodes.Environment()
    # env = environment_test_64nodes.Environment()
    state_space_size = env.obs_space_size
    action_space_size = env.act_space_size
    alpha = 0.98 
    discount = 0.1
    epsilon = 0.8
    agente = qlearning.QL_agent(alpha, discount, epsilon, state_space_size,action_space_size) #(alpha, gamma, epsilon, episodes, n_states, n_actions)
    for episode in range(episodes):
        ini_ep = time.time()
        ep = time.time()
        s = env.reset()
        episode_reward = 0
        episode_state_list = []
        steps = 0
        d = False
        while True:
            steps += 1    
            a = agente.take_action(s,True)
            s_, r, d, _ = env.step(a)
            episode_reward += r
            episode_state_list.append(s)
            agente.updateQ(r,s,a,s_,d)
            if d:
                end_ep = time.time()
                episode_rewards[episode].append(episode_reward)
                episode_states_all[episode].append(episode_state_list)
                episode_duration_all[episode].append(end_ep-ini_ep)
                break
            s = s_            
    rl_paths = agente.use_model(env)
    time_RL = time.time() - t
    return rl_paths, time_RL, episode_rewards, episode_states_all, episode_duration_all

def RL_thread(): #cambiar para que lo llame a rl
    print('Enter thread')
    cont = 0
    episodes = 800 #23nodos
    # episodes = 1100 #32nodos
    # episodes = 4500 #64nodos
    # episodes = 2500 #48nodos

    # ---------TRAINNING AND RECOVERING OF PATHS----------
    # For running after deciding 

    episode_rewards = [[] for _ in range(episodes)]
    episode_states_all = [[] for _ in range(episodes)]
    episode_duration_all = [[] for _ in range(episodes)]
    iteration_times = []
    
    while cont < 28:  #23nodos (250s)
    # while cont < 38:  #32nodos (330s)
    # while cont < 38:   #48nodos (470ss)
    # while cont < 44: #64nodos (620s)
    # while cont < 2: #test inicial
       
        a = time.time()

        cont = cont + 1
        rl_paths, time_RL, episode_rewards, episode_states_all, episode_duration_all = get_all_paths(episode_rewards, episode_states_all, episode_duration_all, episodes)
        
        # print('time_RL',time_RL)
        time_stretch = calc_all_stretch(cont)
        iteration_times.append(time_RL) # print('time_stretch' , time_stretch)
        sleep = setting.MONITOR_PERIOD - time_RL - time_stretch
        
        if sleep > 0:
            print("**"+str(cont)+"**time remaining rl and stretch",sleep)
            time.sleep(sleep)
        else:
            print("**"+str(cont)+"**time remaining rl and stretch",sleep)        
            time.sleep(0.2)
        
    file_info_eps = "/home/controlador/ryu/ryu/app/SDNapps_proac/episode_info.txt"
    list_of_lines = ["Episodes: "+str(episodes),"Iterations: "+str(cont),"Time iteration: "+str(iteration_times)+"\n",str(episode_rewards)+"\n",str(episode_states_all)+"\n", str(episode_duration_all)+"\n"]
    append_multiple_lines(file_info_eps, list_of_lines)
    # print("Episode rewards: ", episode_rewards)
# start_time = 5
# time.sleep(5)
RL_thread()
call_bot("RL-paths-thread ended")