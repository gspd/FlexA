"""
This package is responsible to start server client and server sync
Every configurations of servers is in config.py

You can start servers with
    -i [ipv4]        to specify your interface
    -p [open port]   to specify port of server client
    -v               to verbose
    -vv              to more verbose

"""

#initialize configs
from server import config
import file