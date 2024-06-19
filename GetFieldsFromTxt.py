import re

class GetFieldsFromTxt():
    def get_fields_from_txt(self, path_to_file):
        area_start_regexp =r"{\b\d:" 
        field_regexp = r"(:\b\d\d[A-Z]?:)"
        area_regexp = r"{\b\d:"
        dictionary = {}
        sub_dictionary = {}
        name_of_field = ""
        previos_name_of_field = ""
        content_of_field = ""
        data = []
        with open(path_to_file, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("{"):
                    match = re.match(area_start_regexp,line)
                    name_of_field = match[0].strip("{")
                    if name_of_field == "1:" or name_of_field == "2:" or name_of_field == "3:" or name_of_field == "5:":
                        dictionary.setdefault(name_of_field,line[match.end(0):-1])
                        continue
                    else:
                        if name_of_field == "4:":
                             dictionary.setdefault(name_of_field)
                             continue
                match = re.match(field_regexp, line)
                if match:
                    name_of_field = match[0].strip()
                    if name_of_field != previos_name_of_field:
                        data = []
                    sub_dictionary.setdefault(name_of_field)
                    content_of_field = line[match.end(0):].strip("\n")
                    data.append(content_of_field)
                    sub_dictionary.update({name_of_field : data})
                    previos_name_of_field = name_of_field
                else:
                    content_of_field = line.strip("\n").strip("}").strip("-").strip()
                    if content_of_field == "":
                        continue
                    data.append(content_of_field)
                    sub_dictionary.setdefault(name_of_field)
                    sub_dictionary.update({name_of_field: data})       
            dictionary.update({"4:": sub_dictionary})
            return dictionary

