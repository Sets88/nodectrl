# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, reconstructor
from settings import Settings
import socket
import struct
from nodeoperations import NodeOperations
from sqlalchemy.exc import OperationalError

Base = declarative_base()
Session = sessionmaker()

# All permissions and default values
permissions = {"nodes_add_nodes": [],
               "nodes_delete_nodes": [],
               "nodes_move_nodes": [],
               "nodes_reset_flags": [],
               "nodes_edit_nodes": [],
               "nodes_check_nodes": ["all"],
               "nodes_autoadd_nodes": [],
               "nodes_automove_nodes": [],
               "nodes_show_ips": []
               }

class NodesAPI(object):

    """Main programm API"""
    def __init__(self):
        self.db_engine = None
        self.session = None
        self.db_connect()

    def _ip_to_int(self, ipaddr):
        try:
            ip = struct.unpack("!I", socket.inet_aton(ipaddr))[0]
        except:
            return None
        return ip            

    def db_connect(self):
        if Settings()['db']['engine'] == "mysql":
            self.db_engine = create_engine(
                "mysql://%s:%s@%s:%s/%s?init_command=set names utf8" % (Settings()['db'][
                                                                        'user'], Settings()['db']['password'], Settings()['db']['host'], Settings()['db']['port'], Settings()['db']['db']), echo=True, convert_unicode=True, pool_recycle=7200)
        elif Settings()['db']['engine'] == "sqlite":
            self.db_engine = create_engine("sqlite:///%s" % Settings()['db']['db'], echo=True)

        Session.configure(bind=self.db_engine)
        self.session = Session()
        try:
            Base.metadata.create_all(self.db_engine)
        except OperationalError:
            raise NodeException("Can't connect to database")

    def get_by_id(self, id):
        return self.session.query(Node).filter_by(id=id).first()

    def get_by_parent(self, id):
        return self.session.query(Node).filter_by(parent_id=id).all()

    def get_by_ip(self, ipaddr):
        ip = self._ip_to_int(ipaddr)
        if ip is not None:
            return self.session.query(Node).filter_by(ip=ip).first()

    def delete_node(self, id):
        return self.session.query(Node).filter_by(id=id).delete()

    def save_all(self):
        try:
            self.session.flush()
            self.session.expunge_all()
            self.session.commit()
        except:
            self.session.rollback()

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
            if parent_id is None or parent_id == "0":
                node.parent_id = None
            elif parent is not None and id != parent_id:
                node.parent_id = parent_id
            elif parent is None:
                raise NodeException("No such parent.")
            else:
                raise NodeException("Id and parent are the same item.")

    def reset_flags(self, catid, id=None):
        """Flush flags or flag which indicates that node were off"""
        if id is None:
            nodes = self.session.query(Node).filter(
                Node.catid.in_(catid)).all()
            for node in nodes:
                node.flag = 0
        else:
            node = self.session.query(Node).filter(Node.id == id).first()
            if node is not None:
                node.flag = 0
            else:
                raise NodeException("No such node.")
        self.save_all()
        return node

    def list_nodes(self, catid):
        if isinstance(catid, list):
            nodes = self.session.query(Node).filter(Node.catid.in_(
                catid)).order_by("port").order_by("ip").all()
        self.nodelist = NodeList(nodes)
        return self.nodelist[0].child_list

    def scan_nodes(self, catid, node_list=None):
        nodeop = NodeOperations(Settings().get_nets(catid))
        if not node_list:
            return nodeop.nmap_nets()
        else:
            ip_list = []
            for node in node_list:
                ip_list.append(node.ipaddr)
            return nodeop.nmap_ip_list(ip_list)

    def check_nodes(self, catid):
        nodes = self.session.query(Node).filter(
            Node.catid.in_(catid)).filter(Node.ip > 0).all()
        alive = self.scan_nodes(catid)
        for node in nodes:
            if node.ipaddr in alive:
                node.status = 1
            else:
                node.status = 0
        self.save_all()

    def check_tree(self, catid, node_id):
        self.list_nodes(catid)
        if node_id == 0:
            node_list = self.list_tree(self.nodelist[0].child_list)
        else:
            node_list = self.list_tree(self.nodelist[node_id])
        alive = self.scan_nodes(catid, node_list)
        result = {}
        for node in node_list:
            if node.ipaddr in alive:
                node.status = 1
                result[node.id] = 1
            else:
                node.status = 0
                result[node.id] = 0
        self.save_all()
        return result

    def list_tree(self, nodes):
        if not isinstance(nodes, list):
            nodes = [nodes]
        nodelist  = []
        for node in nodes:
            if node.ip > 0:
                nodelist.append(node)
                nodelist.extend(self.list_tree(node.child_list))
        return nodelist

    def autoadd_nodes(self, catid):
        nodes = self.session.query(Node).filter(
            Node.catid.in_(catid)).filter(Node.ip > 0).all()
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
                sw.catid = catid[0]
                self.add_node(sw)
        self.save_all()

    def automove_nodes(self, catid, cats):

        nodes = self.session.query(Node).filter(
            Node.catid.in_(catid)).order_by("port").all()
        self.nodelist = NodeList(nodes)
        nodeop = NodeOperations(Settings().get_nets(catid))
        nodeop.nmap_nets()

        for node in self.nodelist[0].child_list:
            res = nodeop.get_port_by_ip(
                self.nodelist[0].child_list, node.ipaddr)
            if res:
                node.parent_id = res[0].id
                node.port = res[1]
        self.save_all()

    def get_nodename_by_mac(self, catid, mac):
        nodes = self.session.query(Node).filter(
            Node.catid.in_(catid)).order_by("port").all()
        self.nodelist
        self.nodelist = NodeList(nodes)
        nodeop = NodeOperations(Settings().get_nets(catid))
        res = nodeop.get_port_by_mac(self.nodelist[0].child_list, mac)
        if res:
            for node in res[0].child_list:
                if int(node.port) == int(res[1]):
                    return node.comment
            return res[0].comment

    def freeip_list(self, catid):

        def find_freeip(freeips, ipaddr, return_none=False, exists=False):
            """Finds ipaddr in commented ips and returns it, 
            if found, or return new object with empty comment, 
            if return_none set, return None if not found in commented ips"""
            for freeip in freeips:
                if freeip.ipaddr == ipaddr:
                    freeip.exists = exists
                    return freeip
            if return_none:
                return None
            freeip = FreeIP()
            freeip.ipaddr = ipaddr
            freeip.comment = ""
            return freeip

        nodes = self.session.query(Node).filter(Node.catid.in_(
            catid)).filter(Node.ip > 0).order_by("ip").all()
        ips = []
        freeips = []
        for node in nodes:
            ips.append(str(node.ipaddr))

        for net in Settings().get_nets(catid):
            comm_freeips = self.session.query(FreeIP).filter(FreeIP.ip.in_(map(lambda ip:self._ip_to_int(str(ip)),net[0].iterhosts()))).all()
            for ip in net[0].iterhosts():
                if str(ip) not in ips:
                    freeips.append(find_freeip(comm_freeips, str(ip)))
                else:
                    freeip = find_freeip(comm_freeips, str(ip), return_none=True, exists=True)
                    if freeip:
                        freeips.append(freeip)
        return freeips

    def freeip_get_by_ip(self, ipaddr):
        ip = self._ip_to_int(ipaddr)
        if ip is not None and ip>0:
            freeip = self.session.query(FreeIP).filter(FreeIP.ip == ip).first()
            if freeip:
                return freeip                   

    def freeip_set_comment(self, ipaddr, comment):
        ip = self._ip_to_int(ipaddr)
        if ip is not None and ip > 0:
            freeip = self.session.query(FreeIP).filter(FreeIP.ip == ip).first()
            if freeip is not None:
                if comment == "":
                    self.session.query(FreeIP).filter(FreeIP.ip == ip).delete()
                    freeip = None
                else:
                    freeip.comment = comment
            else:
                if comment == "":
                    return None
                freeip = FreeIP()
                freeip.ip = ip
                freeip.comment = comment
                self.session.add(freeip)
            self.save_all()
            if freeip:
                return freeip

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
            ip = struct.unpack("!I", socket.inet_aton(ipaddr))[0]
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


class FreeIP(Base):
    __tablename__ = "freeip"

    ip = Column(Integer, primary_key=True)
    comment = Column(String(250))

    @reconstructor
    def init_on_load(self):
        self.exists = False
        self.ipaddr = socket.inet_ntoa(struct.pack("!I", self.ip))


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
                if node not in self.nodes[node.parent_id].child_list:
                    self.nodes[node.parent_id].child_list.append(node)
            else:
                if node not in self.nodes[0].child_list:
                    self.nodes[0].child_list.append(node)

    def __getitem__(self, key):
        try:
            return self.nodes[key]
        except IndexError:
            return False

    def __iter__(self):
        return iter(self.nodes.values())


class NodeException(Exception):
    pass
