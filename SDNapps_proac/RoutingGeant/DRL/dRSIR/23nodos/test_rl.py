import qlearning
# import environment
# import test_environment
import environment_test_23nodes
import time
if __name__ =="__main__":
#     agent = agent_q.Agent()
#     timestep_reward = agent.qlearning(agent.env,test = True)
#     print(timestep_reward)
    t = time.time()
    env = environment_test_23nodes.Environment()
    # env = environment.Environment()
    iterations = 33
    episodes = 2100
    steps_ = "30"
    actions = "20"
    # tipo = "acts"
    tipo = "state"
    # rand = "abue"
    # rand = "seq"
    rand = "manual"
    start = "aleatorio-init-q_R_alphas"
    # start = "manual"

    state_space_size = env.obs_space_size
    action_space_size = env.act_space_size
    # print('state_space', state_space_size,'action_space',action_space_size)
    #episode_rewards = [[] for _ in range(episodes)]
    #episode_states_all = [[] for _ in range(episodes)]
    # alphas = [0.9, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99]
    alphas = [0.9]#0.8, 0.85, 0.9, 0.95, 0.98]
    
    # alpha = 0.98 
    discount = 0.1
    epsilon = 0.8
    for alpha in alphas:
        episode_rewards = [[] for _ in range(episodes)]
        episode_states_all = [[] for _ in range(episodes)]
        episode_duration_all = [[] for _ in range(episodes)]
        for i in range(iterations):
            it = time.time()
            # print("***Iteration: {0}".format(i))
            agente = qlearning.QL_agent(alpha, discount, epsilon, state_space_size,action_space_size) #(alpha, gamma, epsilon, episodes, n_states, n_actions)
            # print(agente.Q)
            for episode in range(episodes):
                ini_ep = time.time()
                ep = time.time()
                s = env.reset()
                # print(s)
                episode_reward = 0
                episode_state_list = []
                steps = 0
                d = False
                # a = agente.take_action(s,True) #orig
                # while steps < max_steps:
                while True:
                    steps += 1    
                    a = agente.take_action(s,True) #exp all states
                    s_, r, d, _ = env.step(a)
                    episode_reward += r
                    episode_state_list.append(s)
                    # print('state {0} - ation {1}: reward {2}'.format(s,a,r))
                    # a_ = agente.take_action(s_,False) #orig
                    agente.updateQ(r,s,a,s_,d) #exp all steps
                    # agente.updateQ(r,s,a,s_,a_,d) #orig
                    if d:
                        end_ep = time.time()
                        episode_rewards[episode].append(episode_reward)
                        episode_states_all[episode].append(episode_state_list)
                        episode_duration_all[episode].append(end_ep-ini_ep)
                        # print('\t Time episode',time.time()-ep)
                        # print("Episode {0}: {1} \nseen {2}".format(episode,episode_reward,steps))
                        break
                    s = s_ #only this when exp all lines
                    # a = a_ #orig

            print('Time iteration', time.time()-it)  

        # print(str(len(env.topo_nodes))+"nodos/RL-paths_nodes_"+str(len(env.topo_nodes))+"_ns_"+tipo+"_rand_"+rand+"_stp_"+steps_+".txt")
        # print('\nEpisode rewards',episode_rewards)
        #seq
        path = "/home/controlador/ryu/ryu/app/SDNapps_proac/RoutingGeant/DRL/dRSIR/"+str(len(env.topo_nodes))+"nodos/rl/"
        name_env = "_ns_"+tipo+"_rand_"+rand+"_stp_"+steps_+"_actions_"+actions+"_start_"+start
        name_agent = "_alpha_"+str(alpha)+"_RL-paths_nodes_"+str(len(env.topo_nodes))
        name_train = "_eps_"+str(episodes)+"_iter_"+str(iterations)
        f = open(path+"rew-rl"+name_env+name_agent+name_train+".txt","w+")

        f.write("**Episode rewards:\n")
        f.write(str(episode_rewards)+"\n\n")
        f.write(str(len(episode_rewards))+"\n\n")
        f.write("**Episode states:\n")
        # f.write(str(episode_states_all)+"\n\n")
        f.write(str(len(episode_states_all[0][0]))+"\n\n")
        f.write("**Episode duration:\n")
        f.write(str(episode_duration_all)+"\n\n")
        f.write("**P environment:\n")
        f.write(str(env.P)+"\n\n")
        f.close()
        print('\nTotal time', time.time()- t)       
