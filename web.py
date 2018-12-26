#! /usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask
from flask import request, redirect, abort, session
from flask import jsonify
from flask import make_response
from flask import render_template
from node import NodesAPI, Node, NodeException, permissions as node_permissons
import gettext
from settings import Settings
from auth import Auth
from functools import wraps
import json
import os
import re

app = Flask(__name__)

sw_api = NodesAPI()

auth = Auth(Settings()['users'], Settings()['secret'])

app.secret_key = str(Settings()['secret'])


current_dir = os.path.dirname(os.path.abspath(__file__))

try:
    translation = gettext.translation('nodectrl', os.path.join(current_dir, 'translations'), languages=[Settings()['language']])
except (IOError):
    translation = gettext.translation('nodectrl', os.path.join(current_dir, 'translations'), languages=["en"])


# Permissions
Settings().join_permissions(node_permissons)

def get_cat(categories=None):
    """Gets cat from session otherwise returns 0"""
    if categories is None:
        cats = str(session.get("cat")).split(",")
    else:
        cats = str(categories).split(",")
    try:
        for cat in cats:
            if Settings()['categories'][int(cat)]:
                pass
    except (IndexError, ValueError):
        return ["0"]
    else:
        return cats


@app.teardown_request
def shutdown_session(exception=None):
    sw_api.close_session()

# DECORATORS #############


def login_required(func):
    @wraps(func)
    def wraper(*args, **kwargs):
        if auth.is_logged():
            return func(*args, **kwargs)
        else:
            return redirect("/login/")
    return wraper


def logged_in_or_404(func):
    @wraps(func)
    def wraper(*args, **kwargs):
        if auth.is_logged():
            return func(*args, **kwargs)
        else:
            return abort(404)
    return wraper

def require_permission(permission):
    def decorator(func):
        @wraps(func)
        def wraper(*args, **kwargs):
            if Settings().has_permissions(permission, auth.is_logged()):
                return func(*args, **kwargs)
            else:
                return abort(404)
        return wraper
    return decorator


# MAIN #################


@app.route("/login/", methods=["GET", "POST"])
def login():
    return auth.do_login_window()


@app.route("/logout/")
@logged_in_or_404
def logout():
    return auth.do_logout()


@app.route("/")
@login_required
def nodes():
    """Display nodes list"""
    nodes = sw_api.list_nodes(get_cat())
    sw_api.close_session()
    return render_template("nodes.html", _=translation.ugettext, nodes=nodes, addlinks=Settings()['addlinks'], cats=enumerate(Settings()['categories']), perms=Settings().get_permissions(auth.is_logged()), currcats=get_cat())


@app.route("/script.js")
def scriptjs():
    """Display script.js file"""
    return render_template("script.js", _=translation.ugettext)


@app.route("/editnode/<int:id>/", methods=["GET", "POST"])
@login_required
@require_permission("nodes_edit_nodes")
def edit_node(id):
    """Display node list, with edit field in it, and if POST save node"""
    if request.method == 'POST':
        node = sw_api.get_by_id(id)
        node.comment = request.form['comment']
        node.set_port(request.form.get('port'))
        node.set_ip(request.form.get('ip'))
        sw_api.save_all()
        return redirect("/")
    else:
        nodes = sw_api.list_nodes(get_cat())
        sw_api.close_session()
        return render_template("nodes.html", _=translation.ugettext, nodes=nodes, addlinks=Settings()['addlinks'], cats=enumerate(Settings()['categories']), perms=Settings().get_permissions(auth.is_logged()), act="edit", id=id)


@app.route("/addnode/<int:id>/", methods=["GET", "POST"])
@login_required
@require_permission("nodes_add_nodes")
def add_node(id):
    """Display node list, with add field under it, and if POST save node"""
    if request.method == 'POST':
        node = Node()
        if id == 0:
            node.parent_id = None
        else:
            node.parent_id = id
        if len(request.form.get('comment').strip()) < 1:
            return redirect("/")
        node.comment = request.form['comment']
        node.catid = get_cat()[0]
        sw_api.add_node(node)
        sw_api.save_all()
        return redirect("/")
    else:
        nodes = sw_api.list_nodes(get_cat())
        sw_api.close_session()
        return render_template("nodes.html", _=translation.ugettext, nodes=nodes, addlinks=Settings()['addlinks'], cats=enumerate(Settings()['categories']), perms=Settings().get_permissions(auth.is_logged()), act="add", id=id)


