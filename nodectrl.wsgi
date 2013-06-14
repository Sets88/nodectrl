import sys, os

root_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, root_path)

from web import app as application