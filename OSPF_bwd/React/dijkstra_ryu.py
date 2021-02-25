from ryu.base import app_manager
from ryu.controller import mac_to_port
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib import mac
from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase
from ryu.topology import event, switches
from collections import defaultdict


 #mymac[srcmac]->(switch, port)


 #adjacency map [sw1][sw2]->port from sw1 to sw2




class ProjectController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    def __init__(self, *args, **kwargs):
        super(ProjectController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.topology_api_app = self
        self.datapath_list= []
        self.adjacency=defaultdict(lambda:defaultdict(lambda:None))
        self.mymac= {}
        self.switches= []

    # Handy function that lists all attributes in the given object

    def ls(self,obj):
        print("\n".join([x for x in dir(obj) if x[0] != "_"]))
    
    def minimum_distance(self,distance, Q):
        min = float('Inf')
        node = 0
        for v in Q:
            if distance[v] < min:
                min = distance[v]
                node = v
        return node

    def get_path (self,src,dst,first_port,final_port):
        #Dijkstra's algorithm
        print "get_path is called, src=",src," dst=",dst, " first_port=", first_port, " final_port=", final_port
        distance = {}
        previous = {}
        for dpid in self.switches:
            distance[dpid] = float('Inf')
            previous[dpid] = None
        distance[src]= 0

        Q=set(self.switches)
        print "Q=", Q
        while len(Q)>0:
            u = self.minimum_distance(distance, Q)
            Q.remove(u) 

            for p in self.switches:
                if self.adjacency[u][p]!=None:
                    w = 1
                    if distance[u] + w < distance[p]:
                        distance[p] = distance[u] + w
                        previous[p] = u
        r=[]
        p=dst
        r.append(p)
        q=previous[p]
        while q is not None:
            if q == src:
                r.append(q)
                break
            p=q
            r.append(p)
            q=previous[p]

        r.reverse()
        if src==dst:
            path=[src]
        else:
            path=r

        # Now add the ports
        r = []
        in_port = first_port
        for s1,s2 in zip(path[:-1],path[1:]):
            out_port = self.adjacency[s1][s2]
            r.append((s1,in_port,out_port))
            in_port = self.adjacency[s2][s1]
        r.append((dst,in_port,final_port))

        return r

    def install_path(self, p, ev, src_mac, dst_mac):
        print "install_path is called"
        #print "p=", p, " src_mac=", src_mac, " dst_mac=", dst_mac
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        for sw, in_port, out_port in p:
         #print src_mac,"->", dst_mac, "via ", sw, " in_port=", in_port, " out_port=", out_port
            match=parser.OFPMatch(in_port=in_port, eth_src=src_mac, eth_dst=dst_mac)
            actions=[parser.OFPActionOutput(out_port)]
            datapath=self.datapath_list[int(sw)-1]
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS , actions)]
            mod = datapath.ofproto_parser.OFPFlowMod(datapath=datapath, match=match, idle_timeout=10, priority=1, instructions=inst)
            datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures , CONFIG_DISPATCHER)
    def switch_features_handler(self , ev):
        print "switch_features_handler is called"
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS ,actions)]
        mod = datapath.ofproto_parser.OFPFlowMod(datapath=datapath, match=match, cookie=0,instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        #print "eth.ethertype=", eth.ethertype
        #avodi broadcast from LLDP
        if eth.ethertype==35020:
          return

        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        mymac={}
        if src not in mymac.keys():
            mymac[src]=(dpid, in_port)
        print mymac

        if dst in mymac.keys():
            p = self.get_path(mymac[src][0], mymac[dst][0], mymac[src][1], mymac[dst][1])
            print 'p', p
            self.install_path(p, ev, src, dst)
            out_port = p[0][2]
        else:
            out_port = ofproto.OFPP_FLOOD
        actions = [parser.OFPActionOutput(out_port)]

        # # install a flow to avoid packet_in next time
        # if out_port != ofproto.OFPP_FLOOD:
        #     match = parser.OFPMatch(in_port=in_port, eth_src=src, eth_dst=dst)
       
        data=None
        if msg.buffer_id==ofproto.OFP_NO_BUFFER:
           data=msg.data
        
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port,actions=actions, data=data)
        datapath.send_msg(out)

    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        switch_list = get_switch(self.topology_api_app, None)  
        self.switches=[switch.dp.id for switch in switch_list]
        self.datapath_list=[switch.dp for switch in switch_list]
        #print "self.datapath_list=", self.datapath_list
        # print "switches=", self.switches

        links_list = get_link(self.topology_api_app, None)
        mylinks=[(link.src.dpid,link.dst.dpid,link.src.port_no,link.dst.port_no) for link in links_list]
        # for dp in self.switches:
        #     self.adjacency.setdefault(dp, {})
        for s1,s2,port1,port2 in mylinks:
            self.adjacency[s1][s2]=port1
            self.adjacency[s2][s1]=port2
        print self.adjacency
        print
        # print self.switches

          