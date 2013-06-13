#! /usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask
from flask import request, redirect, abort
from flask import jsonify
from flask import make_response
from flask import render_template
from node import NodesAPI, Node, NodeException
from settings import settings
from auth import Auth
from functools import wraps
import re

app = Flask(__name__)

sw_api = NodesAPI(settings['db'])

auth = Auth(settings['users'], settings['secret'])

app.secret_key = str(settings['secret'])

cookies = {}


def get_cat():
    """Gets cat from cookies otherwise returns 0"""
    global cookies
    cats = str(get_cookie("cat")).split(",")

    try:
        for cat in cats:
            if settings['categories'][int(cat)]:
                pass
    except (IndexError, ValueError):
        return [0]
    else:
        return cats


def get_cookie(name):
    if name in cookies:
        return cookies[name]
    else:
        return request.cookies.get(name)


########### DECORATORS #############


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

def update_cookie(func):
    """Checks if cookie change needed on response"""
    @wraps(func)
    def wraper(*args, **kwargs):
        global cookies
        response = make_response(func(*args, **kwargs))
        if cookies:
            for (key, val) in cookies.items():
                response.set_cookie(key, val)
            cookies.clear()
        return response
    return wraper


############# MAIN #################


@app.route("/login/", methods=["GET", "POST"])
def login():
    return auth.do_login_window()

@app.route("/logout/")
@logged_in_or_404
def logout():
    return auth.do_logout()


@app.route("/")
@update_cookie
@login_required
def nodes():
    """Display nodes list"""
    nodes = sw_api.list_nodes(get_cat())
    sw_api.close_session()
    return render_template("nodes.html", nodes=nodes, addlinks=settings['addlinks'], cats=enumerate(settings['categories']))

@app.route("/editnode/<int:id>/", methods=["GET", "POST"])
@login_required
def edit_node(id):
    """Display node list, with edit field in it, and if POST save node"""
    if request.method == 'POST':
        node = sw_api.get_by_id(id)
        node.comment = request.form['comment']
        node.port = request.form['port']
        node.set_ip(request.form['ip'])
        sw_api.save_all()
        return redirect("/")
    else:
        nodes = sw_api.list_nodes(get_cat())
        sw_api.close_session()
        return render_template("nodes.html", nodes=nodes, addlinks=settings['addlinks'], cats=enumerate(settings['categories']), act="edit", id=id)


@app.route("/addnode/<int:id>/", methods=["GET", "POST"])
@login_required
def add_node(id):
    """Display node list, with add field under it, and if POST save node"""
    if request.method == 'POST':
        node = Node()
        if id == 0:
            node.parent_id = None
        else:
            node.parent_id = id
        node.comment = request.form['comment']
        node.catid = get_cat()[0]
        sw_api.add_node(node)
        sw_api.save_all()
        return redirect("/")
    else:
        nodes = sw_api.list_nodes(get_cat())
        sw_api.close_session()
        return render_template("nodes.html", nodes=nodes, addlinks=settings['addlinks'], cats=enumerate(settings['categories']), act="add", id=id)


@app.route("/movenode/<int:id>/", methods=["GET", "POST"])
@login_required
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
        return render_template("nodes.html", nodes=nodes, addlinks=settings['addlinks'], cats=enumerate(settings['categories']), act="move", id=id)


@app.route("/deletenode/<int:id>/")
@login_required
def delete_node(id):
    sw_api.delete_node(id)
    sw_api.save_all()
    return redirect("/")


@app.route("/cat/<int:catid>")
@login_required
def set_cat(catid):
    """Change category of nodes"""
    global cookies
    if len(settings['categories']) > int(catid):
        cookies["cat"] = catid
    return redirect("/")


@app.route("/checknodes/")
@login_required
def check_nodes():
    sw_api.check_nodes(get_cat())
    return redirect("/")


@app.route("/autoaddnodes/")
@login_required
def autoadd_nodes():
    sw_api.autoadd_nodes(get_cat())
    return redirect("/")


@app.route("/automovenodes/")
@login_required
def automove_nodes():
    sw_api.automove_nodes(get_cat(), settings['categories'])
    return redirect("/")


@app.route("/resetflag/<int:id>/")
@login_required
def reset_flag(id):
    try:
        sw_api.reset_flags(get_cat(), int(id))
    except NodeException:
        abort(404)
    return redirect("/")

@app.route("/resetflags/")
@login_required
def reset_flags():
    sw_api.reset_flags(get_cat())
    return redirect("/")


############# SETTINGS ##################


@app.route("/settings/")
@login_required
def settings_menu():
    return render_template("settings.html", settings=settings, addlinks=settings['addlinks'], cats=enumerate(settings['categories']))

@app.route("/settings/setsecret/", methods=["GET", "POST"])
@login_required
def settings_set_secret():
    if request.method == 'POST':
        settings.set_secret(request.form['secret'])
        return redirect("/settings/")
    else:
        abort(404)

@app.route("/settings/setdboptions/", methods=["GET", "POST"])
@login_required
def settings_set_db_options():
    if request.method == 'POST':
        db_opt = {}
        db_opt['engine'] = request.form['engine']
        db_opt['db'] = request.form['db']
        db_opt['user'] = request.form['user']
        db_opt['password'] = request.form['password']
        db_opt['port'] = request.form['port']
        settings.set_db_options(db_opt)
        sw_api.db_connect(settings['db'])
        return redirect("/settings/")
    else:
        abort(404)

@app.route("/settings/edituser/<name>/", methods=["GET", "POST"])
@login_required
def settings_edit_user(name):
    if request.method == 'POST':
        settings.edit_user(name, request.form['password'])
        return redirect("/settings/")
    else:
        return render_template("settings.html", settings=settings, addlinks=settings['addlinks'], cats=enumerate(settings['categories']), act="edituser", id=name)

