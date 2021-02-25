from __future__ import division
from ryu import cfg
from ryu.base import app_manager
from ryu.base.app_manager import lookup_service_brick
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import hub
from ryu.topology.switches import Switches
from ryu.topology.switches import LLDPPacket
from ryu.app import simple_switch_13
import networkx as nx
import time
import json,ast
import csv
import setting

import simple_awareness
import simple_monitor

CONF = cfg.CONF
num_nodes = 32

class simple_Delay(app_manager.RyuApp):
    """
        A Ryu app for calculating link delay by using echo replay
        messages from the Control Plane to the datapaths in the Data Plane.
        It is part of the Statistics module of the Control Plane
        
    """
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(simple_Delay, self).__init__(*args, **kwargs)
        self.name = "delay"
        self.sending_echo_request_interval = 0.1
        self.sw_module = lookup_service_brick('switches')
        self.monitor = lookup_service_brick('monitor')
        self.awareness = lookup_service_brick('awareness')
        self.count = 0
        self.datapaths = {}
        self.echo_latency = {}
        self.link_delay = {}
        self.delay_dict = {}
        self.measure_thread = hub.spawn(self._detector)

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                self.logger.debug('Register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('Unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _detector(self):
        """
            Delay detecting functon.
            Send echo request and calculate link delay periodically
        """
        while True:
            self.count += 1
            self._send_echo_request()
            self.create_link_delay()
            try:
                self.awareness.shortest_paths = {}
                self.logger.debug("Refresh the shortest_paths")
            except:
                self.awareness = lookup_service_brick('awareness')
            if self.awareness is not None:
                self.show_delay_statis()
            hub.sleep(setting.DELAY_DETECTING_PERIOD)

    def _send_echo_request(self):
        """
            Seng echo request msg to datapath.
        """
        for datapath in self.datapaths.values():
            parser = datapath.ofproto_parser
            echo_req = parser.OFPEchoRequest(datapath,
                                             data="%.12f" % time.time())
            datapath.send_msg(echo_req)
            # Important! Don't send echo request together, it will
            # generate a lot of echo reply almost in the same time.
            # which will generate a lot of delay of waiting in queue
            # when processing echo reply in echo_reply_handler.

            hub.sleep(self.sending_echo_request_interval)

    @set_ev_cls(ofp_event.EventOFPEchoReply, MAIN_DISPATCHER)
    def echo_reply_handler(self, ev):
        """
            Handle the echo reply msg, and get the latency of link.
        """
        now_timestamp = time.time()
        try:
            latency = now_timestamp - eval(ev.msg.data)
            self.echo_latency[ev.msg.datapath.id] = latency
        except:
            return

    def get_delay(self, src, dst):
        """
            Get link delay.
                        Controller
                        |        |
        src echo latency|        |dst echo latency
                        |        |
                   SwitchA-------SwitchB
                        
                    fwd_delay--->
                        <----reply_delay
            delay = (forward delay + reply delay - src datapath's echo latency
        """
        try:
            fwd_delay = self.awareness.graph[src][dst]['lldpdelay']
            re_delay = self.awareness.graph[dst][src]['lldpdelay']
            src_latency = self.echo_latency[src]
            dst_latency = self.echo_latency[dst]
            delay = (fwd_delay + re_delay - src_latency - dst_latency)/2
            return max(delay, 0)
        except:
            return float('inf')

    def _save_lldp_delay(self, src=0, dst=0, lldpdelay=0):
        try:
            self.awareness.graph[src][dst]['lldpdelay'] = lldpdelay
        except:
            if self.awareness is None:
                self.awareness = lookup_service_brick('awareness')
            return

    def create_link_delay(self):
        """
            Create link delay data, and save it into graph object.
        """
        try:
            for src in self.awareness.graph:
                for dst in self.awareness.graph[src]:
                    if src == dst:
                        self.awareness.graph[src][dst]['delay'] = 0
                        continue
                    delay = self.get_delay(src, dst)
                    self.awareness.graph[src][dst]['delay'] = delay
            if self.awareness is not None:
                for dp in self.awareness.graph:
                    self.delay_dict.setdefault(dp, {})
                self.get_link_delay()
        except:
            if self.awareness is None:
                self.awareness = lookup_service_brick('awareness')
            return
           

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """
            Explore LLDP packet and get the delay of link (fwd and reply).
        """
        msg = ev.msg
        try:
            src_dpid, src_port_no = LLDPPacket.lldp_parse(msg.data)
            dpid = msg.datapath.id
            if self.sw_module is None:
                self.sw_module = lookup_service_brick('switches')

            for port in self.sw_module.ports.keys():
                if src_dpid == port.dpid and src_port_no == port.port_no:
                    delay = self.sw_module.ports[port].delay
                    self._save_lldp_delay(src=src_dpid, dst=dpid,
                                          lldpdelay=delay)
        except LLDPPacket.LLDPUnknownFormat as e:
            return

    def get_link_delay(self):
        '''
        Calculates total link dealy and save it in self.link_delay[(node1,node2)]: link_delay
        '''
        for src in self.awareness.graph:
            for dst in self.awareness.graph[src]:
                if src != dst:
                    delay1 = self.awareness.graph[src][dst]['delay']
                    delay2 = self.awareness.graph[dst][src]['delay']
                    link_delay = ((delay1 + delay2)*1000.0)/2 #saves in ms
                    link = (src, dst)
                    self.link_delay[link] = link_delay
                    self.delay_dict[src][dst] = link_delay
        
        if self.monitor is None:
            print('No monitor')
            self.monitor = lookup_service_brick('monitor')
            
        if self.awareness.link_to_port:
            self.write_dijkstra_paths()

    def write_dijkstra_paths(self):
        # loss_dict_cost = {} #Free bw in value of cost for dijsktra (1/bwd)
        loss_dict = {} #dictionary in format for pass to dijkstra
        for dp in self.awareness.switches:
            loss_dict.setdefault(dp,{})

        for link in self.monitor.link_loss:
            loss_dict[link[0]][link[1]] = self.monitor.link_loss[link]
        # print('loss dict', loss_dict)
        print('writing paths file')
        time_init = time.time()
        paths = {}
        for dp in self.awareness.switches:
            paths.setdefault(dp,{})
        for src in self.awareness.switches:
            for dst in self.awareness.switches:
                if src != dst:
                    paths[src][dst] = self.dijkstra(loss_dict, src, dst, visited=[], distances={}, predecessors={})
        
        with open('/home/controlador/ryu/ryu/app/OSPF_loss/Proac/paths_loss.json','w') as json_file:
            json.dump(paths, json_file, indent=2)
        
        total_time = time.time() - time_init
        # print(total_time)
        with open('/home/controlador/ryu/ryu/app/OSPF_loss/Proac/times.txt','a') as txt_file:
            txt_file.write(str(total_time)+'\n')
        self.calc_stretch()

    def dijkstra(self, graph, src, dest, visited=[], distances={}, predecessors={}):
        """ calculates a shortest path tree routed in src
        """

        # a few sanity checks
        if src not in graph:
            raise TypeError('The root of the shortest path tree cannot be found')
        if dest not in graph:
            raise TypeError('The target of the shortest path cannot be found')
        # ending condition
        if src == dest:
            # We build the shortest path and display it
            path = []
            pred = dest
            while pred != None:
                path.append(pred)
                pred = predecessors.get(pred, None)
            
            return list(reversed(path))
        else:
            # if it is the initial  run, initializes the cost
            if not visited:
                distances[src] = 0
            # visit the neighbors
            for neighbor in graph[src]:
                if neighbor not in visited:
                    new_distance = distances[src] + graph[src][neighbor]
                    if new_distance < distances.get(neighbor, float('inf')):
                        distances[neighbor] = new_distance
                        predecessors[neighbor] = src
            # mark as visited

            visited.append(src)
            # now that all neighbors have been visited: recurse
            # select the non visited node with lowest distance 'x'
            # run Dijskstra with src='x'
            unvisited = {}
            for k in graph:
                if k not in visited:
                    unvisited[k] = distances.get(k, float('inf')) #sets the cost of link to the src neighbors with the actual value and inf for the non neighbors
            x = min(unvisited, key=unvisited.get) #find w not in N' such that D(w) is a minimum
            return self.dijkstra(graph, x, dest, visited, distances, predecessors)

    def get_paths_dijkstra(self):
        file_dijkstra = '/home/controlador/ryu/ryu/app/OSPF_loss/Proac/paths_loss.json'
        with open(file_dijkstra,'r') as json_file:
            paths_dict = json.load(json_file)
            paths_dijkstra = ast.literal_eval(json.dumps(paths_dict))
            return paths_dijkstra

    def get_paths_base(self):
        file_base = '/home/controlador/ryu/ryu/app/SDNapps_proac/RoutingGeant/DRL/dRSIR/'+str(num_nodes)+'nodos/paths_weight.json'
        with open(file_base,'r') as json_file:
            paths_dict = json.load(json_file)
            paths_base = ast.literal_eval(json.dumps(paths_dict))
            return paths_base

    def stretch(self, paths, paths_base, src, dst):    
        add_stretch = len(paths.get(str(src)).get(str(dst))) - len(paths_base.get(str(src)).get(str(dst)))
        mul_stretch = len(paths.get(str(src)).get(str(dst))) / len(paths_base.get(str(src)).get(str(dst)))
        return add_stretch, mul_stretch

    def calc_stretch(self):
        # print('Calculating stretch...')
        paths_base = self.get_paths_base()
        paths_dijkstra = self.get_paths_dijkstra()
        cont_dijkstra = 0
        a = time.time()
        sw = [i for i in range(1,num_nodes+1)]
        
        with open('/home/controlador/ryu/ryu/app/OSPF_loss/Proac/stretch/'+str(self.count)+'_stretch.csv','wb') as csvfile:
            header = ['src','dst','add_st','mul_st']
            file = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
            file.writerow(header)
            for src in sw:
                for dst in sw:
                    if src != dst:
                        add_stretch, mul_stretch = self.stretch(paths_dijkstra, paths_base, src, dst)
                        # print(add_stretch)
                        # print(mul_stretch)
                        file.writerow([src, dst, add_stretch, mul_stretch])
        total_time = time.time() - a

    def show_delay_statis(self):
        if self.awareness is None:
            print("Not doing nothing, awareness none")
        # else:
        #     print("Latency ok")
        # if setting.TOSHOW and self.awareness is not None:
        #     self.logger.info("\nsrc   dst      delay")
        #     self.logger.info("---------------------------")
        #     for src in self.awareness.graph:
        #         for dst in self.awareness.graph[src]:
        #             delay = self.awareness.graph[src][dst]['delay']
        #             self.logger.info("%s   <-->   %s :   %s" % (src, dst, delay))