@app.route("/movenode/<int:id>/", methods=["GET", "POST"])
@login_required
@require_permission("nodes_move_nodes")
def move_node(id):
    """Display node list, with move form, and if POST move node to selected parent"""
    if request.method == 'POST':
        try:
            sw_api.move_node(id, request.form['parent'])
        except NodeException:
            abort(404)
        sw_api.save_all()
        return redirect("/")
    else:
        nodes = sw_api.list_nodes(get_cat())
        sw_api.close_session()
        return render_template("nodes.html", _=translation.ugettext, nodes=nodes, addlinks=Settings()['addlinks'], cats=enumerate(Settings()['categories']), perms=Settings().get_permissions(auth.is_logged()), act="move", id=id)


@app.route("/deletenode/<int:id>/")
@login_required
@require_permission("nodes_delete_nodes")
def delete_node(id):
    sw_api.delete_node(id)
    sw_api.save_all()
    return redirect("/")


@app.route("/cat/<int:catid>")
@login_required
def set_cat(catid):
    """Change category of nodes"""
    if len(Settings()['categories']) > int(catid):
        session["cat"] = catid
    return redirect("/")

@app.route("/cat/add/<int:catid>")
@login_required
def add_cat(catid):
    """Add category of nodes"""
    cats = get_cat()
    try:
        if Settings()['categories'][int(catid)]:
            cats.append(catid)
    except (IndexError, ValueError):
        return redirect("/")
    session["cat"] = ",".join(str(x) for x in set(cats))
    return redirect("/")

@app.route("/cat/rem/<int:catid>")
@login_required
def remove_cat(catid):
    """Remove category of nodes"""
    cats = get_cat()
    try:
        if Settings()['categories'][int(catid)]:
            cats.remove(str(catid))
    except (IndexError, ValueError):
        return redirect("/")
    session["cat"] = ",".join(str(x) for x in set(cats))
    return redirect("/")

@app.route("/checknodes/<int:id>/")
@login_required
@require_permission("nodes_check_nodes")
def check_nodes_by_id(id):
    sw_api.check_tree(get_cat(), int(id))
    return redirect("/")

@app.route("/checknodes/")
@login_required
@require_permission("nodes_check_nodes")
def check_nodes():
    sw_api.check_tree(get_cat(), 0)
    return redirect("/")


@app.route("/autoaddnodes/")
@login_required
@require_permission("nodes_autoadd_nodes")
def autoadd_nodes():
    sw_api.autoadd_nodes(get_cat())
    return redirect("/")


@app.route("/automovenodes/")
@login_required
@require_permission("nodes_automove_nodes")
def automove_nodes():
    sw_api.automove_nodes(get_cat(), Settings()['categories'])
    return redirect("/")


@app.route("/resetflag/<int:id>/")
@login_required
@require_permission("nodes_reset_flags")
def reset_flag(id):
    try:
        sw_api.reset_flags(get_cat(), int(id))
    except NodeException:
        abort(404)
    return redirect("/")


@app.route("/resetflags/")
@login_required
@require_permission("nodes_reset_flags")
def reset_flags():
    sw_api.reset_flags(get_cat())
    return redirect("/")


@app.route("/freeip/")
@login_required
@require_permission("nodes_show_ips")
def free_ip():
    nodes = sw_api.freeip_list(get_cat())
    if not nodes:
        nodes = []
    return render_template("freeip.html", _=translation.ugettext, nodes=nodes, addlinks=Settings()['addlinks'], cats=enumerate(Settings()['categories']))


@app.route("/freeip/editcomment/<ipaddr>/", methods=["GET", "POST"])
@login_required
@require_permission("nodes_show_ips")
def freeip_edit_comment(ipaddr):
    if request.method == 'POST':
        sw_api.freeip_set_comment(ipaddr, request.form.get('comment'))
        return redirect("/freeip/")
    else:
        nodes = sw_api.freeip_list(get_cat())
        if not nodes:
            nodes = []
        return render_template("freeip.html", _=translation.ugettext, nodes=nodes, addlinks=Settings()['addlinks'], cats=enumerate(Settings()['categories']), act="editcomment", ip=ipaddr)

