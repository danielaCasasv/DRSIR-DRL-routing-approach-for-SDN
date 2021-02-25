import numpy as np
import json, ast

def init_q(s, a, type="zeros"):
    """
    @param s the number of states
    @param a the number of actions
    @param type random, ones or zeros for the initialization
    """
    if type == "ones":
        return np.ones((s, a))
    elif type == "random":
        return np.random.random((s, a))
    elif type == "zeros":
        return np.zeros((s, a))
    elif type == "inf":
        return np.inf*np.ones((s, a))

def epsilon_greedy(Q, epsilon, n_actions, s, train=False):
    """
    @param Q Q values state x action -> value
    @param epsilon for exploration
    @param s number of states
    @param train if true then no random actions selected
    """
    if train or np.random.rand() < epsilon: #rand() random flotante 0-1
        action = np.argmin(Q[s, :])
    else:
        action = np.random.randint(0, n_actions)
    return action


class QL_agent:
    def __init__(self, alpha, gamma, epsilon,n_states, n_actions):

        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.n_actions = n_actions
        self.n_states = n_states
        self.Q = init_q(n_states, n_actions, type="random")

    def take_action(self,s,first_state):
        if first_state:
            action = epsilon_greedy(self.Q,self.epsilon,self.n_actions,s,False)
        else:
            s_=s
            action = np.argmin(self.Q[s_, :])
        return action

    def updateQ(self,reward,s,a,s_,end_sate):
    # def updateQ(self,reward,s,a,s_,a_,end_sate):
        Q=self.Q
        alpha = self.alpha
        gamma = self.gamma
    
        if end_sate:
            # print("*** Terminal state")
            Q[s, a] += alpha * (reward - Q[s, a])

        else:
            # print("*** step")
            Q[s, a] += alpha * (reward + (gamma * np.argmin(self.Q[s_, :])) - Q[s, a])
            # Q[s, a] += alpha * (reward + (gamma * Q[s_, a_]) - Q[s, a])
    
    def use_model(self,env):
        
        #Recover paths corresponding to each action for states
        file = '/home/controlador/ryu/ryu/app/SDNapps_proac/RoutingGeant/DRL/dRSIR/'+str(len(env.topo_nodes))+'nodos/k_paths.json'
        # file = '/home/controlador/ryu/ryu/app/SDNapps_proac/k_paths_20.json'
        with open(file,'r') as json_file:
            k_paths = json.load(json_file)
            k_paths_dict = ast.literal_eval(json.dumps(k_paths))

        #Use trained model to find choosen actions
        rl_paths = {src: {dst: [] for dst in range(1,len(env.topo_nodes)+1) if src != dst} for src in range(1,len(env.topo_nodes)+1)}
        for src in range(1,len(env.topo_nodes)+1):
                    for dst in range(1,len(env.topo_nodes)+1):
                        if src != dst:
                            state = env.obs_space.index((src,dst))                            
                            action = epsilon_greedy(self.Q, 0, self.n_actions, state, train=True)
                            # print(src, dst, state, action)
                            path = k_paths_dict[str(src)][str(dst)][int(action)]
                            rl_paths[src][dst].append(path)

        #write choosen paths
        with open('/home/controlador/ryu/ryu/app/SDNapps_proac/rl_paths.json','w') as json_file:
            json.dump(rl_paths, json_file, indent=2)
        # print('\t Time total: ',time.time()-t)
        return rl_paths 
