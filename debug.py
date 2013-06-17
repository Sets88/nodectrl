#! /usr/bin/python

from web import app

if __name__ == "__main__":
    # app.debug = True
    # DEBUG_WITH_APTANA: True
    app.run(use_debugger=True, debug=True,
            use_reloader=True)
    # app.run()