@app.route("/freeip/applycomment/<ipaddr>/", methods=["GET"])
@login_required
@require_permission("nodes_show_ips")
@require_permission("nodes_edit_nodes")
def freeip_apply(ipaddr):
    freeip = sw_api.freeip_get_by_ip(ipaddr)
    node = sw_api.get_by_ip(ipaddr)
    if freeip and node:
        node.comment = freeip.comment
        sw_api.freeip_set_comment(ipaddr, "")
        sw_api.save_all()
        return redirect("/freeip/")
    else:
        abort(404)

# SETTINGS ##################


@app.route("/settings/")
@login_required
@require_permission("settings_edit")
def settings_menu():
    return render_template("settings.html", _=translation.ugettext, settings=Settings(), addlinks=Settings()['addlinks'], cats=enumerate(Settings()['categories']))


@app.route("/settings/setsecret/", methods=["GET", "POST"])
@login_required
@require_permission("settings_edit")
def settings_set_secret():
    if request.method == 'POST':
        Settings().set_secret(str(request.form['secret']))
        app.secret_key = str(request.form['secret'])
        auth.secret = str(request.form['secret'])
        return redirect("/settings/")
    abort(404)


@app.route("/settings/setdboptions/", methods=["GET", "POST"])
@login_required
@require_permission("settings_edit")
def settings_set_db_options():
    if request.method == 'POST':
        db_opt = {}
        db_opt['engine'] = request.form['engine']
        db_opt['db'] = request.form['db']
        db_opt['user'] = request.form['user']
        if (request.form['password']):
            db_opt['password'] = request.form['password']
        db_opt['host'] = request.form['host']
        db_opt['port'] = request.form['port']
        Settings().set_db_options(db_opt)
        sw_api.db_connect(Settings()['db'])
        return redirect("/settings/")
    abort(404)


@app.route("/settings/edituser/<name>/", methods=["GET", "POST"])
@login_required
@require_permission("settings_edit")
def settings_edit_user(name):
    if request.method == 'POST':
        Settings().edit_user(name, request.form['password'])
        return redirect("/settings/")
    else:
        return render_template("settings.html", _=translation.ugettext, settings=Settings(), addlinks=Settings()['addlinks'], cats=enumerate(Settings()['categories']), act="edituser", id=name)


@app.route("/settings/adduser/", methods=["GET", "POST"])
@login_required
@require_permission("settings_edit")
def settings_add_user():
    if request.method == 'POST':
        Settings().edit_user(request.form['login'], request.form['password'])
        return redirect("/settings/")
    else:
        return render_template("settings.html", _=translation.ugettext, settings=Settings(), addlinks=Settings()['addlinks'], cats=enumerate(Settings()['categories']), act="adduser")


@app.route("/settings/deleteuser/<name>/")
@login_required
@require_permission("settings_edit")
def settings_delete_user(name):
    Settings().delete_user(name)
    return redirect("/settings/")


@app.route("/settings/editlink/<name>/", methods=["GET", "POST"])
@login_required
@require_permission("settings_edit")
def settings_edit_link(name):
    if request.method == 'POST':
        Settings().edit_link(request.form['name'].replace(
            "/", ""), request.form['url'], name)
        return redirect("/settings/")
    else:
        return render_template("settings.html", _=translation.ugettext, settings=Settings(), addlinks=Settings()['addlinks'], cats=enumerate(Settings()['categories']), act="editlink", id=name)


@app.route("/settings/addlink/", methods=["GET", "POST"])
@login_required
@require_permission("settings_edit")
def settings_add_link():
    if request.method == 'POST':
        Settings().edit_link(request.form['name'], request.form['url'])
        return redirect("/settings/")
    else:
        return render_template("settings.html", _=translation.ugettext, settings=Settings(), addlinks=Settings()['addlinks'], cats=enumerate(Settings()['categories']), act="addlink")


@app.route("/settings/deletelink/<name>/")
@login_required
@require_permission("settings_edit")
def settings_delete_link(name):
    Settings().delete_link(name)
    return redirect("/settings/")


@app.route("/settings/addcategory/", methods=["GET", "POST"])
@login_required
@require_permission("settings_edit")
def settings_add_category():
    if request.method == 'POST':
        Settings().add_category(request.form['name'])
        return redirect("/settings/")
    else:
        return render_template("settings.html", _=translation.ugettext, settings=Settings(), addlinks=Settings()['addlinks'], cats=enumerate(Settings()['categories']), act="addcategory")