@app.route("/settings/adduser/", methods=["GET", "POST"])
@login_required
def settings_add_user():
    if request.method == 'POST':
        settings.edit_user(request.form['login'], request.form['password'])
        return redirect("/settings/")
    else:
        return render_template("settings.html", settings=settings, addlinks=settings['addlinks'], cats=enumerate(settings['categories']), act="adduser")

@app.route("/settings/deleteuser/<name>/")
@login_required
def settings_delete_user(name):
    settings.delete_user(name)
    return redirect("/settings/")

@app.route("/settings/editlink/<name>/", methods=["GET", "POST"])
@login_required
def settings_edit_link(name):
    if request.method == 'POST':
        settings.edit_link(request.form['name'].replace("/", ""), request.form['url'], name)
        return redirect("/settings/")
    else:
        return render_template("settings.html", settings=settings, addlinks=settings['addlinks'], cats=enumerate(settings['categories']), act="editlink", id=name)

@app.route("/settings/addlink/", methods=["GET", "POST"])
@login_required
def settings_add_link():
    if request.method == 'POST':
        settings.edit_link(request.form['name'], request.form['url'])
        return redirect("/settings/")
    else:
        return render_template("settings.html", settings=settings, addlinks=settings['addlinks'], cats=enumerate(settings['categories']), act="addlink")

@app.route("/settings/deletelink/<name>/")
@login_required
def settings_delete_link(name):
    settings.delete_link(name)
    return redirect("/settings/")

@app.route("/settings/addcategory/", methods=["GET", "POST"])
@login_required
def settings_add_category():
    if request.method == 'POST':
        settings.add_category(request.form['name'])
        return redirect("/settings/")
    else:
        return render_template("settings.html", settings=settings, addlinks=settings['addlinks'], cats=enumerate(settings['categories']), act="addcategory")

@app.route("/settings/deletecategory/<int:id>/")
@login_required
def settings_delete_category(id):
    settings.delete_category(id)
    return redirect("/settings/")

@app.route("/settings/editcategory/<int:id>/", methods=["GET", "POST"])
@login_required
def settings_edit_category(id):
    if request.method == 'POST':
        settings.edit_category(id, request.form['name'])
        return redirect("/settings/")
    else:
        return render_template("settings.html", settings=settings, addlinks=settings['addlinks'], cats=enumerate(settings['categories']), act="editcategory", id=id)

@app.route("/settings/addsubnet/<int:catid>/", methods=["GET", "POST"])
@login_required
def settings_add_subnet(catid):
    if request.method == 'POST':
        settings.add_subnet(catid, request.form['net'], request.form['vlan'])
        return redirect("/settings/")
    else:
        return render_template("settings.html", settings=settings, addlinks=settings['addlinks'], cats=enumerate(settings['categories']), act="addsubnet", catid=catid)

@app.route("/settings/deletesubnet/<int:catid>/<int:id>/")
@login_required
def settings_delete_subnet(catid, id):
    settings.delete_subnet(catid, id)
    return redirect("/settings/")

@app.route("/settings/editsubnet/<int:catid>/<int:id>/", methods=["GET", "POST"])
@login_required
def settings_edit_subnet(catid,id):
    if request.method == 'POST':
        settings.edit_subnet(int(id), int(catid), request.form['net'], request.form['vlan'])
        return redirect("/settings/")
    else:
        return render_template("settings.html", settings=settings, addlinks=settings['addlinks'], cats=enumerate(settings['categories']), act="editsubnet", catid=catid, id=id)

@app.route("/settings/savesettings/")
@login_required
def settings_save_settings():
    settings.save()
    return redirect("/")


############# AJAX ##################


@app.route("/ajax/editnode/<int:id>/", methods=["GET", "POST"])
@logged_in_or_404
def ajax_edit_node(id):
    resp_dict = {}
    node = sw_api.get_by_id(id)
    if request.method == 'POST':
        node.comment = request.form['comment']
        node.port = request.form['port']
        node.set_ip(request.form['ip'])
        sw_api.save_all()
        resp_dict['result'] = 0
        return jsonify(resp_dict)
    resp_dict['comment'] = node.comment
    resp_dict['ip'] = node.ipaddr
    resp_dict['port'] = node.port
    resp_dict['id'] = node.id
    resp_dict['result'] = 0
    sw_api.close_session()
    return jsonify(resp_dict)

@app.route("/ajax/addnode/<int:id>/", methods=["POST"])
@logged_in_or_404
def ajax_add_node(id):
    resp_dict = {}
    if request.method == 'POST':
        node = Node()
        node.parent_id = id
        node.comment = request.form['comment']
        node.catid = get_cat()[0]
        node.set_ip("0.0.0.0")
        sw_api.add_node(node)

        resp_dict['comment'] = node.comment
        resp_dict['port'] = node.port
        resp_dict['id'] = node.id
        resp_dict['ip'] = node.ipaddr
        resp_dict['result'] = 0

        sw_api.save_all()

        return jsonify(resp_dict)

@app.route("/ajax/movenode/<int:id>/", methods=["GET", "POST"])
@logged_in_or_404
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
        return render_template("moveform.html", node=node, nodes=nodes, cats=enumerate(settings['categories']), act="move", id=id)


@app.route("/ajax/deletenode/<int:id>/")
@logged_in_or_404
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

@app.route("/ajax/")
@logged_in_or_404
def ajax():
    nodes = sw_api.scan_nodes(0)
    sw_api.close_session()
    if nodes:
        return "</br>".join(nodes)
    else:
        abort(404)


if __name__ == "__main__":
    app.run()
