META_KEY = b"metadatas"
VARS_KEY = b"variables"
INPUTS_KEY = b"inputs"
SIZE_KEY = b"size"


class QSynthDBSQLite3Table():
    def __init__(self, cur):
        self.cur = cur

    def get(self, key):
        res = self.cur.execute("SELECT min_expr FROM oracle WHERE hash=?", (key,)).fetchone()
        if res != None: res = res[0]
        return res

class QSynthDB():
    def __init__(self, path):
        if path.endswith(".db"): # sqlite3
            import sqlite3
            self.sqldb = True
            self.dbtable = sqlite3.connect(path)
            self.cur = self.dbtable.cursor()

            input_count = self.cur.execute("SELECT MAX(indx) FROM inputs").fetchone()[0]+1
            
            self.vrs = [(t[0], t[1]) for t in self.cur.execute("SELECT name, bits FROM variables").fetchall()]
            self.inps = []
            for i in range(input_count):
                inps = self.cur.execute("SELECT variable_name, value FROM inputs WHERE indx=?", (i,)).fetchall()
                inpdict = {}
                for tuple in inps:
                    inpdict[tuple[0]] = tuple[1]
                self.inps.append(inpdict)

            # optimization in memory if oracle isn't too big
            oracle_count = self.cur.execute("SELECT COUNT(*) FROM oracle").fetchone()[0]
            if oracle_count < 500000:
                self.table = {}
                data = self.cur.execute("SELECT hash, min_expr FROM oracle").fetchall()
                for entry in data:
                    self.table[entry[0]] = entry[1]
                self.cur.close()
                self.dbtable.close()
            else:
                self.table = QSynthDBSQLite3Table(self.cur)
        else:
            import plyvel, json
            self.sqldb = False
            self.table = plyvel.DB(path)
            self.metas = json.loads(self.table.get(META_KEY))
            self.vrs = list(json.loads(self.table.get(VARS_KEY)).items())
            self.inps = json.loads(self.table.get(INPUTS_KEY))
            assert self.metas["hash_mode"] == "MD5"
            for var, bits in self.vrs:
                assert bits == 64