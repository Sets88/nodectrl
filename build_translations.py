#! /usr/bin/python

import os
import re
from datetime import datetime

templates = "templates"
translations = "translations"
appname = "nodectrl"

curr_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
header = """msgid ""
msgstr ""
"Project-Id-Version: 1.0\\n"
"POT-Creation-Date: %s\\n"
"PO-Revision-Date: %s\\n"
"Last-Translator: Maxim Nikitenko <sets88@mail.ru>\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: UTF-8\\n"
"Generated-By: build_translations.py\\n"
""" % (curr_date, curr_date)
def get_po_path(lang):
   return os.path.join(translations, lang, "LC_MESSAGES", appname + ".pot")


def get_mo_path(lang):
   return os.path.join(translations, lang, "LC_MESSAGES", appname + ".mo")


def parse_po(lang):
    path_to_po = get_po_path(lang)
    if not os.path.exists(path_to_po):
        return set()
    po_file = open(path_to_po, "r")
    text = po_file.read()
    regx = re.compile(r"""msgid[ \t]*(['"])((?:(?!\1).)+)\1""")
    res = regx.findall(text)
    return set([x[1] for x in res])


def get_translated_strings(text):
    regx = re.compile(r"""_\((['"])((?:(?!\1).)+)\1\)""")
    res = regx.findall(text)
    return [x[1] for x in res]


def get_strings():
    strings = []
    for filename in os.listdir(templates):
        path = os.path.join(templates, filename)
        text = open(path).read()
        new = get_translated_strings(text)
        if new is not None:
            strings.extend(new)
    return set(strings)


def create_po(strings, include_header=True):
    if include_header:
        po = [header]
    else:
        po = []
    for item in strings:
        po.append('msgid "%s"' % item)
        po.append('msgstr "%s"\n' % item)
    return "\n".join(po) + "\n"


def save_to_po(text, lang, rewrite=False):
    if rewrite:
        po_file = open(get_po_path(lang), "w")
    else:
        po_file = open(get_po_path(lang), "a")
    po_file.write(text)
    po_file.close()


def update_po_datetime(lang):
    new_file = []
    with open(get_po_path(lang)) as po_file:
        for line in po_file.readlines():
            if line.startswith('"POT-Creation-Date:'):
                new_file.append('"POT-Creation-Date: %s\\n"\n' % curr_date)
                continue
            elif line.startswith('"PO-Revision-Date:'):
                new_file.append('"PO-Revision-Date: %s\\n"\n' % curr_date)
                continue
            else:
                new_file.append(line)
    with open(get_po_path(lang), "w") as po_file:
        for line in new_file:
            po_file.write(line)


def build_mo_file(lang):
    try:
        os.unlink(get_mo_path(lang))
    except OSError:
        pass
    os.system("/usr/bin/msgfmt -o %s %s" % (get_mo_path(lang), get_po_path(lang)))

def main():
    strings = get_strings()
    for lang in os.listdir(translations):
        lang_strings = parse_po(lang)
        if len(lang_strings) == 0:
            save_to_po(create_po(strings), lang, rewrite=True)
        else:
            if len(strings - lang_strings) > 0:
                save_to_po(create_po(strings - lang_strings, include_header=False), lang)
                update_po_datetime(lang)

        build_mo_file(lang)


#print create_po(get_strings())
main()
