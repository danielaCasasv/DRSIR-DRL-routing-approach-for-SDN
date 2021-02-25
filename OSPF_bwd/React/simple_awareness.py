import networkx as nx
#import matplotlib.pyplot as plt
import time

from ryu import cfg
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp
from ryu.lib import hub
from ryu.topology import event
from ryu.topology.api import get_switch, get_link

import setting
import time


CONF = cfg.CONF


class simple_Awareness(app_manager.RyuApp):
    """
        NetworkAwareness is a Ryu app for discovering topology information.
        This App can provide many data services for other App, such as
        link_to_port, access_table, switch_port_table, access_ports,
        interior_ports, topology graph and shortest paths.
    """
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    # List the event list should be listened.
    events = [event.EventSwitchEnter,
              event.EventSwitchLeave, event.EventPortAdd,
              event.EventPortDelete, event.EventPortModify,
              event.EventLinkAdd, event.EventLinkDelete]

    def __init__(self, *args, **kwargs):
        super(simple_Awareness, self).__init__(*args, **kwargs)
        self.topology_api_app = self
        self.name = "awareness"
        self.link_to_port = {}                # {(src_dpid,dst_dpid):(src_port,dst_port),}
        self.access_table = {}                # {(sw,port):(ip, mac),}
        self.switch_port_table = {}           # {dpid:set(port_num,),}
        self.access_ports = {}                # {dpid:set(port_num,),}
        self.interior_ports = {}              # {dpid:set(port_num,),}
        self.switches = []                    # self.switches = [dpid,]
        self.shortest_paths = {}              # {dpid:{dpid:[[path],],},}
        self.pre_link_to_port = {}
        self.pre_access_table = {}

        self.graph = nx.DiGraph()
        # Get initiation delay.
        self.initiation_delay = self.get_initiation_delay(CONF.fanout)
        self.start_time = time.time()

        # Start a green thread to discover network resource.
        self.discover_thread = hub.spawn(self._discover)

    def _discover(self):
        i = 0
        while True:
            self.show_topology()
            if i == 1:   # Reload topology every 20 seconds.
                self.get_topology(None)
                i = 0
            hub.sleep(setting.DISCOVERY_PERIOD)
            i = i + 1

    def add_flow(self, dp, priority, match, actions, idle_timeout=0, hard_timeout=0):
        ofproto = dp.ofproto
        parser = dp.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath=dp, priority=priority,
                                idle_timeout=idle_timeout,
                                hard_timeout=hard_timeout,
                                match=match, instructions=inst)
        dp.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """
            Install table-miss flow entry to datapaths.
        """
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        self.logger.info("switch:%s connected", datapath.id)


        # Install table-miss flow entry.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        """
            Handle the packet_in packet, and register the access info.
        """
        msg = ev.msg
        datapath = msg.datapath
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        eth_type = pkt.get_protocols(ethernet.ethernet)[0].ethertype #delay
        arp_pkt = pkt.get_protocol(arp.arp)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)

        if arp_pkt:
            arp_src_ip = arp_pkt.src_ip
            arp_dst_ip = arp_pkt.dst_ip #delay
            mac = arp_pkt.src_mac
            # Record the access infomation.
            self.register_access_info(datapath.id, in_port, arp_src_ip, mac)
        elif ip_pkt:
            ip_src_ip = ip_pkt.src
            eth = pkt.get_protocols(ethernet.ethernet)[0]
            mac = eth.src
            # Record the access infomation.
            self.register_access_info(datapath.id, in_port, ip_src_ip, mac)
        else:
            pass

    @set_ev_cls(events)
    def get_topology(self, ev):
        """
            Get topology info and calculate shortest paths.
            Note: In looped network, we should get the topology
            20 or 30 seconds after the network went up.
        """
        present_time = time.time()
        if present_time - self.start_time < self.initiation_delay: #Set to 30s
            return

        self.logger.info("[GET NETWORK TOPOLOGY]")
        switch_list = get_switch(self.topology_api_app, None)
        self.create_port_map(switch_list)
        time.sleep(0.5)
        self.switches = [sw.dp.id for sw in switch_list]
        links = get_link(self.topology_api_app, None)
        self.create_interior_links(links)
        self.create_access_ports()
        self.graph = self.get_graph(self.link_to_port.keys())
        # self.shortest_paths = self.all_k_shortest_paths(
        #     self.graph, weight='weight', k=CONF.k_paths)

    def get_host_location(self, host_ip):
        """
            Get host location info ((datapath, port)) according to the host ip.
            self.access_table = {(sw,port):(ip, mac),}
        """
        # print('Access table: \n{0}'.format(self.access_table))
        init_time_host = time.time()
        for key in self.access_table.keys():
            if self.access_table[key][0] == host_ip:
                end_time_host = time.time()
                total_host = end_time_host - init_time_host
                # print("Time function host IP {0}: {1}s".format(host_ip, total_host))
                return key
        self.logger.info("%s location is not found." % host_ip)

        return None

    def get_host_location_arp(self, host_ip):
        """
            Get host location info ((datapath, port)) according to the host ip.
            self.access_table = {(sw,port):(ip, mac),}
        """
        # print('Access table: \n{0}'.format(self.access_table))
        init_time_host = time.time()
        for key in self.access_table.keys():
            if self.access_table[key][0] == host_ip:
                end_time_host = time.time()
                total_host = end_time_host - init_time_host
                # print("Time function host_ARP: ", total_host)
                return key
        self.logger.info("%s location is not found." % host_ip)

        return None

    def get_graph(self, link_list):
        """
            Get Adjacency matrix from link_to_port.
        """
        _graph = self.graph.copy()
        for src in self.switches:
            for dst in self.switches:
                if src == dst:
                    _graph.add_edge(src, dst, weight=0)
                elif (src, dst) in link_list:
                    _graph.add_edge(src, dst, weight=1)
                else:
                    pass
        return _graph

    def get_initiation_delay(self, fanout):
        """
            Get initiation delay.
        """
        if fanout == 4:
            delay = 10
        elif fanout == 8:
            delay = 20
        else:
            delay = 20
        return delay

    def create_port_map(self, switch_list):
        """
            Create interior_port table and access_port table.
        """
        for sw in switch_list:
            dpid = sw.dp.id
            self.switch_port_table.setdefault(dpid, set())
            # switch_port_table is equal to interior_ports plus access_ports.
            self.interior_ports.setdefault(dpid, set())
            self.access_ports.setdefault(dpid, set())
            for port in sw.ports:
                # switch_port_table = {dpid:set(port_num,),}
                self.switch_port_table[dpid].add(port.port_no)

    def create_interior_links(self, link_list):
        """
            Get links' srouce port to dst port  from link_list.
            link_to_port = {(src_dpid,dst_dpid):(src_port,dst_port),}
        """
        for link in link_list:
            src = link.src
            dst = link.dst
            self.link_to_port[(src.dpid, dst.dpid)] = (src.port_no, dst.port_no)
            # Find the access ports and interior ports.
            if link.src.dpid in self.switches:
                self.interior_ports[link.src.dpid].add(link.src.port_no)
            if link.dst.dpid in self.switches:
                self.interior_ports[link.dst.dpid].add(link.dst.port_no)

    def create_access_ports(self):
        """
            Get ports without link into access_ports.
        """
        for sw in self.switch_port_table:
            all_port_table = self.switch_port_table[sw]
            interior_port = self.interior_ports[sw]
            # That comes the access port of the switch.
            self.access_ports[sw] = all_port_table - interior_port

    # def k_shortest_paths(self, graph, src, dst, weight='weight', k=5):
    #     """
    #         Creat K shortest paths from src to dst.
    #         generator produces lists of simple paths, in order from shortest to longest.
    #     """
    #     generator = nx.shortest_simple_paths(graph, source=src, target=dst, weight=weight)
    #     shortest_paths = []
    #     try:
    #         for path in generator:
    #             if k <= 0:
    #                 break
    #             shortest_paths.append(path)
    #             k -= 1
    #         return shortest_paths
    #     except:
    #         self.logger.debug("No path between %s and %s" % (src, dst))

    # def all_k_shortest_paths(self, graph, weight='weight', k=5):
    #     """
    #         Creat all K shortest paths between datapaths.
    #         Note: We get shortest paths for bandwidth-sensitive
    #         traffic from bandwidth-sensitive switches.
    #     """
    #     _graph = graph.copy()
    #     paths = {}
    #     # Find k shortest paths in graph.
    #     for src in _graph.nodes():
    #         paths.setdefault(src, {src: [[src] for i in xrange(k)]})
    #         for dst in _graph.nodes():
    #             if src == dst:
    #                 continue
    #             paths[src].setdefault(dst, [])
    #             paths[src][dst] = self.k_shortest_paths(_graph, src, dst, weight=weight, k=k)
    #     return paths

    def register_access_info(self, dpid, in_port, ip, mac):
        """
            Register access host info into access table.
        """
        if in_port in self.access_ports[dpid]:
            if (dpid, in_port) in self.access_table:
                if self.access_table[(dpid, in_port)] == (ip, mac):
                    return
                else:
                    self.access_table[(dpid, in_port)] = (ip, mac)
                    return
            else:
                self.access_table.setdefault((dpid, in_port), None)
                self.access_table[(dpid, in_port)] = (ip, mac)
                return

    def show_topology(self):
        # print self.link_to_port
        if self.pre_link_to_port != self.link_to_port:# and setting.TOSHOW:
            # It means the link_to_port table has changed.
            _graph = self.graph.copy()
            print "\n---------------------Link Port---------------------"
            print '%6s' % ('switch'),
            for node in sorted([node for node in _graph.nodes()], key=lambda node: node):
                print '%6d' % node,
            print
            for node1 in sorted([node for node in _graph.nodes()], key=lambda node: node):
                print '%6d' % node1,
                for node2 in sorted([node for node in _graph.nodes()], key=lambda node: node):
                    if (node1, node2) in self.link_to_port.keys():
                        print '%6s' % str(self.link_to_port[(node1, node2)]),
                    else:
                        print '%6s' % '/',
                print
            print
            self.pre_link_to_port = self.link_to_port.copy()

        if self.pre_access_table != self.access_table:# and setting.TOSHOW:
            # It means the access_table has changed.
            print "\n----------------Access Host-------------------"
            print '%10s' % 'switch', '%10s' % 'port', '%22s' % 'Host'
            if not self.access_table.keys():
                print "    NO found host"
            else:
                for sw in sorted(self.access_table.keys()):
                    print '%10d' % sw[0], '%10d      ' % sw[1], self.access_table[sw]
            print
            self.pre_access_table = self.access_table.copy()