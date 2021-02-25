import itertools
import random
import time
import numpy as np
import json, ast
import agent
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


class Environment(object):
    def __init__(self):
        self.act_space = [i for i in range(20)] # 20 possible paths per pair of nodes
        self.topo_nodes = [i for i in range(1,33)]
        self.obs_space = [i for i in itertools.permutations(self.topo_nodes,2)] #9900
        self.act_space_size = len(self.act_space) #number of actions per state
        self.obs_pm_size = len(random.choice(self.obs_space)) #number of parameters per state NOT ENCODE
        self.obs_pm_size = 1 #number of parameters per state ENCODE
        self.obs_space_size = len(self.obs_space) #number of states
        self.s = random.randrange(len(self.obs_space)) 
        self.cont_steps = 0
        self.next_states = self.zigZag()
        self.P = {state: {action: [] for action in range(self.act_space_size)} for state in range(self.obs_space_size)}
        self.rewards_dic = self.path_metrics_to_reward()
        
        for src in range(1,len(self.topo_nodes)+1):
            for dst in range(1,len(self.topo_nodes)+1):
                if src != dst:
                    state = self.obs_space.index((src,dst)) #state represented as te index in the array of obs
                    
                    new_state, done = self.rand_next_state(state) # #next state for state
                    for action in range(self.act_space_size):
                        reward =  self.rewards_dic[str(src)][str(dst)][action]
                        self.P[state][action].append((new_state, reward, done))

        with open('rewards_dic.json','w') as json_file:
            json.dump(self.rewards_dic, json_file, indent=2)
            
    def zigZag(self): 
        # a=time.time()
        '''Given an array of DISTINCT elements, rearrange the elements 
        of array in zig-zag fashion in O(n) time. 
        return a < b > c < d > e < f
        Flag true if relation <, else ">" is expected.  
        The first expected relation is "<" '''
        states = [i for i in range(self.obs_space_size)]
        flag = True
        for i in range(self.obs_space_size-1): 
            # "<" relation expected 
            if flag is True: 
                # If we have a situation like A > B > C, 
                #   we get A > B < C  
                # by swapping B and C 
                if states[i] > states[i+1]: 
                    states[i], states[i+1] = states[i+1],states[i] 
                # ">" relation expected 
            else: 
                # If we have a situation like A < B < C, 
                #   we get A < C > B 
                # by swapping B and C     
                if states[i] < states[i+1]: 
                    states[i],states[i+1] = states[i+1],states[i] 
            flag = bool(1 - flag) 
        next_states = states
        return next_states

    def rand_next_state(self, state):
        done = False 

        #automatic all states random
        if self.next_states.index(state) == self.obs_space_size-1:
          next_state = self.next_states[0]
        else:
          next_state = self.next_states[self.next_states.index(state)+1]
        return next_state, done
  
    #------Reward------------
    def path_metrics_to_reward(self):
        
        # #Reads metrics paths file 
        # ini = time.time()
        file = '/home/controlador/ryu/ryu/app/SDNapps_proac/paths_metrics.json'
        num_actions = self.act_space_size
        rewards_dic = {}
        metrics = ['bwd_paths','delay_paths','loss_paths']


        with open(file,'r') as json_file:
            paths_metrics_dict = json.load(json_file)
            paths_metrics_dict = ast.literal_eval(json.dumps(paths_metrics_dict))
        # print('path metrics json:',paths_metrics_dict['3']['19'])
        # print()

        for i in paths_metrics_dict:
            rewards_dic.setdefault(i,{})
            for j in paths_metrics_dict[i]:
                rewards_dic.setdefault(j,{})
                for m in metrics:
                    if m == metrics[0]:
                        bwd_cost = [] #since agent will minimize reward function, we do 1/bwd for such function
                        for val in paths_metrics_dict[str(i)][str(j)][m][0]:
                            if val > 0.001: #ensure minimum bwd available
                                temp = 1/val
                                bwd_cost.append(round(temp, 15))
                            else:
                                bwd_cost.append(1/0.001)
                        paths_metrics_dict[str(i)][str(j)][m][0] = bwd_cost
                        # print('****',i,j,m,bwd_cost)
                        #print(paths_metrics_dict[str(i)][str(j)][m])
                        
                    met_list = paths_metrics_dict[str(i)][str(j)][m]
                    met_norm = [self.normalize(met_val, 0, 100, min(paths_metrics_dict[str(i)][str(j)][m][0]), max(paths_metrics_dict[str(i)][str(j)][m][0])) for met_val in paths_metrics_dict[str(i)][str(j)][m][0]]
                    paths_metrics_dict[str(i)][str(j)][m].append(met_norm)
 
        for i in paths_metrics_dict:
            for j in paths_metrics_dict[i]:
                rewards_actions = []              
                for act in range(num_actions):
                    rewards_actions.append(self.reward(i,j,paths_metrics_dict,act,metrics))
                    rewards_dic[i][j] = rewards_actions
        return rewards_dic

    def reward(self, src, dst, paths_metrics_dict, act, metrics):
        '''
        paths_metrics_dict ={src:{dst:{metric1:[[orig value list],[normalized value list]]},metric2...}}
        '''
        beta1=1
        beta2=1
        beta3=1
        cost_action=1
        reward = cost_action + beta1*paths_metrics_dict[str(src)][str(dst)][metrics[0]][1][act] + beta2*paths_metrics_dict[str(src)][str(dst)][metrics[1]][1][act] + beta3*paths_metrics_dict[str(src)][str(dst)][metrics[2]][1][act]
        return round(reward,15)

    def normalize(self, value, minD, maxD, min_val, max_val):
        if max_val == min_val:
            value_n = (maxD + minD) / 2 
        else:
            value_n = (maxD - minD) * (value - min_val) / (max_val - min_val) + minD
        return round(value_n,15)

    def reset(self):
        i = time.time()
        self.s = random.randrange(len(self.obs_space))
        # print('Reset time:', time.time()-i)
        return self.s

    def step(self, a):
        # e = time.time()
        self.cont_steps += 1
        s, r, d = self.P[int(self.s)][int(a)][0]
        self.s = s
        d = self.cont_steps == 30
        if d:
            self.cont_steps = 0
        return (self.s, r, d, '')