@app.route("/settings/deletecategory/<int:id>/")
@login_required
@require_permission("settings_edit")
def settings_delete_category(id):
    Settings().delete_category(id)
    return redirect("/settings/")


@app.route("/settings/editcategory/<int:id>/", methods=["GET", "POST"])
@login_required
@require_permission("settings_edit")
def settings_edit_category(id):
    if request.method == 'POST':
        Settings().edit_category(id, request.form['name'])
        return redirect("/settings/")
    else:
        return render_template("settings.html", _=translation.ugettext, settings=Settings(), addlinks=Settings()['addlinks'], cats=enumerate(Settings()['categories']), act="editcategory", id=id)


@app.route("/settings/addsubnet/<int:catid>/", methods=["GET", "POST"])
@login_required
@require_permission("settings_edit")
def settings_add_subnet(catid):
    if request.method == 'POST':
        Settings().add_subnet(catid, request.form['net'], request.form['vlan'])
        return redirect("/settings/")
    else:
        return render_template("settings.html", _=translation.ugettext, settings=Settings(), addlinks=Settings()['addlinks'], cats=enumerate(Settings()['categories']), act="addsubnet", catid=catid)


@app.route("/settings/deletesubnet/<int:catid>/<int:id>/")
@login_required
@require_permission("settings_edit")
def settings_delete_subnet(catid, id):
    Settings().delete_subnet(catid, id)
    return redirect("/settings/")


@app.route("/settings/editsubnet/<int:catid>/<int:id>/", methods=["GET", "POST"])
@login_required
@require_permission("settings_edit")
def settings_edit_subnet(catid, id):
    if request.method == 'POST':
        Settings().edit_subnet(int(catid), int(id), request.form['net'], request.form['vlan'])
        return redirect("/settings/")
    else:
        return render_template("settings.html", _=translation.ugettext, settings=Settings(), addlinks=Settings()['addlinks'], cats=enumerate(Settings()['categories']), act="editsubnet", catid=catid, id=id)


@app.route("/settings/editpermission/<permission>/", methods=["GET", "POST"])
@login_required
@require_permission("settings_edit")
def settings_edit_permission(permission):
    if request.method == 'POST':
        Settings().set_permissions(permission, request.form['permission'])
        return redirect("/settings/")
    else:
        return render_template("settings.html", _=translation.ugettext, settings=Settings(), addlinks=Settings()['addlinks'], cats=enumerate(Settings()['categories']), act="editpermission", permission=permission)


@app.route("/settings/generatehash/", methods=["POST"])
@login_required
@require_permission("settings_edit")
def settings_generate_hash():
    if request.method == 'POST':
        hashh = auth.get_ip_hash(request.form['text'])
        return render_template("settings.html", _=translation.ugettext, settings=Settings(), addlinks=Settings()['addlinks'], cats=enumerate(Settings()['categories']), hashh=hashh)
    else:
        abort(404)


@app.route("/settings/setlanguage/", methods=["POST"])
@login_required
@require_permission("settings_edit")
def settings_set_language():
    global translation
    if request.method == 'POST':
        Settings().set_language(request.form['language'])
        translation = gettext.translation('nodectrl', os.path.join(current_dir, 'translations'), languages=[Settings()['language']])
        return redirect("/settings/")


@app.route("/settings/savesettings/")
@login_required
@require_permission("settings_edit")
def settings_save_settings():
    Settings().save()
    return redirect("/")


# AJAX ##################


@app.route("/ajax/editnode/<int:id>/", methods=["GET", "POST"])
@logged_in_or_404
@require_permission("nodes_edit_nodes")
def ajax_edit_node(id):
    resp_dict = {}
    node = sw_api.get_by_id(id)
    if request.method == 'POST':
        if len(request.form.get('comment', "").strip()) < 1:
            resp_dict['result'] = 1
            return jsonify(resp_dict)
        node.comment = request.form['comment']
        node.set_port(request.form.get('port'))
        node.set_ip(request.form.get('ip'))
        sw_api.save_all()
        resp_dict['adminbut'] = render_template("adminbut.html", _=translation.ugettext, node=node, perms=Settings().get_permissions(auth.is_logged()))
    else:
        resp_dict['html'] = render_template("editnode.html", _=translation.ugettext, node=node)
    resp_dict['comment'] = node.comment.replace('"', "&quot;")
    resp_dict['ip'] = node.ipaddr
    resp_dict['port'] = node.port
    resp_dict['id'] = node.id
    resp_dict['result'] = 0
    sw_api.close_session()
    return jsonify(resp_dict)


