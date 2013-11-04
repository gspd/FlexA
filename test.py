import os
import sys
import message
import logging

logging.basicConfig(level=logging.DEBUG)

def test_send(connections, repeat):
    c = []

    for i in range(connections):
        c.append(message.SendThread())
        c[i].start()
        logging.debug("Connection number {} successful!".format(i))

    msg = "Hello World number {} from {}!"
    for i in range(repeat):
        for j in range(connections):
            c[j].send(message.Types.SEND_FILE, msg.format(i, j))

    for i in range(connections):
        c[i].disconnect()


def test_server():
    server = message.Receive()

if __name__ == '__main__':
    test_send(100, 10)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
