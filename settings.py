# -*- coding: utf-8 -*-
import json

class Settings(object):
    options = {"users":{}, 
               "secret":"",
               "db": {
                        "engine": "sqlite",
                        "db": "nodes.db",
                        "user": "",
                        "password": "",
                        "port": ""
                },
                "categories": [
                        ["Default" , [("192.168.1.0/24", "1")]]
                    ],
                "addlinks": {}
    }

    def __init__(self):
        try:
            f = open("settings.json", "r")
        except IOError:
            self.load()
        else:
            self.load(json.load(f))


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
                self.options['users'].pop(name)
            except KeyError:
                pass

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

    def set_secret(self, secret):
        self.options['secret'] = secret

    def set_db_options(self, db):
        if "engine" and "db" in db:
            self.options['db']['engine'] = db['engine']
            self.options['db']['db'] = db['db']
            try:
                self.options['db']['user'] = db['user']
                self.options['db']['password'] = db['password']
                self.options['db']['port'] = db['port']
            except KeyError:
                pass

    def set_categories(self, data):
        self.options['categories'] = data

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

    def save(self):
        f = open("settings.json", "w")
        json.dump(self.options, f, indent=4)

settings = Settings()