@app.route("/ajax/addnode/<int:id>/", methods=["POST"])
@logged_in_or_404
@require_permission("nodes_add_nodes")
def ajax_add_node(id):
    resp_dict = {}
    if request.method == 'POST':
        if len(request.form.get('comment', "").strip()) > 0:
            node = Node()
            node.parent_id = id
            node.comment = request.form['comment']
            node.catid = get_cat()[0]
            node.set_ip("0.0.0.0")
            sw_api.add_node(node)
        else:
            resp_dict['result'] = 1
            return jsonify(resp_dict)

        resp_dict['comment'] = node.comment
        resp_dict['port'] = node.port
        resp_dict['id'] = node.id
        resp_dict['ip'] = node.ipaddr
        resp_dict['result'] = 0
        resp_dict['adminbut'] = render_template("adminbut.html", _=translation.ugettext, node=node, perms=Settings().get_permissions(auth.is_logged()))

        sw_api.save_all()

        return jsonify(resp_dict)
    abort(404)


@app.route("/ajax/movenode/<int:id>/", methods=["GET", "POST"])
@logged_in_or_404
@require_permission("nodes_move_nodes")
def ajax_move_node(id):
    resp_dict = {}
    if request.method == 'POST':
        try:
            sw_api.move_node(id, request.form['parent'])
        except NodeException:
            abort(404)

        resp_dict['id'] = id
        resp_dict['parent'] = request.form['parent']
        resp_dict['result'] = 0

        sw_api.save_all()
        return jsonify(resp_dict)
    else:
        node = sw_api.get_by_id(id)
        nodes = sw_api.list_nodes(get_cat())
        sw_api.close_session()
        return render_template("moveform.html", _=translation.ugettext, node=node, nodes=nodes, cats=enumerate(Settings()['categories']), act="move", id=id)


@app.route("/ajax/deletenode/<int:id>/")
@logged_in_or_404
@require_permission("nodes_delete_nodes")
def ajax_delete_node(id):
    resp_dict = {}
    if sw_api.delete_node(id):
        resp_dict['result'] = "0"
    else:
        resp_dict['result'] = "1"
    sw_api.save_all()
    return jsonify(resp_dict)


@app.route("/ajax/resetflag/<int:id>/")
@logged_in_or_404
@require_permission("nodes_reset_flags")
def ajax_reset_flag(id):
    resp_dict = {}
    if sw_api.reset_flags(get_cat(), id):
        resp_dict['result'] = "0"
    else:
        resp_dict['result'] = "1"
    return jsonify(resp_dict)


@app.route("/ajax/ipcalc/")
def ajax_ipcalc():
    return render_template("ipcalc.html")


@app.route("/ajax/getswitchbymac/<mac>/")
def ajax_get_nodename_by_mac(mac):
    mac = mac.replace("-", ":").strip()
    resp_dict = {}
    if re.match("^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$", mac) is None:
        resp_dict['result'] = "1"
    else:
        res = sw_api.get_nodename_by_mac(get_cat(), mac)
        if res:
            resp_dict['result'] = "0"
            resp_dict['comment'] = res
        else:
            resp_dict['result'] = "1"
    return jsonify(resp_dict)


@app.route("/ajax/freeip/editcomment/<ipaddr>/", methods=["GET", "POST"])
@logged_in_or_404
@require_permission("nodes_show_ips")
def ajax_freeip_edit(ipaddr):
    resp_dict = {}
    if request.method == 'POST':
        freeip = sw_api.freeip_set_comment(ipaddr, request.form['comment'])
        if freeip:
            resp_dict['comment'] = freeip.comment
            resp_dict['result'] = 0
        elif request.form['comment'] == "":
            if sw_api.get_by_ip(ipaddr):
                resp_dict['exists'] = 1
            resp_dict['comment'] = ""
            resp_dict['result'] = 0
        else:
            resp_dict['result'] = 1

        return jsonify(resp_dict)
    freeip = sw_api.freeip_get_by_ip(ipaddr)
    if freeip:
        resp_dict['ipaddr'] = ipaddr
        resp_dict['comment'] = freeip.comment.replace('"', "&quot;")
    else:
        resp_dict['ipaddr'] = ipaddr
        resp_dict['comment'] = ""
    resp_dict['result'] = 0
    return jsonify(resp_dict)

