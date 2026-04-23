from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, tcp, udp, icmp
import datetime
import csv
import os

LOG_FILE = os.path.expanduser('~/sdn-packet-logger/packet_log.csv')

class PacketLogger(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(PacketLogger, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.blocked_pairs = [('10.0.0.2', '10.0.0.4')]  # h2 <-> h4 blocked
        self.packet_count = 0

        # Create CSV log file with headers
        with open(LOG_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['#', 'Timestamp', 'Datapath', 'In-Port',
                             'Src-MAC', 'Dst-MAC', 'Src-IP', 'Dst-IP',
                             'Protocol', 'Action'])
        self.logger.info("=== Packet Logger Started ===")
        self.logger.info("Log file: %s", LOG_FILE)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Default rule: send all unmatched packets to controller
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        self.logger.info("Switch %s connected.", datapath.id)

    def add_flow(self, datapath, priority, match, actions, idle=0, hard=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                idle_timeout=idle, hard_timeout=hard,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    def is_blocked(self, src_ip, dst_ip):
        return (src_ip, dst_ip) in self.blocked_pairs or \
               (dst_ip, src_ip) in self.blocked_pairs

    def log_packet(self, dp_id, in_port, src_mac, dst_mac, src_ip, dst_ip, proto, action):
        self.packet_count += 1
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        self.logger.info("[%d] %s | dp=%s port=%s | %s->%s | %s->%s | proto=%s | %s",
                         self.packet_count, timestamp, dp_id, in_port,
                         src_mac, dst_mac, src_ip, dst_ip, proto, action)
        with open(LOG_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([self.packet_count, timestamp, dp_id, in_port,
                             src_mac, dst_mac, src_ip, dst_ip, proto, action])

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        if eth is None:
            return

        dst_mac = eth.dst
        src_mac = eth.src
        dpid = datapath.id

        # Learn MAC address
        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src_mac] = in_port

        # Extract IP info if available
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        src_ip = ip_pkt.src if ip_pkt else 'N/A'
        dst_ip = ip_pkt.dst if ip_pkt else 'N/A'

        # Detect protocol
        if pkt.get_protocol(tcp.tcp):
            proto = 'TCP'
        elif pkt.get_protocol(udp.udp):
            proto = 'UDP'
        elif pkt.get_protocol(icmp.icmp):
            proto = 'ICMP'
        else:
            proto = 'OTHER'

        # Check if this pair is blocked
        if ip_pkt and self.is_blocked(src_ip, dst_ip):
            self.log_packet(dpid, in_port, src_mac, dst_mac, src_ip, dst_ip, proto, 'BLOCKED')
            return  # Drop packet, install no flow rule

        # Determine output port
        if dst_mac in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst_mac]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # Install flow rule for known destinations
        if out_port != ofproto.OFPP_FLOOD and ip_pkt:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst_mac,
                                    eth_src=src_mac)
            self.add_flow(datapath, 1, match, actions, idle=10, hard=30)

        # Log and forward
        self.log_packet(dpid, in_port, src_mac, dst_mac, src_ip, dst_ip, proto, 'FORWARDED')

        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=msg.buffer_id,
                                  in_port=in_port,
                                  actions=actions,
                                  data=msg.data)
        datapath.send_msg(out)
