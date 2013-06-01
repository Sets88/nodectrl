# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, reconstructor
from settings import settings
import socket
import struct
import os
from xml.dom import minidom
from flask import abort

Base = declarative_base()
Session = sessionmaker()


class NodesAPI(object):

    """Main programm API"""
    def __init__(self, settings):
        try:
            if settings['engine'] == "mysql":
                self.db_engine = create_engine(
                    "mysql://%s:%s@%s/%s?init_command=set names utf8" % (settings['user'], settings['password'], settings['host'], settings['db'])
                    , echo=True, convert_unicode=True)
            elif settings['engine'] == "sqlite":
                self.db_engine = create_engine("sqlite:///%s" % settings['db'])
        except:
            abort(404)
        Session.configure(bind=self.db_engine)
        self.session = Session()
        Base.metadata.create_all(self.db_engine)

    def get_by_id(self, id):
        return self.session.query(Node).filter_by(id=id).first()

    def get_by_parent(self, id):
        return self.session.query(Node).filter_by(parent_id=id).all()

    def delete_node(self, id):
        return self.session.query(Node).filter_by(id=id).delete()
        
    def save_all(self):
        self.session.commit()
        self.close_session()

    def close_session(self):
        self.session.close()

    def add_node(self, node):
        if not isinstance(node, Node):
            raise NodeException("Node instance expected.")
        self.session.add(node)
        self.session.flush()

    def move_node(self, id, parent_id):
        """Change node's parent"""

        node = self.session.query(Node).filter_by(id=id).first()
        parent = self.session.query(Node).filter_by(id=parent_id).first()
        if node is not None:
            if parent_id is None or parent_id=="0":
                node.parent_id = 0
            elif parent is not None and id != parent_id:
                node.parent_id = parent_id
            elif parent is None:
                raise NodeException("No such parent.")
            else:
                raise NodeException("Id and parent are the same item.")

    def reset_flags(self, catid, id=None):
        """Flush flags or flag which indicates that node were off"""
        if id is None:
            nodes = self.session.query(Node).filter(Node.catid.in_(catid)).all()
            for node in nodes:
                node.flag = 0
        else:
            node = self.session.query(Node).filter(Node.id==id).first()
            if node is not None:
                node.flag = 0
            else:
                raise NodeException("No such node.")
        self.save_all()
        return node

    def list_nodes(self, catid):
        if isinstance(catid, list):
            nodes = self.session.query(Node).filter(Node.catid.in_(catid)).order_by("port").all()
        self.nodelist = NodeList(nodes)
        return self.nodelist[0].child_list

    def nmap_nets(self, nets):
        pipe = os.popen("nmap -n %s -sP -oX -" % " ".join(nets))
        out = pipe.read()
        ecode = pipe.close()
        if ecode:
            return False
        xml = minidom.parseString(out)
        hosts = xml.getElementsByTagName("host")
        ips = []
        for host in hosts:
            address = host.getElementsByTagName("address")[0].getAttribute("addr")
            status = host.getElementsByTagName("status")[0].getAttribute("state")
            if status == "up":
                ips.append(address)
        return ips

    def scan_nodes(self, catid):

        nets = []
        for cat in catid:
            net = settings['categories'][int(cat)][1]
            nets.extend(net)
        return self.nmap_nets(nets)

    def check_nodes(self, catid):
        nodes = self.session.query(Node).filter(Node.catid.in_(catid)).filter(Node.ip > 0).all()
        alive = self.scan_nodes(catid)
        for node in nodes:
            if node.ipaddr in alive:
                node.status = 1
            else:
                node.status = 0
        self.save_all()

    def autoadd_nodes(self, catid):
        nodes = self.session.query(Node).filter(Node.catid.in_(catid)).filter(Node.ip > 0).all()
        alive = self.scan_nodes(catid)
        ips = []
        for node in nodes:
            ips.append(node.ipaddr)
        for ip in alive:
            if ip not in ips:
                sw = Node()
                sw.comment = "???"
                sw.status = 1
                sw.set_ip(ip)
                self.add_node(sw)
        self.save_all()
    def automove_nodes(self, catid):
        #oid =  ".1.3.6.1.2.1.17.7.1.2.2.1.2.%s.%s" % (vlan, mac)
        #netsnmp.snmpget(".1.3.6.1.2.1.17.7.1.2.2.1.2.1.188.246.133.61.155.111", DestHost="10.91.90.53", Version=1, Community="public")
        pass

    def setup(self):
        pass


class Node(Base):

    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('nodes.id'))
    name = Column(String(250))
    comment = Column(String(250))
    ip = Column(Integer, default=0)
    status = Column(Integer, default=0)
    datetime = Column(DateTime)
    flag = Column(Integer, default=0)
    catid = Column(Integer, default=0)
    port = Column(Integer, default=0)

    def __init__(self):
        self.child_list = []

    @reconstructor
    def init_on_load(self):
        self.child_list = []
        self.ipaddr = socket.inet_ntoa(struct.pack("!I", self.ip))

    def set_ip(self, ipaddr):
        try:
            ip = struct.unpack("!I",socket.inet_aton(ipaddr))[0]
            self.ip = ip
            self.ipaddr = ipaddr
        except:
            return False
        else:
            return True

    def __repr__(self):
        if self.comment:
            return self.comment.encode("utf-8")
        else:
            return ""


class NodeList(object):

    def __init__(self, nodes=None):
        if nodes is None:
            nodes = []
        root = Node()
        self.nodes = {0: root}
        for node in nodes:
            self.nodes[node.id] = node
        for node in nodes:
            if node.parent_id in self.nodes and node.parent_id > 0:
                self.nodes[node.parent_id].child_list.append(node)
            else:
                self.nodes[0].child_list.append(node)
    def __getitem__(self, key):
        return self.nodes[key]

    def __iter__(self):
        return iter(self.nodes.values())

class NodeException(Exception):
    pass