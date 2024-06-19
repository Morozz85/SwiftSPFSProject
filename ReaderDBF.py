import os
from dbf_light import Dbf

path_to_file = r"dbfile.dbf"

class ReaderDBF():
    def __init__(self, path_to_file):
        self.dbf_data = self.get_dbf_data(path_to_file)

    def get_dbf_data(self, path_to_file):
        with Dbf.open(path_to_file) as dbf:
            dbf_data = [row for row in dbf]
        return dbf_data
    

def main():
    ReaderDBF(path_to_file)

if __name__ == "__main__":
    main()

