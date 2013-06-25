#! /usr/bin/python

from web import app

if __name__ == "__main__":
    app.run(use_debugger=True, debug=True,
            use_reloader=True)
