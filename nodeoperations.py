#-*- coding: utf-8 -*-
import os
from xml.dom import minidom
import ipaddr
import netsnmp
#from node import Node

class NodeOperations(object):
    def __init__(self, nets):
        self.nets = nets

    def get_mac_by_ip(self, ip):
        with open("/proc/net/arp", "r") as f:
            for line in f.readlines():
                if line.startswith(ip + " "):
                    return " ".join(line.split()).split()[3]
        return None

    def get_ip_by_mac(self, mac):
        with open("/proc/net/arp", "r") as f:
            for line in f.readlines():
                if mac.lower() in line.lower():
                    return " ".join(line.split()).split()[0]
        return None

    def get_vlan_by_ip(self, ip):
        if not ip:
            return None
        ip = ipaddr.IPAddress(ip)
        for net in self.nets:
            if net[0].Contains(ip):
                return net[1]


    def hex2dec(self, s):
        return str(int(s, 16))

    def mac2dec(self, mac):
        if mac:
            return ".".join(map(self.hex2dec, mac.split(":")))
        return None

    def nmap_nets(self):
        nets = []
        for net in self.nets:
            nets.append(str(net[0]))
        pipe = os.popen("nmap -n --max-parallelism 500 --min-rtt-timeout=200ms -sP -oX - %s" % " ".join(nets))
        print "nmap -n --max-parallelism 500 --min-rtt-timeout=200ms -sP -oX - %s" % " ".join(nets)
        out = pipe.read()
        ecode = pipe.close()
        if ecode:
            return None
        xml = minidom.parseString(out)
        hosts = xml.getElementsByTagName("host")
        ips = []
        for host in hosts:
            address = host.getElementsByTagName("address")[0].getAttribute("addr")
            status = host.getElementsByTagName("status")[0].getAttribute("state")
            if status == "up":
                ips.append(address)
        return ips

    def nmap_ip_list(self, ip_list):
        pipe = os.popen("nmap -n --max-parallelism 500 --min-rtt-timeout=200ms -sP -oX - %s" % " ".join(ip_list))
        out = pipe.read()
        ecode = pipe.close()
        if ecode:
            return None
        xml = minidom.parseString(out)
        hosts = xml.getElementsByTagName("host")
        ips = []
        for host in hosts:
            address = host.getElementsByTagName("address")[0].getAttribute("addr")
            status = host.getElementsByTagName("status")[0].getAttribute("state")
            if status == "up":
                ips.append(address)
        return ips

    def snmp_node(self, ipaddr, mac, vlan="1", oid="1.3.6.1.2.1.17.7.1.2.2.1.2"):
        oid =  ".%s.%s.%s" % (oid, vlan, self.mac2dec(mac))
        res = netsnmp.snmpget(oid, DestHost=ipaddr, Version=1, Community="public")
        return res

    def _find_port(self, childs, mac, vlan, ipaddr=None, port=0):

        if mac is None:
            return None

        if vlan is None:
            vlan = 1

        for node in childs:
            if port == 0 or (int(port)>0 and int(node.port) == int(port)):
                if (node.ip) and node.comment.startswith("(v)"):
                    res = self.snmp_node(node.ipaddr, mac, vlan)
                    if res[0] and int(res[0])>0:
                        recres=self._find_port(node.child_list, mac, vlan, ipaddr=ipaddr, port=res[0])
                        if recres and int(recres[1])>0:
                            return recres
                        else:
                            return (node, res[0])
        return None


    def get_port_by_ip(self, childs, ip):
        mac = self.get_mac_by_ip(ip)
        vlan = self.get_vlan_by_ip(ip)
        return self._find_port(childs, mac, vlan, ipaddr=ip)

    def get_port_by_mac(self, childs, mac):
        ip = self.get_ip_by_mac(mac)
        vlan = self.get_vlan_by_ip(ip)
        return self._find_port(childs, mac, vlan)
