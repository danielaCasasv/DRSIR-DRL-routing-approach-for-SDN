from operator import attrgetter

from ryu.base import app_manager
from ryu.controller import ofp_event
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

import time
import simple_awareness
import simple_delay
import simple_monitor
# import requests
import json, ast
import setting
import csv
import time

class baseline_Dijsktra(app_manager.RyuApp):
    '''
    A Ryu app that route traffic based on Dijkstra algorithm when it takes
    a combination of metrics link loss, link delay, link bdw as link cost
    '''

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {"simple_awareness": simple_awareness.simple_Awareness,
                 "simple_delay": simple_delay.simple_Delay,
                 "simple_monitor": simple_monitor.simple_Monitor}

    def __init__(self, *args, **kwargs):
        super(baseline_Dijsktra, self).__init__(*args, **kwargs)
        self.awareness = kwargs["simple_awareness"]
        self.delay = kwargs["simple_delay"]
        self.monitor = kwargs["simple_monitor"]
        self.datapaths = {}
        self.paths = {}
        self.monitor_thread = hub.spawn(self.installation_module)

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def state_change_handler(self, ev): 
        """
            Record datapath information.
        """
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug('Datapath registered: %016x', datapath.id)
                print 'Datapath registered:', datapath.id ##
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('Datapath unregistered: %016x', datapath.id)
                print 'Datapath unregistered:', datapath.id
                print "FUCK"
                del self.datapaths[datapath.id]
        
    def installation_module(self):
        """
            Main entry method of monitoring traffic.
        """
        while True:
            if self.awareness.link_to_port:
                self.paths = None
                self.flow_install_monitor()    
            hub.sleep(setting.MONITOR_PERIOD)
            
    def flow_install_monitor(self): 
        print("[Flow Installation Ok]")
        out_time = time.time()
        for dp in self.datapaths.values():   
            for dp2 in self.datapaths.values():
                if dp.id != dp2.id:
                    ip_src = '10.0.0.'+str(dp.id) 
                    ip_dst = '10.0.0.'+str(dp2.id)
                    self.forwarding(dp.id, ip_src, ip_dst, dp.id, dp2.id)
                    time.sleep(0.0005)
        end_out_time = time.time()
        out_total_ = end_out_time - out_time
        return

    def forwarding(self, dpid, ip_src, ip_dst, src_sw, dst_sw):
        """
            Get paths and install them into datapaths.
        """
        path = self.get_path(str(src_sw), str(dst_sw)) #changed to str cuz the json convertion
        flow_info = (ip_src, ip_dst)
        self.install_flow(self.datapaths, self.awareness.link_to_port, path, flow_info)


    def install_flow(self, datapaths, link_to_port, path,
                     flow_info, data=None):
        init_time_install = time.time()
        ''' 
            Install flow entires.
            path=[dpid1, dpid2...]
            flow_info=(src_ip, dst_ip)
        '''
        if path is None or len(path) == 0:
            self.logger.info("Path error!")
            return
        
        in_port = 1
        first_dp = datapaths[path[0]]

        out_port = first_dp.ofproto.OFPP_LOCAL
        back_info = (flow_info[1], flow_info[0])

        # Flow installing por middle datapaths in path
        if len(path) > 2:
            for i in range(1, len(path)-1):
                port = self.get_port_pair_from_link(link_to_port,
                                                    path[i-1], path[i])
                port_next = self.get_port_pair_from_link(link_to_port,
                                                         path[i], path[i+1])
                if port and port_next:
                    src_port, dst_port = port[1], port_next[0]
                    datapath = datapaths[path[i]]
                    self.send_flow_mod(datapath, flow_info, src_port, dst_port)
                    self.send_flow_mod(datapath, back_info, dst_port, src_port)
        if len(path) > 1:
            # The last flow entry
            port_pair = self.get_port_pair_from_link(link_to_port,
                                                     path[-2], path[-1])
            if port_pair is None:
                self.logger.info("Port is not found")
                return
            src_port = port_pair[1]
            dst_port = 1 #I know that is the host port --
            last_dp = datapaths[path[-1]]
            self.send_flow_mod(last_dp, flow_info, src_port, dst_port)
            self.send_flow_mod(last_dp, back_info, dst_port, src_port)

            # The first flow entry
            port_pair = self.get_port_pair_from_link(link_to_port, path[0], path[1])
            if port_pair is None:
                self.logger.info("Port not found in first hop.")
                return
            out_port = port_pair[0]
            self.send_flow_mod(first_dp, flow_info, in_port, out_port)
            self.send_flow_mod(first_dp, back_info, out_port, in_port)

        # src and dst on the same datapath
        else:
            out_port = 1
            self.send_flow_mod(first_dp, flow_info, in_port, out_port)
            self.send_flow_mod(first_dp, back_info, out_port, in_port)

        end_time_install = time.time()
        total_install = end_time_install - init_time_install

    def send_flow_mod(self, datapath, flow_info, src_port, dst_port):
        """
            Build flow entry, and send it to datapath.
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        actions = []
        actions.append(parser.OFPActionOutput(dst_port))

        match = parser.OFPMatch(
             eth_type=ETH_TYPE_IP, ipv4_src=flow_info[0], 
             ipv4_dst=flow_info[1])

        self.add_flow(datapath, 1, match, actions,
                      idle_timeout=250, hard_timeout=0)
        

    def add_flow(self, dp, priority, match, actions, idle_timeout=0, hard_timeout=0):
        """
            Send a flow entry to datapath.
        """
        ofproto = dp.ofproto
        parser = dp.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=dp, command=dp.ofproto.OFPFC_ADD, priority=priority,
                                idle_timeout=idle_timeout, 
                                hard_timeout=hard_timeout,
                                match=match, instructions=inst)
        dp.send_msg(mod)

    def build_packet_out(self, datapath, buffer_id, src_port, dst_port, data):
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

    def arp_forwarding(self, msg, src_ip, dst_ip):
        """
            Send ARP packet to the destination host if the dst host record
            is existed.
            result = (datapath, port) of host
        """
        datapath = msg.datapath
        ofproto = datapath.ofproto

        result = self.awareness.get_host_location(dst_ip)
        if result:
            # Host has been recorded in access table.
            datapath_dst, out_port = result[0], result[1]
            datapath = self.datapaths[datapath_dst]
            out = self.build_packet_out(datapath, ofproto.OFP_NO_BUFFER,
                                         ofproto.OFPP_CONTROLLER,
                                         out_port, msg.data)
            datapath.send_msg(out)
            self.logger.debug("Deliver ARP packet to knew host")
        else:
            
            pass

    def get_path(self, src, dst):
            if self.paths != None:
                #print ('PATHS: OK')
                path = self.paths.get(src).get(dst)#[0]
                # print('get_path return:', path)
                return path
            else:
                #print('Getting paths: OK')
                paths = self.get_dijkstra_paths_()
                path = paths.get(src).get(dst)#[0]
                return path

    def get_dijkstra_paths_(self):
        # file = '/home/controlador/ryu/ryu/app/SDNapps_proac/RoutingGeant/DRL/dRSIR/32nodos/fffpaths_weight.json'
        file = '/home/controlador/ryu/ryu/app/OSPF_all/Proac/paths_all.json'
        try:
            with open(file,'r') as json_file:
                paths_dict = json.load(json_file)
                paths_dict = ast.literal_eval(json.dumps(paths_dict))
                self.paths = paths_dict
                return self.paths
        # except ValueError as e: #error excpetsion when trying to read the json and is still been updated
        #     return
        except:
            time.sleep(0.35)
            with open(file,'r') as json_file: #try again
                paths_dict = json.load(json_file)
                paths_dict = ast.literal_eval(json.dumps(paths_dict))
                self.paths = paths_dict
                return self.paths
        
        # try:
        #     with open(file,'r') as json_file:
        #         paths_dict = json.load(json_file)
        #         paths_dict = ast.literal_eval(json.dumps(paths_dict))
        #         self.paths = paths_dict
        #         return self.paths
        # except ValueError as e: #error excpetion when trying to read the json and is still been updated
        #     return
        # else:
        #     with open(file,'r') as json_file: #try again
        #         paths_dict = json.load(json_file)
        #         paths_dict = ast.literal_eval(json.dumps(paths_dict))
        #         self.paths = paths_dict
        #         return self.paths

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

                    
    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def port_status_handler(self, ev):
        """
            Handle the port status changed event.
        """
        msg = ev.msg
        ofproto = msg.datapath.ofproto
        reason = msg.reason
        dpid = msg.datapath.id
        port_no = msg.desc.port_no

        reason_dict = {ofproto.OFPPR_ADD: "added",
                       ofproto.OFPPR_DELETE: "deleted",
                       ofproto.OFPPR_MODIFY: "modified", }

        if reason in reason_dict:
            print "switch%d: port %s %s" % (dpid, reason_dict[reason], port_no)
        else:
            print "switch%d: Illegal port state %s %s" % (dpid, port_no, reason)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        '''
            In packet_in handler, we need to learn access_table by ARP and IP packets.
            Therefore, the first packet from UNKOWN host MUST be ARP
        '''
        msg = ev.msg
        pkt = packet.Packet(msg.data)
        arp_pkt = pkt.get_protocol(arp.arp)
        if isinstance(arp_pkt, arp.arp):
            self.arp_forwarding(msg, arp_pkt.src_ip, arp_pkt.dst_ip)
