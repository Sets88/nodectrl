# -*- coding: utf-8 -*-
import json

class Settings(object):
    def __init__(self):
        try:
            f = open("settings.json", "r")
        except IOError:
            self.options = {}
        else:
            self.options = json.load(f)

    def __getitem__(self, key):
        try:
            return self.options[key]
        except KeyError:
            return None

    def __setitem__(self, key, val):
        self.options[key] = val

    def save(self):
        f = open("settings.json", "w")
        json.dump(self.options, f, indent=4)

settings = Settings()