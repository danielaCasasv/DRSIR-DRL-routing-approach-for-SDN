from ryu import cfg
from ryu.app import simple_switch_stp_13
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4
from ryu.lib.packet import tcp
from ryu.lib.packet import udp
import pandas as pd

import simple_awareness
# import simple_monitor
import simple_delay
import setting
import time

CONF = cfg.CONF


class baseline_dijsktra(app_manager.RyuApp):


    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {
        "simple_awareness": simple_awareness.simple_Awareness,
        # "simple_monitor": simple_monitor.simple_Monitor}
        "simple_delay": simple_delay.simple_Delay}

    def __init__(self, *args, **kwargs):
        super(baseline_dijsktra, self).__init__(*args, **kwargs)

        self.awareness = kwargs["simple_awareness"]
        # self.monitor = kwargs["simple_monitor"]
        self.delay = kwargs["simple_delay"]
        self.datapaths = {}
 
    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        """
            Collect datapath information.
        """
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def add_flow(self, dp, priority, match, actions, idle_timeout=10):
        """
            Send a flow entry to datapath.
        """
        ini_time_send = time.time()
        ofproto = dp.ofproto
        parser = dp.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=dp, priority=priority,
                                idle_timeout=idle_timeout,
                                match=match, instructions=inst)
        dp.send_msg(mod)
        end_time_send = time.time()
        total_send = end_time_send - ini_time_send

    def send_flow_mod(self, datapath, flow_info, src_port, dst_port, idle, hard):
        """
            Build flow entry, and send it to datapath.
        """
        parser = datapath.ofproto_parser
        actions = []
        actions.append(parser.OFPActionOutput(dst_port))

        # match = parser.OFPMatch(
        #     in_port=src_port, eth_type=flow_info[0],
        #     ipv4_src=flow_info[1], ipv4_dst=flow_info[2])
        match = parser.OFPMatch(eth_type=flow_info[0],
            ipv4_src=flow_info[1], ipv4_dst=flow_info[2])

        self.add_flow(datapath, 1, match, actions,
                      idle_timeout=idle)

    def _build_packet_out(self, datapath, buffer_id, src_port, dst_port, data):
        """
            Build packet out object.
        """
        actions = []
        if dst_port:
            actions.append(datapath.ofproto_parser.OFPActionOutput(dst_port))

        msg_data = None
        if buffer_id == datapath.ofproto.OFP_NO_BUFFER:
            if data is None:
                return None
            msg_data = data

        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=buffer_id,
            data=msg_data, in_port=src_port, actions=actions)
        return out

    def send_packet_out(self, datapath, buffer_id, src_port, dst_port, data):
        """
            Send packet out packet to assigned datapath.
            The controller uses this message to send a packet out throught the switch.
        """
        out = self._build_packet_out(datapath, buffer_id,
                                     src_port, dst_port, data)
        if out:
            datapath.send_msg(out)

    def get_port(self, dst_ip, access_table): 
        """
            Get access port of dst host.
            access_table = {(sw,port):(ip, mac),}
        """
        if access_table:
            if isinstance(access_table.values()[0], tuple):
                for key in access_table.keys():
                    if dst_ip == access_table[key][0]:   # Use the IP address only, not the MAC address. (hmc)
                        dst_port = key[1]
                        return dst_port
        return None

    def get_port_pair_from_link(self, link_to_port, src_dpid, dst_dpid):
        """
            Get port pair of link, so that controller can install flow entry.
            link_to_port = {(src_dpid,dst_dpid):(src_port,dst_port),}
        """
        if (src_dpid, dst_dpid) in link_to_port:
            return link_to_port[(src_dpid, dst_dpid)]
        else:
            self.logger.info("Link from dpid:%s to dpid:%s is not in links" %
             (src_dpid, dst_dpid))
            return None

    def flood(self, msg):
        """
            Flood packet to the access ports which have no record of host.
            access_ports = {dpid:set(port_num,),}
            access_table = {(sw,port):(ip, mac),}
        """
        datapath = msg.datapath
        ofproto = datapath.ofproto

        for dpid in self.awareness.access_ports:
            for port in self.awareness.access_ports[dpid]:
                if (dpid, port) not in self.awareness.access_table.keys(): 
                    datapath = self.datapaths[dpid]
                    out = self._build_packet_out(
                        datapath, ofproto.OFP_NO_BUFFER,
                        ofproto.OFPP_CONTROLLER, port, msg.data)
                    datapath.send_msg(out)
        self.logger.debug("Flooding packet to access port")

    def arp_forwarding(self, msg, src_ip, dst_ip):
        """
            Send ARP packet to the destination host if the dst host record
            is existed, else flow it to the unknow access port.
            result = (datapath, port) of host
        """
        datapath = msg.datapath
        ofproto = datapath.ofproto

        result = self.awareness.get_host_location_arp(dst_ip)
        if result:
            # Host has been recorded in access table.
            datapath_dst, out_port = result[0], result[1]
            datapath = self.datapaths[datapath_dst]
            out = self._build_packet_out(datapath, ofproto.OFP_NO_BUFFER,
                                         ofproto.OFPP_CONTROLLER,
                                         out_port, msg.data)
            datapath.send_msg(out)
            self.logger.debug("Deliver ARP packet to knew host")
        else:
            # Flood is not good.
            # self.flood(msg)
            pass

    # def get_path(self, src, dst):
        
    #     # Because all paths will be calculated when we call self.monitor.get_RL_paths,
    #     # so we just need to call it once in a period, and then, we can get path directly.
    #     # If path is existed just return it, else calculate and return it.
    #     ini_time_path = time.time()
    #     paths = self.monitor.paths
    #     # if paths != None:
    #     print ('PATHS: OK')
    #     path = paths.get(src).get(dst)[0]
    #     end_time_path = time.time()
    #     total_path = end_time_path - ini_time_path
    #     print("Time path function ", total_path)
    #     return path
        
    #     # else:
    #     #     print('Getting paths: OK')
    #     #     result = self.monitor.get_RL_paths()
    #     #     #result = (paths, time_rl)
    #     #     paths = result[0]
    #     #     # print("#####PATHS: {0}".format(paths))
    #     #     # print(src)
    #     #     # print("#####",paths.get(src))
    #     #     path = paths.get(src).get(dst)[0]
    #     #     # print('Path result: ', path)
    #     #     return path
        
    def dijkstra(self, graph, src, dest, visited=[], distances={}, predecessors={}):
        """ 
        Calculates a shortest path tree routed in src
        """
        # a few sanity checks
        if src not in graph:
            raise TypeError('The root of the shortest path tree cannot be found')
        if dest not in graph:
            raise TypeError('The target of the shortest path cannot be found')
        # ending condition
        if src == dest:
            # We build the shortest path
            path = []
            pred = dest
            while pred != None:
                path.append(pred)
                pred = predecessors.get(pred, None)
            path_= list(reversed(path))
            # print(path_)
            return path_
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
            x = min(unvisited, key=unvisited.get) #find w not in N such that D(w) is a minimum
            return self.dijkstra(graph, x, dest, visited, distances, predecessors)


    def install_flow(self, datapaths, link_to_port, access_table, path,
                     flow_info, buffer_id, data=None):
        ''' 
            Install flow entires for roundtrip: go and back.
            @parameter: path=[dpid1, dpid2...]
                        flow_info=(eth_type, src_ip, dst_ip, in_port)
        '''
        init_time_install = time.time()
        if path is None or len(path) == 0:
            self.logger.info("Path error!")
            return
        in_port = flow_info[3]

        first_dp = datapaths[path[0]]

        # print("\tFor 1st dp {0}:".format(first_dp))

        out_port = first_dp.ofproto.OFPP_LOCAL
        back_info = (flow_info[0], flow_info[2], flow_info[1])
        idle_base = 15
        hard_base = 60
        inc = 2 

        # Flow installing por middle datapaths in path
        if len(path) > 2:
            for i in xrange(1, len(path)-1):
                port = self.get_port_pair_from_link(link_to_port,
                                                    path[i-1], path[i])
                port_next = self.get_port_pair_from_link(link_to_port,
                                                         path[i], path[i+1])
                if port and port_next:
                    src_port, dst_port = port[1], port_next[0]
                    datapath = datapaths[path[i]]
                    idle_go = idle_base + i*inc
                    hard_go = hard_base + i*inc
                    idle_back = idle_base + (len(path)-1)*2 - i*inc
                    hard_back = hard_base + (len(path)-1)*2 - i*inc
                    self.send_flow_mod(datapath, flow_info, src_port, dst_port, idle_go, hard_go)
                    self.send_flow_mod(datapath, back_info, dst_port, src_port, idle_back, hard_back)
                    print("Inter link flow install", "---go", idle_go, hard_go, "---back", idle_back, hard_back)
        if len(path) > 1:
            # the last flow entry: tor -> host
            idle_last = idle_base + (len(path)-1)*2
            hard_last = hard_base + (len(path)-1)*2
            port_pair = self.get_port_pair_from_link(link_to_port,
                                                     path[-2], path[-1])
            if port_pair is None:
                self.logger.info("Port is not found")
                return
            src_port = port_pair[1]

            dst_port = self.get_port(flow_info[2], access_table)
            if dst_port is None:
                self.logger.info("Last port is not found.")
                return

            last_dp = datapaths[path[-1]]
            self.send_flow_mod(last_dp, flow_info, src_port, dst_port, idle_last, hard_last)
            self.send_flow_mod(last_dp, back_info, dst_port, src_port, idle_base, hard_base)
            print("Last link flow install","---go", idle_last, hard_last, "---back", idle_base, hard_base)

            # the first flow entry
            port_pair = self.get_port_pair_from_link(link_to_port,
                                                     path[0], path[1])
            if port_pair is None:
                self.logger.info("Port not found in first hop.")
                return
            out_port = port_pair[0]
            self.send_flow_mod(first_dp, flow_info, in_port, out_port, idle_base, hard_base)
            self.send_flow_mod(first_dp, back_info, out_port, in_port, idle_last, hard_last)
            self.send_packet_out(first_dp, buffer_id, in_port, out_port, data)
            print("First link flow install", "---go",idle_base, hard_base, "---back", idle_last, hard_last)

        # src and dst on the same datapath
        else:
            out_port = self.get_port(flow_info[2], access_table)
            if out_port is None:
                self.logger.info("Out_port is None in same dp")
                return
            self.send_flow_mod(first_dp, flow_info, in_port, out_port, idle_base, hard_base)
            self.send_flow_mod(first_dp, back_info, out_port, in_port, idle_base, hard_base)
            self.send_packet_out(first_dp, buffer_id, in_port, out_port, data)
        
        end_time_install = time.time()
        total_install = end_time_install - init_time_install
        print("Time install", total_install)

    def _forwarding(self, msg, eth_type, ip_src, ip_dst):
        ini_time_forw = time.time()
        """
            Get paths and install them into datapaths.
        """
        datapath = msg.datapath
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        print('\ndpid: {0}, in_port:{1}, ip_src: {2}, ip_dst: {3}'.format(dpid, in_port, ip_src, ip_dst))
        # print(self.awareness.access_ports[dpid], self.awareness.access_table)
        if len(self.awareness.access_table) == 23 :
            if in_port in self.awareness.access_ports[dpid]:
                print ("@@@@@@2 Looking ip_src {0} and ip_dst {1}".format(ip_src,ip_dst))
                src_location = self.awareness.get_host_location(ip_src)   # src_location = (dpid, port)
                # if (dpid, in_port) == src_location:
                src_sw = src_location[0]
                dst_location = self.awareness.get_host_location(ip_dst)   # dst_location = (dpid, port)
                # if dst_location:
                dst_sw = dst_location[0]
                # if src_sw and dst_sw:
                #     return src_sw, dst_sw
                # else:
                #     raise Exception ("Didn't find hosts src dst locations")
                #     # return "Didn't find hosts ip_src ip_dst locations"
                
                # print("@@@@@@@2",result)
                # if result:
                #     src_sw, dst_sw = result[0], result[1]
                # if dst_sw:
                    # Path has already calculated, just get it.
                if src_sw and dst_sw:    
                    print("@@@@@@@1",src_sw, dst_sw)
                    
                    path = self.dijkstra(self.delay.delay_dict,src_sw, dst_sw)
                    print("[PATH]{0}<-->{1}: {2}".format(ip_src, ip_dst, path))
                    flow_info = (eth_type, ip_src, ip_dst, in_port)
                    # install flow entries to datapath along side the path.
                    # self.install_flow(self.datapaths,
                    #                   self.awareness.link_to_port,
                    #                   self.awareness.access_table, path,
                    #                   flow_info, msg.buffer_id, msg.data)
                end_time_forw = time.time()
                total_forw = end_time_forw - ini_time_forw
                print("Time forwarding function: ", total_forw)
                return

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        '''
            In packet_in handler, we need to learn access_table by ARP and IP packets.
            Therefore, the first packet from UNKOWN host MUST be ARP
        '''
        msg = ev.msg
        pkt = packet.Packet(msg.data)
        arp_pkt = pkt.get_protocol(arp.arp)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        # print('packet type ARP{0} IP{1}'.format(arp_pkt,ip_pkt))
        if isinstance(arp_pkt, arp.arp):
            # print('Packet In!!')
            # print("ARP processing")
            self.arp_forwarding(msg, arp_pkt.src_ip, arp_pkt.dst_ip)

        if isinstance(ip_pkt, ipv4.ipv4):
            # print("IPV4 processing")h=datapath, command=datapath.ofproto.OFPFC_ADD,
            if len(pkt.get_protocols(ethernet.ethernet)):
                eth_type = pkt.get_protocols(ethernet.ethernet)[0].ethertype
                #FUNCION DE FORWARDING BY THE LEARNED IN RL
                self._forwarding(msg, eth_type, ip_pkt.src, ip_pkt.dst)
