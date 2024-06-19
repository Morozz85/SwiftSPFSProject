import os
from dbf_light import Dbf

# path_to_currency_file = r"lib\CurrCode.DBF"
path_to_currency_file = r"lib\CURRLIST.DBF"


##список валют
class Currency():
    def __init__(self, path_to_currency_file):
        self.currency_list = self.get_currency_list(path_to_currency_file)


    
    # def get_currency_list(self, path_to_currency_file):
    #     with Dbf.open(path_to_currency_file) as dbf:
    #         currency_list = [(row.code + " - " + row.name) for row in dbf]
    #     return currency_list
    
    def get_currency_list(self, path_to_currency_file):
        with Dbf.open(path_to_currency_file) as dbf:
            currency_list = [(row.iso_lat3 + " - " + row.name_rush.split(",")[0]) for row in dbf]
        return currency_list
    
    


if __name__ == "__main__":
    with Dbf.open(r"lib\CURRLIST.DBF") as dbf:
        currency_list = [(row.iso_lat3 + " - " + row.name_rush.split(",")[0]) for row in dbf]
        print(currency_list)