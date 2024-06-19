
path_to_file = "spfs\ed574.txt"


class GetSpfsBic():
    def __init__(self):
        self.main_list = []
        self.create_dictionary()

    def create_dictionary(self):
        self.dictionary = {}
        self.dictionary.setdefault("Наименование","")
        self.dictionary.setdefault("Уникальный идентификатор","")
        self.dictionary.setdefault("БИК","")
        self.dictionary.setdefault("КП","")
        self.dictionary.setdefault("Обмен ЭС через ЦОС","")
##        self.dictionary.setdefault("Код услуги","")
##        self.dictionary.setdefault("Дата начала обмена сообщениями","")
        return self.dictionary
        

    def get_fields_from_txt(self, path_to_file):
        dictionary = self.create_dictionary()
        start = False
        self.line_name = False
        with open(path_to_file, "r") as f:
            for line in f:
                #Считываем название
                if line.startswith("Наименование") and not start:
                    self.line_name = True
                    dictionary = self.create_dictionary()
                    self.name = line.split(":")[1].strip()
                    dictionary.update({"Наименование":self.name})
                    start = True
                
                #Считываем уникальный идентификатор    
                elif line.strip().startswith("Уникальный идентификатор") and start:
                    self.line_name = False
                    uid = line.split(":")[1].strip()
                    dictionary.update({"Уникальный идентификатор":uid})

                #БИК обслуживающего ПБР: 
                elif line.strip().startswith("БИК") and start:
                    bic = line.split(":")[1].strip()
                    dictionary.update({"БИК":bic})
                
                #КП: 
                elif line.strip().startswith("КП") and start:
                    kp = line.split(":")[1].strip()
                    dictionary.update({"КП":kp})

                #Обмен: 
                
                elif line.strip().startswith("Обмен ЭС") and start:
                    obmen = line.split(":")[1].strip()
                    dictionary.update({"Обмен ЭС через ЦОС":obmen})

                #Код услуги: 
                elif line.strip().startswith("Код услуги") and start:
                    code = line.split(":")[1].strip()
                    number = code.split("-")[0]
                    dictionary.setdefault("Код услуги - {}".format(number), "")
                    
                #Дата начала: 
                elif line.strip().startswith("Дата начала") and start:
                    date = line.split(":")[1].strip()
                    dictionary.update({"Код услуги - {}".format(number):[number,date]})
                
                elif self.line_name:
                    self.name += line.strip()
                    dictionary.update({"Наименование":self.name})

                elif start:
                    self.main_list.append(dictionary)
                    start = False


        return self.main_list          
        


if __name__ == "main":
    main_list = GetSpfsBic().get_fields_from_txt(path_to_file)
    for elem in main_list:
        print(elem)
                
