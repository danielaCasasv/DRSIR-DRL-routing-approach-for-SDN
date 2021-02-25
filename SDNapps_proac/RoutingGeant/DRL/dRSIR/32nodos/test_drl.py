import agent
import numpy as np
# import environment
# import test_environment
import environment_test_64nodes
import time
if __name__ =="__main__":
    t = time.time()
    lrs = [0.01]#, 0.001]#, 0.0001]#, 0.00001]
    env = environment_test_64nodes.Environment()
    # env = environment.Environment()
    
    #---Training parameters
    iterations = 33
    episodes = 300
    steps_ = "30"
    # tipo = "acts"
    tipo = "state"
    # rand = "abue"
    # rand = "seq"
    rand = "manual"
    start = "aleatorio-init-q_R_alphas"
    # start = "manual"

    #---AGENT parameters---
    state_space_size = env.obs_pm_size
    action_space_size = env.act_space_size

    target_update_freq=100 #5*steps, #cada n steps se actualiza la target network
    discount=0.1
    batch_size=15
    max_explore=1
    min_explore=0.005
    anneal_rate=(1/400) #1/100000),
    replay_memory_size = 100000#100000,
    replay_start_size= 400 #3*steps
    hl = "1"
    neu = "50"
    for lr in lrs:
        episode_rewards = [[] for _ in range(episodes)]
        episode_states_all = [[] for _ in range(episodes)]
        episode_duration_all = [[] for _ in range(episodes)]
        for i in range(iterations):
            it = time.time()
            print("***Iteration: {0}".format(i))
            # agente = qlearning.QL_agent(alpha, discount, epsilon, state_space_size,action_space_size,) #(alpha, gamma, epsilon, episodes, n_states, n_actions)
            agente = agent.Agent(state_space_size, action_space_size,target_update_freq, #1000, #cada n steps se actualiza la target network
                                 discount, batch_size, max_explore, min_explore,
                                 anneal_rate, replay_memory_size, replay_start_size,lr)
            if i == 0:
                print('tup:',agente.target_update_freq)
                print('disc, bs:',agente.discount, agente.batch_size)
                print('max exp, min exp: ',agente.max_explore, agente.min_explore)
                print('rss, rms: ',agente.replay_memory_size, agente.replay_start_size)
                print('annr:',agente.anneal_rate)
                print('lr:',agente.lr)
            for episode in range(episodes):
                # print("***Episode: {0}".format(i))
                ini_ep = time.time()
                agente.handle_episode_start()
                s = [np.float32(env.reset())] #state inicial
                episode_reward = 0
                episode_state_list = []
                steps = 0
                r = 0
                d = False
                while True:
                    steps += 1    
                    a = agente.step(s,r)
                    s_, r, d, _ = env.step(a)
                    episode_reward += r
                    episode_state_list.append(s)
                    
                    if d:
                        end_ep = time.time()
                        episode_rewards[episode].append(episode_reward)
                        episode_states_all[episode].append(episode_state_list)
                        episode_duration_all[episode].append(end_ep-ini_ep)
                        # print('\t Time episode',time.time()-ep)
                        # print("Episode {0}: {1} \nseen {2}".format(episode,episode_reward,steps))
                        break
                    s = [np.float32(s_)] 
            print('Time iteration', time.time()-it) 
            # print(str(len(env.topo_nodes))+"nodos/RL-paths_nodes_"+str(len(env.topo_nodes))+"_ns_"+tipo+"_rand_"+rand+"_stp_"+steps_+".txt")
            # print('\nEpisode rewards',episode_rewards)
            
        path = "/home/controlador/ryu/ryu/app/SDNapps_proac/RoutingGeant/DRL/dRSIR/"+str(len(env.topo_nodes))+"nodos/drl/"
        name_env = "_ns_"+tipo+"_rand_"+rand+"_stp_"+steps_+"_start_"+start
        name_agent = "_hl_"+hl+"_neu_"+neu+"_rss_"+str(replay_start_size)+"_annr_"+str(anneal_rate)+"_bs_"+str(batch_size)+"_tup_"+str(target_update_freq)+"_rms_"+str(replay_memory_size)
        name_train = "_eps_"+str(episodes)+"_iter_"+str(iterations)
        #manual
        f = open(path+"rew-drl_lr_"+str(lr)+name_env+name_agent+name_train+".txt","w+")
        
        f.write("**Episode rewards:\n")
        f.write(str(episode_rewards)+"\n\n")
        f.write(str(len(episode_rewards))+"\n\n")
        f.write("**Episode states:\n")
        f.write(str(episode_states_all)+"\n\n")
        f.write(str(len(episode_states_all[0][0]))+"\n\n")
        f.write("**Episode duration:\n")
        f.write(str(episode_duration_all)+"\n\n")
        f.write("**P environment:\n")
        f.write(str(env.P)+"\n\n")
        f.write("**Total episodes:"+str(episodes)+"\n")
        f.write("**Total iterations:"+str(iterations)+"\n")
        f.write("\nTotal time: "+str(time.time()- t))
        f.close()
        print('\nTotal time', time.time()- t)       
