from .qsynthdb import QSynthDB
import os
import time

from multiprocessing import Process
from multiprocessing.managers import BaseManager, MakeProxyType, public_methods


QSYNTHDBSERVER_PORT = 50000
QSYNTHDBSERVER_AUTHKEY=b'qsynthdbser'



PROJECT_PATH = os.getcwd()
TABLE_PATH = os.path.join(PROJECT_PATH,"qsynth_table")



class QSynthDBServer():
    def __init__(self, path=os.path.join(TABLE_PATH, "msynth_oracle.db")):
        self.db = QSynthDB(path)

class QSynthDBServerConnection:
    def __init__(self):
        pass
    def vrs(self):
        global db
        return db.db.vrs
    def inps(self):
        global db
        return db.db.inps
    def get(self, key):
        global db
        return db.db.table.get(key)
    
QSynthDBServerConnectionProxy = MakeProxyType("QSynthDBServerConnection", public_methods(QSynthDBServerConnection))
BaseManager.register("QSynthDBServerConnection", QSynthDBServerConnection, QSynthDBServerConnectionProxy)

def _startServer():
    global db
    db = QSynthDBServer()
    manager = BaseManager(address=('', QSYNTHDBSERVER_PORT), authkey=QSYNTHDBSERVER_AUTHKEY)
    s = manager.get_server()
    s.serve_forever()

def startQSynthDBServer():
    print("Creating QSynthDBServer")
    global qsynthServer
    qsynthServer = Process(target=_startServer, args=())
    qsynthServer.start()
    time.sleep(1)
    return qsynthServer

def stopQSynthDBServer():
    print("Terminating QSynthDBServer...")
    global qsynthServer
    qsynthServer.terminate()

def connectQSynthProvider(provider):
    manager = BaseManager(address=('', QSYNTHDBSERVER_PORT), authkey=QSYNTHDBSERVER_AUTHKEY)
    manager.connect()
    connection = manager.QSynthDBServerConnection()

    provider.db.vrs = connection.vrs()
    provider.db.inps = connection.inps()
    provider.db.table = connection

