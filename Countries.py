import os
from dbf_light import Dbf

path_to_country_file = r"lib\Countries.dbf"

##список cтран
class Countries():
    def __init__(self, path_to_country_file):
        self.country_list = self.get_codes_list(path_to_country_file)

    def get_codes_list(self, path_to_country_file):
        with Dbf.open(path_to_country_file) as dbf:
            country_list = [[row.co_code_2, row.co_name] for row in dbf]
        return country_list
