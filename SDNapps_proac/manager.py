from operator import attrgetter

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.base.app_manager import lookup_service_brick
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.topology import event, switches
from ryu.ofproto.ether import ETH_TYPE_IP
from ryu.topology.api import get_switch, get_link
from ryu.ofproto import ofproto_v1_3
from ryu.lib import hub
from ryu.lib.packet import packet
from ryu.lib.packet import arp

# import sys
# sys.path.insert(0,'/home/controlador/ryu/ryu/app/SDNapps_proac/RoutingGeant')
# from main import get_all_paths
# import pandas as pd
import time

import simple_awareness
import simple_delay
import simple_monitor
import json, ast
import setting
import csv
import time

class Manager(app_manager.RyuApp):

    # _CONTEXTS = {"simple_delay": simple_delay.simple_Delay}#,
                  # "simple_awareness": simple_awareness.simple_Awareness,
                  #"simple_monitor": simple_monitor.simple_Monitor}

    def __init__(self, *args, **kwargs):
        super(Manager, self).__init__(*args, **kwargs)
        self.name = "manager"
        self.awareness = lookup_service_brick("awareness")
        self.delay = lookup_service_brick("delay")
        self.monitor = lookup_service_brick("monitor")
        # self.delay = kwargs["simple_delay"]

        self.link_loss = {}
        self.net_info = {}
        self.net_metrics= {}
        self.link_free_bw = {}
        self.link_used_bw = {}
        self.paths_metrics = {}
        # self.bwd_paths = {}
        # self.delay_paths = {}
        # self.loss_paths = {}
        

    # def get_flow_loss(self):
    #     #Get per flow loss
    #     bodies = self.monitor.stats['flow']
    #     for dp in bodies.keys():
    #         list_flows = sorted([flow for flow in bodies[dp] if flow.priority == 1], 
    #                             key=lambda flow: (flow.match.get('ipv4_src'),flow.match.get('ipv4_dst')))
    #         for stat in list_flows:
    #             out_port = stat.instructions[0].actions[0].port
    #             if self.awareness.link_to_port and out_port != 1: #get loss form ports of network
    #                 key = (stat.match.get('ipv4_src'), stat.match.get('ipv4_dst'))
    #                 tmp1 = self.flow_stats[dp][key]
    #                 # print('temp1 dp{0}, match: {1}: {2}'.format(dp,key,tmp1))
    #                 byte_count_src = tmp1[-1][1]
                    
    #                 result = self.get_sw_dst(dp, out_port)
    #                 dst_sw = result[0]
    #                 tmp2 = self.flow_stats[dst_sw][key]
    #                 # print('temp2 dp{0}, match: {1}: {2}'.format(dst_sw,key,tmp2))
    #                 byte_count_dst = tmp2[-1][1]
    #                 # print("----dp: {0}, byte count src:{1}".format(dst_sw, byte_count_dst))
    #                 flow_loss = byte_count_src - byte_count_dst
    #                 # # print("dpid: {0}, key: {1}, count_src: {2}, count_dst: {3}, loss: {4}".format(dpid,key,byte_count_src,byte_count_dst,flow_loss))
    #                 self.save_stats(self.flow_loss[dp], key, flow_loss, 5)
    #                 # print(self.flow_loss)

    # ----------------------Link metrics ------------------------- 
    
    def get_port_loss(self):
        #Get loss_port
        i = time.time()
        try:
            bodies = self.monitor.stats['port']
        except:
            self.monitor = lookup_service_brick('monitor')
            bodies = self.monitor.stats['port']

        for dp in sorted(bodies.keys()):
            for stat in sorted(bodies[dp], key=attrgetter('port_no')):
                if self.awareness.link_to_port and stat.port_no != 1 and stat.port_no != ofproto_v1_3.OFPP_LOCAL: #get loss form ports of network
                    key1 = (dp, stat.port_no)
                    # print(self.port_stats)
                    tmp1 = self.monitor.port_stats[key1]
                    tx_bytes_src = tmp1[-1][0]
                    tx_pkts_src = tmp1[-1][8]

                    key2 = self.monitor.get_sw_dst(dp, stat.port_no)
                    tmp2 = self.monitor.port_stats[key2]
                    rx_bytes_dst = tmp2[-1][1]
                    rx_pkts_dst = tmp2[-1][9]
                    # print('\ntemp1 dp{0}, key: {1}: tx {2}'.format(dp,key1,tx_pkts_src))
                    # print('temp2 dp{0}, key: {1}: rx{2}'.format(key2[0],key2,rx_pkts_dst))
                    loss_port = float(tx_pkts_src - rx_pkts_dst) / tx_pkts_src #loss rate
                    values = (loss_port, key2)
                    # print('tx_pkts: {0}, rx_pkts: {1}, loss: {2}'.format(tx_pkts_src, rx_pkts_dst, loss_port))
                    self.monitor.save_stats(self.monitor.port_loss[dp], key1, values, 5)

        #Calculates the total link loss and save it in self.link_loss[(node1,node2)]:loss
        for dp in self.monitor.port_loss.keys():
            for port in self.monitor.port_loss[dp]:
                key2 = self.monitor.port_loss[dp][port][-1][1]
                loss_src = self.monitor.port_loss[dp][port][-1][0]
                # tx_src = self.port_loss[dp][port][-1][1]
                loss_dst = self.monitor.port_loss[key2[0]][key2][-1][0]
                # tx_dst = self.port_loss[key2[0]][key2][-1][1]
                loss_l = max(abs(loss_src),abs(loss_dst)) #para DRL estoy cambiando cual es el loss del link... ahora es el max de los dos puertos, el peor de los casos, no el promedio
                link = (dp, key2[0])
                self.link_loss[link] = loss_l*100.0     #link loss ration in %
        # print(self.link_loss)
        # print('Time get_port_loss', time.time()-i)

    def get_link_free_bw(self):
        #Calculates the total free bw of link and save it in self.link_free_bw[(node1,node2)]:link_free_bw
        i = time.time()
        for dp in self.monitor.free_bandwidth.keys():
            for port in self.monitor.free_bandwidth[dp]:
                free_bw1 = self.monitor.free_bandwidth[dp][port]
                key2 = self.monitor.get_sw_dst(dp, port) #key2 = (dp,port)
                free_bw2= self.monitor.free_bandwidth[key2[0]][key2[1]]
                link_free_bw = min(free_bw1,free_bw2) #para DRL estoy cambiando cual es el bw del link... es el min de ambos, el peor de los caso, no el promedio
                link = (dp, key2[0])
                self.link_free_bw[link] = link_free_bw
        # print(self.free_bandwidth)
        # print('- - - - -  - - - - - - - - ')
        # print(self.link_free_bw)
        # print('Time to get link_free_bw', time.time()-i)

    def get_link_used_bw(self):
        #Calculates the total free bw of link and save it in self.link_free_bw[(node1,node2)]:link_free_bw
        i = time.time()
        for key in self.monitor.port_speed.keys():
            used_bw1 = self.monitor.port_speed[key][-1]
            key2 = self.monitor.get_sw_dst(key[0], key[1]) #key2 = (dp,port)
            used_bw2 = self.monitor.port_speed[key2][-1]
            link_used_bw = (used_bw1 + used_bw2)/2
            link = (key[0], key2[0])
            self.link_used_bw[link] = link_used_bw
        # print(self.link_free_bw)
        # print('Time to get link_used_bw', time.time()-i)

    def write_values(self):
        a = time.time()
        # self.delay = lookup_service_brick('delay')
        # print('\nwriting file............')
        # print(self.free_bandwidth[1][2] , self.free_bandwidth[7][4] )
        # print('- - - - -  - - - - - - - - ')
        # print(self.link_free_bw[(1, 7)], self.link_free_bw[(7, 1)])
        # print('- - - - -  - - - - - - - - ')
        # if self.delay is None:
        #     self.delay = app_manager.lookup_service_brick('delay')
        # else:    
        if self.delay is not None:
            for link in self.link_free_bw:
                # print('loss_links', self.link_loss)
                self.net_info[link] = [round(self.link_free_bw[link],6) , round(self.delay.link_delay[link],6), round(self.link_loss[link],6)]
                self.net_metrics[link] = [round(self.link_free_bw[link],6), round(self.link_used_bw[link],6), round(self.delay.link_delay[link],6), round(self.link_loss[link],6)]
                
            # print(self.net_info[(1, 7)])
            with open('/home/controlador/ryu/ryu/app/SDNapps_proac/net_info.csv','wb') as csvfile:
                header_names = ['node1','node2','bwd','delay','pkloss']
                file = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
                links_in = []
                file.writerow(header_names)
                for link, values in sorted(self.net_info.items()):
                    links_in.append(link)
                    tup = (link[1], link[0])
                    if tup not in links_in:
                        file.writerow([link[0],link[1], values[0],values[1],values[2]])

            file_metrics = '/home/controlador/ryu/ryu/app/SDNapps_proac/Metrics/'+str(self.monitor.count_monitor)+'_net_metrics.csv'
            with open(file_metrics,'wb') as csvfile:
                header_ = ['node1','node2','free_bw','used_bw','delay','pkloss']
                file = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
                links_in = []
                file.writerow(header_)
                for link, values in sorted(self.net_metrics.items()):
                    links_in.append(link)
                    tup = (link[1], link[0])
                    if tup not in links_in:
                        file.writerow([link[0],link[1],values[0],values[1],values[2],values[3]]) 
            b = time.time() 
            # print('total writing time: {0}'.format(b-a))
            return
        else:
            self.delay = lookup_service_brick('delay')
            # if self.delay.link_delay:
            for link in self.link_free_bw:
                # print('fre_links', self.link_free_bw)
                # print('loss_links', self.link_loss)
                self.net_info[link] = [round(self.link_free_bw[link],6) , round(self.delay.link_delay[link],6), round(self.link_loss[link],6)]
                self.net_metrics[link] = [round(self.link_free_bw[link],6), round(self.link_used_bw[link],6), round(self.delay.link_delay[link],6), round(self.link_loss[link],6)]
        
            # print(self.net_info[(1, 7)])
            with open('/home/controlador/ryu/ryu/app/SDNapps_proac/net_info.csv','wb') as csvfile:
                header_names = ['node1','node2','bwd','delay','pkloss']
                file = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
                links_in = []
                file.writerow(header_names)
                for link, values in sorted(self.net_info.items()):
                    links_in.append(link)
                    tup = (link[1], link[0])
                    if tup not in links_in:
                        file.writerow([link[0],link[1], values[0],values[1],values[2]])

            file_metrics = '/home/controlador/ryu/ryu/app/SDNapps_proac/Metrics/'+str(self.monitor.count_monitor)+'_net_metrics.csv'
            with open(file_metrics,'wb') as csvfile:
                header_ = ['node1','node2','free_bw','used_bw','delay','pkloss']
                file = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
                links_in = []
                file.writerow(header_)
                for link, values in sorted(self.net_metrics.items()):
                    links_in.append(link)
                    tup = (link[1], link[0])
                    if tup not in links_in:
                        file.writerow([link[0],link[1],values[0],values[1],values[2],values[3]]) 
            b = time.time()            
            # print('total writing time: {0}'.format(b-a))
            return

    # ----------Path metrics -------- 
    def get_k_paths_nodes(self,shortest_paths,src,dst):
        k_paths = shortest_paths[src][dst]
        return k_paths

    def calc_bwd_path(self,bwd_links_path):
        '''
        path = [link1, link2, link3]
        path_bwd = min(bwd of all links)
        '''
        bwd_path = min(bwd_links_path)
        return round(bwd_path,6)

    def calc_delay_path(self,delay_links_path):
        '''
        path = [link1, link2, link3]
        path_ldelay = sum(delay of all links)
        '''
        delay_path = sum(delay_links_path)
        return round(delay_path,6)

    def calc_loss_path(self,loss_links_path): 
        '''
        path = [link1, link2, link3]
        path_loss = 1-[(1-loss_link1)*(1-loss_link2)*(1-loss_link3)]
        '''
        loss_links_path_ = [1-(i/100.0) for i in loss_links_path]
        result_multi = reduce((lambda x, y: x * y), loss_links_path_)
        loss_path = 1.0 - result_multi
        return round(loss_path*100.0,6)

    def metrics_links_kpaths(self,k_paths,bwd_links,delay_links,loss_links):
        '''
        Calculates the metrics for k_paths of a pair of nodes src - dst
        k_paths = [path1, path2, ..., pathk]

        '''
        bwd_paths_nodes = []
        delay_paths_nodes = []
        loss_paths_nodes = []

        # print('------****',src,dst)
        for path in k_paths:
            # print('------',src,dst,path)
            bwd_links_path = []
            delay_links_path = []
            loss_links_path = []
            for i in range(len(path)-1):
                link_ = (path[i],path[i+1])

                bwd = round(bwd_links[link_],6)
                delay = round(delay_links[link_],6)
                loss = round(loss_links[link_],6)

                bwd_links_path.append(bwd)
                delay_links_path.append(delay)
                loss_links_path.append(loss)

            bwd_path = self.calc_bwd_path(bwd_links_path)
            bwd_paths_nodes.append(bwd_path)

            delay_path = self.calc_delay_path(delay_links_path)
            delay_paths_nodes.append(delay_path)

            loss_path = self.calc_loss_path(loss_links_path)
            loss_paths_nodes.append(loss_path)

        # bwd_paths[src][dst] = bwd_paths_nodes
        # delay_paths[src][dst] = delay_paths_nodes
        # loss_paths[src][dst] = loss_paths_nodes

        return bwd_paths_nodes,delay_paths_nodes,loss_paths_nodes

    def get_k_paths_metrics_dic(self,shortest_paths,bwd_links,delay_links,loss_links):
        ''' escribe las metricas en un solo diccionario todas juntas distingiendo en el dic
            con llaves 'bwd', 'delay','loss'
            pahts_metrics[src][dst]['bwd']:[bwd1,...,bwdk], pahts_metrics[src][dst]['delay']:[delay1,...,delay2]
        '''
        i = time.time()
        # print('Entra paths metrics')
        metrics = ['bwd_paths','delay_paths','loss_paths']
        # print('------switches',self.awareness.switches)
        for sw in shortest_paths.keys():
            self.paths_metrics.setdefault(sw,{})
            for sw2 in shortest_paths.keys():
                if sw != sw2:
                    self.paths_metrics[sw].setdefault(sw2,{})
                    for m in metrics:
                        self.paths_metrics[sw][sw2].setdefault(m,)

            # if shortest_paths is not None:
         
        for src in shortest_paths.keys():
            for dst in shortest_paths[src].keys():
                if src != dst:
                    k_paths = self.get_k_paths_nodes(shortest_paths,src,dst)
                    bwd_paths_nodes, delay_paths_nodes, loss_paths_nodes = self.metrics_links_kpaths(k_paths,bwd_links,delay_links,loss_links)      
                    # print('---',src,dst,bwd_paths_nodes, delay_paths_nodes, loss_paths_nodes)
                    self.paths_metrics[src][dst][metrics[0]] = [bwd_paths_nodes]
                    self.paths_metrics[src][dst][metrics[1]] = [delay_paths_nodes]
                    self.paths_metrics[src][dst][metrics[2]] = [loss_paths_nodes]
        # print('paths_metrics',self.paths_metrics)
        print('writing paths_metrics')
        
        with open('/home/controlador/ryu/ryu/app/SDNapps_proac/paths_metrics.json','w') as json_file:
            json.dump(self.paths_metrics, json_file, indent=2) 
        
        print('------****metrics k_paths', time.time()-i)

    def get_k_paths_metrics(self,shortest_paths,bwd_links,delay_links,loss_links):
        ''' escribe las metricas en un diccionario por separado
            bwd_paths [src][dst]:[bwd1,bwd1,bwd3...,bwdk]''' 
        for sw in self.awareness.switches:
            self.bwd_paths.setdefault(sw,{})
            self.delay_paths.setdefault(sw,{})
            self.loss_paths.setdefault(sw,{})
            for sw2 in self.awareness.switches:
                if sw != sw2:
                    self.bwd_paths[sw].setdefault(sw2,[])
                    self.delay_paths[sw].setdefault(sw2,[])
                    self.loss_paths[sw].setdefault(sw2,[])

        if shortest_paths is not None:
            for src in shortest_paths.keys():
                for dst in shortest_paths[src].keys():
                    if src != dst:
                        k_paths = self.get_k_paths_nodes(shortest_paths,src,dst)
                        bwd_paths_nodes, delay_paths_nodes, loss_paths_nodes = self.metrics_links_kpaths(k_paths,bwd_links,delay_links,loss_links)      
                        self.bwd_paths[src][dst] = bwd_paths_nodes
                        self.delay_paths[src][dst] = delay_paths_nodes
                        self.loss_paths[src][dst] = loss_paths_nodes
            # print('bwd_paths',self.bwd_paths) 
            # print('delay_paths',self.delay_paths)
            # print('loss_paths',self.loss_paths)
            
            return 

    # def write_values_paths(self):
    #     a = time.time()
           
    #     if self.delay is not None:
    #         for link in self.link_free_bw:
    #             self.net_info[link] = [round(self.link_free_bw[link],6), round(self.delay.link_delay[link],6), round(self.link_loss[link],6)]
    #             self.net_metrics[link] = [round(self.link_free_bw[link],6), round(self.link_used_bw[link],6), round(self.delay.link_delay[link],6), round(self.link_loss[link],6)]
                
    #         # print(self.net_info[(1, 7)])
    #         with open('/home/controlador/ryu/ryu/app/SDNapps_proac/net_info.csv','wb') as csvfile:
    #             header_names = ['node1','node2','bwd','delay','pkloss']
    #             file = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
    #             links_in = []
    #             file.writerow(header_names)
    #             for link, values in sorted(self.net_info.items()):
    #                 links_in.append(link)
    #                 tup = (link[1], link[0])
    #                 if tup not in links_in:
    #                     file.writerow([link[0],link[1], values[0],values[1],values[2]])

    #         file_metrics = '/home/controlador/ryu/ryu/app/SDNapps_proac/Metrics/'+str(self.monitor.count_monitor)+'_net_metrics.csv'
    #         with open(file_metrics,'wb') as csvfile:
    #             header_ = ['node1','node2','free_bw','used_bw','delay','pkloss']
    #             file = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
    #             links_in = []
    #             file.writerow(header_)
    #             for link, values in sorted(self.net_metrics.items()):
    #                 links_in.append(link)
    #                 tup = (link[1], link[0])
    #                 if tup not in links_in:
    #                     file.writerow([link[0],link[1],values[0],values[1],values[2],values[3]]) 
    #         b = time.time()            
    #         # print('total writing time: {0}'.format(b-a))
    #         return
    #     else:
    #         self.delay = lookup_service_brick('delay')
    #         # if self.delay.link_delay:
    #         for link in self.link_free_bw:
    #             # print('fre_links', self.link_free_bw)
    #             print('loss_links', self.link_loss)
    #             self.net_info[link] = [round(self.link_free_bw[link],6) , round(self.delay.link_delay[link],6), round(self.link_loss[link],6)]
    #             self.net_metrics[link] = [round(self.link_free_bw[link],6), round(self.link_used_bw[link],6), round(self.delay.link_delay[link],6), round(self.link_loss[link],6)]
        
    #         # print(self.net_info[(1, 7)])
    #         with open('/home/controlador/ryu/ryu/app/SDNapps_proac/net_info.csv','wb') as csvfile:
    #             header_names = ['node1','node2','bwd','delay','pkloss']
    #             file = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
    #             links_in = []
    #             file.writerow(header_names)
    #             for link, values in sorted(self.net_info.items()):
    #                 links_in.append(link)
    #                 tup = (link[1], link[0])
    #                 if tup not in links_in:
    #                     file.writerow([link[0],link[1], values[0],values[1],values[2]])

    #         file_metrics = '/home/controlador/ryu/ryu/app/SDNapps_proac/Metrics/'+str(self.monitor.count_monitor)+'_net_metrics.csv'
    #         with open(file_metrics,'wb') as csvfile:
    #             header_ = ['node1','node2','free_bw','used_bw','delay','pkloss']
    #             file = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
    #             links_in = []
    #             file.writerow(header_)
    #             for link, values in sorted(self.net_metrics.items()):
    #                 links_in.append(link)
    #                 tup = (link[1], link[0])
    #                 if tup not in links_in:
    #                     file.writerow([link[0],link[1],values[0],values[1],values[2],values[3]]) 
    #         b = time.time()            
    #         # print('total writing time: {0}'.format(b-a))
    #         return