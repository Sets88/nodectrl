from flask import render_template
from flask import make_response
from flask import request, redirect
from hashlib import sha512

class Auth(object):
    def __init__(self, users, secret):
        self.userlist = users
        self.secret = secret

    def do_login_window(self):
        if (request.method == "POST"):
            try:
                if self.userlist[request.form['login']] != request.form['pass']:
                    raise(KeyError)
            except KeyError:
                return render_template("auth.html", login=request.form['login'], error="Oops, Login Error")

            response = make_response(redirect("/"))
            try:
                if request.form['remember']:
                    time = 365 * 24 * 60 * 60
            except:
                time = 24 * 60 * 60
            response.set_cookie("user", request.form['login'], time)
            response.set_cookie("pass", self.hash(request.form['pass'], request.form["login"]), time)
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

    def is_logged(self):
        try:
            if self.hash(self.userlist[request.cookies.get("user")], request.cookies.get("user")) == request.cookies.get("pass"):
                return True
            else:
                return False
        except:
            return False