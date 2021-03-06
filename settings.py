# -*- coding: utf-8 -*-
import json
import ipaddr
import os

# All permissions and default values
permissions = {"settings_edit" : ["all"]}

class Settings(object):

    root_path = os.path.dirname(os.path.realpath(__file__))

    options = {"users": {},
               "secret": "secret",
               "db": {
                   "engine": "sqlite",
                   "db": os.path.join(root_path, "nodes.db"),
                   "host": "localhost",
                   "user": "",
                   "password": "",
                   "port": ""
               },
               "categories": [
                   ["Default", [("192.168.1.0/24", "1")]]
               ],
               "language": "en",
               "addlinks": {},
               "permissions": permissions
               }

    def __init__(self):
        if(self.__initialized):
            return
        try:
            f = open(os.path.join(self.root_path, "settings.json"), "r")
        except IOError:
            self.load()
        else:
            self.load(json.load(f))
        self.__initialized = True

    def __new__(cls):
        if not hasattr(cls, 'instance'):
             cls.instance = super(Settings, cls).__new__(cls)
             cls.instance.__initialized = False
        return cls.instance

    def __getitem__(self, key):
        try:
            return self.options[key]
        except KeyError:
            return None

    def __setitem__(self, key, val):
        self.options[key] = val

    def edit_user(self, name, password):
        self.options['users'][name] = password

    def edit_users(self, users):
        if isinstance(users, dict):
            for user in users.items():
                self.options['users'][user[0]] = user[1]

    def delete_user(self, name):
        if len(self.options['users']) > 1:
            try:
                return self.options['users'].pop(name)
            except KeyError:
                return None

    def edit_link(self, name, link, oldname=None):
        if oldname is not None:
            self.options['addlinks'].pop(oldname)
        else:
            if name in self.options['addlinks']:
                return
        self.options['addlinks'][name] = link

    def edit_links(self, links):
        if isinstance(links, dict):
            for link in links.items():
                self.options['addlinks'][link[0]] = link[1]

    def delete_link(self, name):
        try:
            self.options['addlinks'].pop(name)
        except KeyError:
            pass

    def add_category(self, name):
        self.options['categories'].append([name, []])


    def edit_category(self, id, name):
        if id < len(self.options['categories']):
            self.options['categories'][id][0] = name

    def delete_category(self, id):
        if len(self.options['categories']) > 1:
            if len(self.options['categories']) <= int(id) + 1:
                self.options['categories'].pop(id)

    def add_subnet(self, catid, net, vlan):
        if len(self.options['categories']) > catid:
            self.options['categories'][catid][1].append([net, vlan])

    def edit_subnet(self, catid, id, net, vlan):
        if len(self.options['categories']) > catid and len(self.options['categories'][catid][1]) > id:
            self.options['categories'][catid][1][id] = (net, vlan)

    def delete_subnet(self, catid, id):
        if len(self.options['categories']) > catid and len(self.options['categories'][catid][1]) > id:
            self.options['categories'][catid][1].pop(id)

    def set_secret(self, secret):
        self.options['secret'] = secret

    def get_nets(self, cats=None):
        nets = []
        for idx, cat in enumerate(self.options['categories']):
            if cats is None or str(idx) in cats:
                for net in cat[1]:
                    nets.append((ipaddr.IPNetwork(net[0]), net[1]))
        return nets

    def set_db_options(self, db):
        if "engine" and "db" in db:
            self.options['db']['engine'] = db['engine']
            self.options['db']['db'] = db['db']
            try:
                self.options['db']['user'] = db['user']
                self.options['db']['password'] = db['password']
                self.options['db']['host'] = db['host']
                if not db['port']:
                    self.options['db']['port'] = "3306"
                else:
                    self.options['db']['port'] = db['port']
            except KeyError:
                pass

    def set_categories(self, data):
        self.options['categories'] = data
#        print "\n %s \n" % self.options['categories']

    def load(self, data=None):
        if data is None:
            pass
        else:
            if "users" in data:
                self.edit_users(data['users'])
            if "secret" in data:
                self.set_secret(data['secret'])
            if "db" in data:
                self.set_db_options(data['db'])
            if "addlinks" in data:
                self.edit_links(data["addlinks"])
            if "categories" in data:
                self.set_categories(data['categories'])
            if "permissions" in data:
                self.init_permissions(data['permissions'])
            if "language" in data:
                self.set_language(data['language'])

    def init_permissions(self, permissions):
        for perm in permissions.items():
            if isinstance(perm[1], list):
                for user in perm[1]:
                    if not self._check_user_exists(user):
                        permissions[perm[0]].pop(perm[1].index(user))
            else:
                permissions[perm[0]] = []
        self.options['permissions'] = permissions


    def join_permissions(self, perm):
        if isinstance(perm, dict):
            perm.update(self.options['permissions'])
            self.options['permissions'] = perm
            return True
        return None

    def has_permissions(self, permission, user):
        if user in self.options['permissions'][permission] or "all" in self.options['permissions'][permission]:
            return True
        elif user == "Annonymous":
            return True
        else:
            return False

    def get_permissions(self, user):
        permissions = []
        for perm in self.options['permissions'].items():
            if user in perm[1] or "all" in perm[1]:
                permissions.append(perm[0])
            elif user == "Annonymous":
                permissions.append(perm[0])
        return permissions

    def _check_user_exists(self, user):
        if user in self.options['users']:
            return True
        elif user == "all":
            return True
        else:
            return False


    def set_permissions(self, permission, data):
        if permission not in self.options['permissions']:
            return None
        users = [x.strip() for x in data.split(',')]
        for user in users:
            if not self._check_user_exists(user):
                users.pop(users.index(user))
        if users == ['']:
            self.options['permissions'][permission] = []
        else:
            self.options['permissions'][permission] = users


    def set_language(self, language):
        if os.path.exists(os.path.join(self.root_path, "translations", language, "LC_MESSAGES", "nodectrl.mo")):
            self.options['language'] = language

    def save(self):
        f = open(os.path.join(self.root_path, "settings.json"), "w")
        json.dump(self.options, f, indent=4)
