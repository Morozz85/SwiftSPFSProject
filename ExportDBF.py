import code
import dbf
from datetime import date

path_to_file = r"lib\settings.dbf"

data = {
    "s_kp":"NOVKIB010002",
    "s_name":"ООО'Новокиб'",
    "r_kp":"BELERUMMAXXX",
    "r_name":"ООО 'Киви банк'",
    "date": date.today(),
    "number": 1
}

class ExportDBF():
    def __init__(self, path_to_file):
        self.table = dbf.Table(path_to_file, 
                                "s_kp C(200); s_name C(200); r_kp C(200); r_name C(200); date D; number N (12, 0)",
                                codepage="cp866")
        


    def save_dbf(self, data):
        self.table.open(mode=dbf.READ_WRITE)
        self.table.append(data)
       

def main():
    ExportDBF(path_to_file).save_dbf(data)

if __name__ == "__main__":
    main()