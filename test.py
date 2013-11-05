from threading import Thread
import logging
from xmlrpc.client import ServerProxy
import socket
from timeit import timeit

def listdir():
    server_addr = 'http://{}:5500'.format(socket.gethostname())
    s = ServerProxy(server_addr)
    s.list_directory()

def test_send(connections):
        c = []
        for i in range(connections):
            c.append(Thread(target=listdir))
            c[i].start()
        for conn in c:
            conn.join()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    print(timeit(stmt="test_send(100)",
                 setup="from __main__ import test_send",
                 number=5))

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
