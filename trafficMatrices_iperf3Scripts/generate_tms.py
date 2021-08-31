from tmgen.models import modulated_gravity_tm
from tmgen import TrafficMatrix
from numpy import random
import numpy as np
import pickle
import time
import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt
'''
This file generates the pkl file with the TMs based on the modulated gravity model 
by using the TMGen python library. 
Please refer to https://github.com/progwriter/TMgen for installing the library.
'''

"""
    Generate a modulated gravity traffic matrix with the given parameters
    :-- num_nodes: number of Points-of-Presence (i.e., origin-destination pairs)
    :-- num_tms: total number of traffic matrices to generate (i.e., time epochs)
    :-- mean_traffic: the average total volume of traffic
    :-- pm_ratio: peak-to-mean ratio. Peak  traffic will be larger by
        this much (must be bigger than 1). Default is 1.5
    :-- t_ratio: trough-to-mean ratio. Default is 0.75
    :-- diurnal_freq: Frequency of modulation. Default is 1/24 (i.e., hourly)
        if you are generating multi-day TMs
    :-- spatial_variance: Variance on the volume of traffic between
        origin-destination pairs.
        Pick something reasonable with respect to your mean_traffic.
        Default is 100
    :-- temporal_variance: Variance on the volume in time. Default is 0.01
"""
num_nodes = 100
num_tms = 24
mean_traffic = 20000 #per OD kbps -- 75% of link capacities in network
pm_ratio = 1.5
diurnal_freq = 1/24 #generates tms per hours of day
t_ratio = .75
spatial_variance = 500
temporal_variance = 0.03
     
tm = modulated_gravity_tm(num_nodes,num_tms,mean_traffic,pm_ratio,t_ratio)#, spatial_variance,temporal_variance)

mean_load_tms_complete = []
total_load_tms_complete = []
# print("Tms complete:\n")
for i in range(num_tms):
    # print('Epoch',i,'\n')#,tm.at_time(i))
    # print(tm.at_time(i).mean())
    mean_load_tms_complete.append(tm.at_time(i).mean())
    # print(tm.at_time(i).sum())
    total_load_tms_complete.append(tm.at_time(i).sum())
    # print()

#choose randomly nodes for final traffic matrix
rand_od = [random.random(num_nodes) for i in range (num_nodes)]
od_bin = [[0 if i <= .3 else 1 for i in r_od] for r_od in rand_od] #70%of nodes communicate per tm
tms = [np.array(np.array(od_bin)*tm.at_time(i)).tolist() for i in range(num_tms)]

mean_load_tms_final = []
total_load_tms_final = []
print("Tms final 24:")
for i in range(num_tms):
    # print('Epoch',i,'\n')#,tms[i])
    # print(np.array(tms[i]).mean())
    mean_load_tms_final.append(np.array(tms[i]).mean())
    # print(np.array(tms[i]).sum())
    total_load_tms_final.append(np.array(tms[i]).sum())
    # print()

print("Amount tms 24: ",len(tms))
print('Mean load tms 24:\n', mean_load_tms_final)
print('Total load tms 24:\n', total_load_tms_final)

with open(str(num_nodes)+'Nodes_tms_info_24.pkl','wb') as f:
    pickle.dump([od_bin, tms],f)

#   [0,1,2,3,4,5, 6, 7, 8, 9,10,11,12,13,14,15,16,17,18,19,20,21,22,23] #index list tms
x = [4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23, 0, 1, 2,3] #hours as I chose to use and plot!!! index in tms
plt.plot(x,total_load_tms_final,marker = 'o', linestyle = '')
plt.title(str(num_nodes)+"Nodes topology loads (24)")
plt.xlabel('Tms')
plt.ylabel('Load (Mbps)')
plt.xticks(x)
plt.grid()
plt.savefig(str(num_nodes)+"Nodes_load_24.eps",bbox_inches = 'tight') 
plt.close()

#-------------Choosen tms for scripts traffic-------------
print("\n\nTms final 14:")
tms_14_hours = [0,1,3,5,7,9,10,11,12,14,16,18,20,22] #hours as I chose (14)
index_tms = [20,21,23,1,3,5,6,7,8,10,12,14,16,18] #index from tms 

tms_14 = [tms[i] for i in index_tms]
mean_load_tms_14 = [np.array(tms_14[i]).mean() for i in range(len(tms_14))]
total_load_tms_14 = [np.array(tms_14[i]).sum() for i in range(len(tms_14))]
print("Amount tms 14: ",len(tms_14))
print('Mean load tms 14:\n', mean_load_tms_14, len(mean_load_tms_14))
print('Total load tms 14:\n', total_load_tms_14, len(total_load_tms_14))

with open(str(num_nodes)+'Nodes_tms_info_14.pkl','wb') as f:
    pickle.dump([od_bin, tms_14],f)

plt.plot(tms_14_hours,total_load_tms_14,marker = 'o', linestyle = '')
plt.title(str(num_nodes)+"Nodes topology loads (14)")
plt.xlabel('Tms')
plt.ylabel('Load (Mbps)')
plt.xticks(tms_14_hours)
plt.grid()
plt.savefig(str(num_nodes)+"Nodes_load_14.eps",bbox_inches = 'tight') 
plt.close()


#--------------------GEANT----------------------
# geant_load = [5488416.834900001, 5043266.933899991, 5095276.160400002, 6880465.770500002, 9581002.970000016, 9705147.848200008, 9725804.7823, 9466881.377099995, 9276812.729499986, 8702496.461300002, 8453294.000400001, 8333976.977400003, 7917113.724099998, 8011548.747299995, 7522307.892499997, 6322587.761599998, 5872382.728099998]
# y = [0,1,3,5,7,9,11,12,13,14,15,16,17,18,19,21,23]
# plt.plot(y,geant_load)
# plt.title("Geant load")
# plt.xlabel('Tms')
# plt.ylabel('Load (Mbps)')
# # plt.legend(fontsize = 14,loc='lower right', fancybox=True, shadow=True)
# plt.savefig("loadGeant.eps",bbox_inches = 'tight') 
# plt.close()

# print('Rec values:\n')
# with open('tms_info.pkl', 'rb') as f:
#     rec_od_bin,rec_tms = pickle.load(f)
# print(rec_tms, rec_od_bin)
