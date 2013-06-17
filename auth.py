from flask import render_template
from flask import make_response
from flask import request, redirect
from flask import flash, url_for
from hashlib import sha512, sha1


class Auth(object):

    def __init__(self, users, secret):
        self.userlist = users
        self.secret = secret
        self.me = ""

    def do_login_window(self):
        if (request.method == "POST"):
            try:
                if self.userlist[request.form['login']] != request.form['pass']:
                    flash("Oops, Login Error")
                    redirect(url_for("login"))
            except KeyError:
                flash("Oops, Login Error")
                redirect(url_for("login"))

            response = make_response(redirect("/"))
            try:
                if request.form['remember']:
                    time = 365 * 24 * 60 * 60
            except:
                time = 24 * 60 * 60
            response.set_cookie("user", request.form['login'], time)
            response.set_cookie("pass", self.hash(request.form[
                                'pass'], request.form["login"]), time)
            self.me = request.form['login']
            return response

        else:
            return render_template("auth.html")

    def do_logout(self):
        response = make_response(redirect("login/"))
        response.set_cookie("user", "", 0)
        response.set_cookie("pass", "", 0)
        return response

    def hash(self, password, user):
        return sha512(self.secret + sha512(password + user).hexdigest() + self.secret).hexdigest()

    def simplehash(self, key):
        return sha1(self.secret + sha512(key).hexdigest() + self.secret).hexdigest()

    def check_ip_hash(self, hashh, ip):
        if self.simplehash(ip) == hashh:
            return True
        else:
            return False

    def get_ip_hash(self, ip):
        return self.simplehash(ip)

    def is_logged(self):
        if len(self.userlist) == 0:
            return True
        try:
            if self.hash(self.userlist[request.cookies.get("user")], request.cookies.get("user")) == request.cookies.get("pass"):
                return True
            else:
                return False
        except:
            return False
