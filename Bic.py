import os
from dbf_light import Dbf

path_to_bic_file = r"lib\MBRBANKS.DBF"


##список валют
class Bic():
    def __init__(self, path_to_bic_file):
        self.bic_list = self.get_bic(path_to_bic_file)

    def get_bic(self, path_to_bic_file):
        with Dbf.open(path_to_bic_file) as dbf:
            
            bic_list = [row for row in dbf]
##            print(bic_list[0])
        return bic_list
