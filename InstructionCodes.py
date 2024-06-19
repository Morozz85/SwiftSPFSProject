import os
from dbf_light import Dbf

path_to_currency_file = r"lib\F72Key.DBF"


##список валют
class InstructionCodes():
    def __init__(self, path_to_currency_file):
        self.currency_list = self.get_codes_list(path_to_currency_file)

    def get_codes_list(self, path_to_currency_file):

        with Dbf.open(path_to_currency_file) as dbf:
            
            currency_list = [(row.keyword, row.coment) for row in dbf]
        return currency_list