@app.route("/ajax/freeip/applycomment/<ipaddr>/", methods=["GET"])
@logged_in_or_404
@require_permission("nodes_show_ips")
@require_permission("nodes_edit_nodes")
def ajax_freeip_apply(ipaddr):
    resp_dict = {}
    freeip = sw_api.freeip_get_by_ip(ipaddr)
    node = sw_api.get_by_ip(ipaddr)
    if freeip and node:
        node.comment = freeip.comment
        sw_api.freeip_set_comment(ipaddr, "")
        resp_dict['result'] = 0
        sw_api.save_all()
    else:
        resp_dict['result'] = 1
    return jsonify(resp_dict)

@app.route("/ajax/nodes/")
@login_required
def nodes_ajax():
    """Display nodes list in json"""
    def get_nodes(nodes, group=0):
        node_dict = []
        for node in nodes:
            node_info = {"name": node.comment}
            if node.child_list:
                node_info["children"] = get_nodes(node.child_list, node.id)
            node_dict.append(node_info)
        return node_dict
    nodes = sw_api.list_nodes(get_cat())
    sw_api.close_session()
    return jsonify({"name": "root", "children": get_nodes(nodes)})

@app.route("/ajax/checknodes/<int:id>/")
@login_required
@require_permission("nodes_check_nodes")
def ajax_check_nodes_by_id(id):
    resp_dict = {}
    nodes = sw_api.check_tree(get_cat(), int(id))
    if nodes:
        resp_dict['result'] = '0'
        resp_dict['nodes'] = nodes
    else:
        resp_dict['result'] = '1'
    return jsonify(resp_dict)

@app.route("/ajax/checknodes/")
@login_required
@require_permission("nodes_check_nodes")
def ajax_check_nodes():
    resp_dict = {}
    nodes = sw_api.check_tree(get_cat(), 0)
    if nodes:
        resp_dict['result'] = '0'
        resp_dict['nodes'] = nodes
    else:
        resp_dict['result'] = '1'
    return jsonify(resp_dict)

#    return render_template("nodes.html", nodes=nodes, addlinks=settings['addlinks'], cats=enumerate(settings['categories']), perms=settings.get_permissions(auth.is_logged()))


#@app.route("/ajax/")
#@logged_in_or_404
#def ajax():
#    nodes = sw_api.scan_nodes(0)
#    sw_api.close_session()
#    if nodes:
#        return "</br>".join(nodes)
#    else:
#        abort(404)

# API ##################


@app.route("/api/setflag/<ip>/<int:status>/<hashh>/")
def api_set_flag(ip, status, hashh):
    resp_dict = {}
    if auth.check_ip_hash(hashh, request.remote_addr):
        node = sw_api.get_by_ip(ip)
        if node:
            node.flag = status
            sw_api.save_all()
            resp_dict['result'] = "0"
        else:
            resp_dict['result'] = "1"
        return jsonify(resp_dict)
    abort(404)


@app.route("/api/getnodebymac/<mac>/<hashh>/")
def api_get_nodename_by_mac(mac, hashh):
    if auth.check_ip_hash(hashh, request.remote_addr):
        resp_dict = {}
        if re.match("^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$", mac) is None:
            resp_dict['result'] = "1"
            resp_dict['error'] = "wrong mac format"
        else:
            res = sw_api.get_node_by_mac(get_cat(), mac)
            if res:
                resp_dict['result'] = "0"
                resp_dict['comment'] = res.comment
                resp_dict['id'] = res.id
                resp_dict['ip'] = res.ipaddr
            else:
                resp_dict['result'] = "1"
                resp_dict['error'] = "unknown error"
        return jsonify(resp_dict)
    abort(404)

@app.route("/api/getnodelist/<cat>/<hashh>/")
def api_get_nodelist(cat, hashh):
    def nodes_to_dict(nodes):
        node_list = []
        for node in nodes:
            item = {}
            item['id'] = node.id
            item['comment'] = node.comment
            item['ip'] = node.ipaddr
            item['child_list'] = nodes_to_dict(node.child_list)
            node_list.append(item)
        return node_list

    if auth.check_ip_hash(hashh, request.remote_addr):
        nodes = sw_api.list_nodes(get_cat(cat))
        return json.dumps(nodes_to_dict(nodes))
    abort(404)


if __name__ == "__main__":
    app.run()
