#!/usr/bin/python

from gsm_call_fsm import GsmCallFsm, GsmCallConnector
from mncc_sock import MnccSocket
from thread import start_new_thread
import pykka
import logging
import signal, sys, time
import readline, code

# MnccActor provides an interface for GsmCallFsm to send MNCC messages
class MnccActor(pykka.ThreadingActor):
    def __init__(self, mncc_sock):
        super(MnccActor, self).__init__()
        self.mncc_sock = mncc_sock

    def on_receive(self, message):
        if message['type'] == 'send':
            msg = message['msg']
            print 'MnccActor TxMNCC %s' % msg
            mncc_sock.send(msg)
        else:
            raise Exception('mncc', 'MnccActor Received unhandled %s' % message)

# MNCC receive thread, broadcasting received MNCC packets to GsmCallFsm
def mncc_rx_thread(mncc_sock):
    while 1:
        msg = mncc_sock.recv()
        print "MnccActor RxMNCC %s, broadcasting to Call FSMs" % msg
        # we simply broadcast to all calls
        pykka.ActorRegistry.broadcast({'type': 'mncc', 'msg': msg}, GsmCallFsm)

# capture SIGINT (Ctrl+C) and stop all actors
def sigint_handler(signum, frame):
    pykka.ActorRegistry.stop_all()
    sys.exit(0)

logging.basicConfig(level=logging.DEBUG)

signal.signal(signal.SIGINT, sigint_handler)

# start the MnccSocket and associated pykka actor + rx thread
mncc_sock = MnccSocket()
mncc_act = MnccActor.start(mncc_sock)
start_new_thread(mncc_rx_thread, (mncc_sock,))

# convenience wrapper
def connect_call(msisdn_a, msisdn_b):
    call_conn = GsmCallConnector.start(mncc_act).proxy()
    call_conn.start_call_ab(msisdn_a, msisdn_b)
    return call_conn

# start a first bogus call
connect_call("7839", "3802")
connect_call("3809", "3814")
connect_call("3805", "3806")
connect_call("3812", "3815")
connect_call("3807", "3811")
connect_call("3804", "3808")
connect_call("3803", "3813")

time.sleep(1)

# start a shell to enable the user to add more calls as needed
vars = globals().copy()
vars.update(locals())
shell = code.InteractiveConsole(vars)
try:
    shell.interact()
except SystemExit:
    pass
# clan up after user leaves interactive shell
sigint_handler(signal.SIGINT, None)
