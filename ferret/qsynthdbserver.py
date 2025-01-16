
import plyvel
import json
import os
import time

from multiprocessing import Process
from multiprocessing.managers import BaseManager, MakeProxyType, public_methods


QSYNTHDBSERVER_PORT = 50000
QSYNTHDBSERVER_AUTHKEY=b'qsynthdbser'


META_KEY = b"metadatas"
VARS_KEY = b"variables"
INPUTS_KEY = b"inputs"
SIZE_KEY = b"size"

PROJECT_PATH = os.getcwd()
TABLE_PATH = os.path.join(PROJECT_PATH,"qsynth_table", "msynth_oracle")



class QSynthDBServer():
    def __init__(self):
        self.table = plyvel.DB(TABLE_PATH)
        self.metas = json.loads(self.table.get(META_KEY))
        self.vrs = list(json.loads(self.table.get(VARS_KEY)).items())
        self.inps = json.loads(self.table.get(INPUTS_KEY))

class QSynthDBServerConnection:
    def __init__(self):
        pass
    def vrs(self):
        global db
        return db.vrs
    def inps(self):
        global db
        return db.inps
    def metas(self):
        global db
        return db.metas
    def get(self, key):
        global db
        return db.table.get(key)
    
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
    provider.metas = connection.metas()
    provider.vrs = connection.vrs()
    provider.inps = connection.inps()
    provider.table = connection

