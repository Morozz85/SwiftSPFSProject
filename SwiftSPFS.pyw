from cgitb import enable
from faulthandler import disable
import re
import ttkcalendar
import tkSimpleDialog
import uuid
import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from Currency import Currency
from InstructionCodes import InstructionCodes
from Bic import Bic
from GetSpfsBic import GetSpfsBic
from Countries import Countries
from GetFieldsFromTxt import GetFieldsFromTxt
from ReaderDBF import ReaderDBF
from ExportDBF import ExportDBF
from datetime import date


# path_to_currency_file = r"lib\CurrCode.DBF"
path_to_currency_file = r"lib\CURRLIST.DBF"
path_to_codes = r"lib\F72Key.DBF"
path_to_bic = r"lib\MBRBANKS.dbf"
path_to_country= r"lib\Countries.dbf"
path_to_bic_spfs = r"spfs\ed574.txt"
path_to_settings = r"lib\settings.dbf"
tabs = None


#вспомогательный класс для отображения календаря(писал не я (скопипиздил) у кого то)
class CalendarDialog(tkSimpleDialog.Dialog):
    """Dialog box that displays a calendar and returns the selected date"""
    def body(self, master):
        self.calendar = ttkcalendar.Calendar(master)
        self.calendar.pack()

    def apply(self):
        self.result = self.calendar.selection


#стили
class Styles(ttk.Style):
    def __init__(self,master):
        super().__init__(master)
        self.configure("Mandatory.TLabel", font=("Veranda", 12), foreground="red")#красный лэйбл (обязательные сообщения)
        self.configure("Heading.TLabel", font=("Veranda", 12))#обычный лэйбл
        ########################################################################
        self.combobox_conf = {"font": ("Verdana", 10, "bold"), "width":27}
        self.help_combobox_conf = {"font": ("Verdana", 10, "bold"), "width":65}
        self.date_entry_conf = {"font": ("Verdana", 10, "bold"),"width":10}
        
        #Стили Entry
        self.entry_conf = {"font": ("Verdana", 10, "bold"), "width":30}
        self.entry_amount_conf = {"font": ("Verdana", 10, "bold"), "width":17}
        self.entry_amount_conf_small = {"font": ("Verdana", 10, "bold"), "width":10}
        self.entry_amount_conf_big = {"font": ("Verdana", 10, "bold"),  "width":45}
        self.entry_search_conf = {"font": ("Verdana", 15, "bold"), "width":15}

        #Cтили Text
        self.text_conf = {"font":("Verdana", 10, "italic"), "background": "#d6ebff"}
        #Стили Settings
        self.label_top = {"font": ("Verdana", 11, "bold","italic")} #верхний label
        self._label = {"font": ("Verdana", 11, "italic")} #левый label
        self.label =  {"font": ("Verdana", 10, "bold")}
        self.settings_entry = {"font": ("Verdana", 10, "bold"), "width":6}
        #cтили treeview         
        self.configure("mystyle.Treeview", font=("Verdana", 10, "bold"), foreground="black", background="#d6ebff")
 
######################################################################################################################
#----------------------------------------------Проверочные функции --------------------------------------------------#

#функция осуществляет проверку полей где необходимо вводить только цифры и запятые(ещё можно точку) 
def check_entry_settled_amount(P, i, d, amount)->bool:
        """P - это полная последовательность символов
           i - это индекс
           P[-1] - последний введёный символ
           d- управляющий символ(например del или backspace)
        """
        i = int(i)
        # если нажали управляющий символ, то возврат True
        if int(d) == 0:
            return True
        result = re.findall(r"[,]",P)#поиск точки или запятой в последовательности символов(нам нужна только одна точка или запятая)
        if P == "": #обязательное на данный момент условие(02.06.2022) на пустую строку в entry
            return True
        if str.isalpha(P[i]):#нельзя вводить буквы
            return False
        if len(result) > 1:#если мы нашли уже запятую или точку, то больше не даём её ввести
            return False
        elif P[0] == ",": #or P[0] == ",":#запрещаем вводить первыми . или ,
            return False
        elif len(result) == 1 and len(re.split(r"[,]",P)[1]) > 2: #ограничиваем дробную часть до 2-х знаков
            return False
        elif int(i) < int(amount) and (str.isdigit(P[i]) or (P[i]== ",")):# or (P[i]== ",")):#по формату не больше 15 знаков, могут быть только цифры, точка или запятая
            return True
        return False

#для поля entry
def check_entry(P, i, d, amount)->bool:
      # если нажали управляющий символ, то возврат True
    if int(d) == 0:
        return True
    if P =="": #обязательное на данный момент условие(02.06.2022) на пустую строку в entry
        return True
    print(P)
    if len(P) < int(amount) + 1:
        return True
    else:
        return False

    
def check_simple_entry(P, i, d, amount)->bool:
     # если нажали управляющий символ, то возврат True
    if int(d) == 0:
        return True
    if P =="": #обязательное на данный момент условие(02.06.2022) на пустую строку в entry
        return True
    if P[0] == "/": #не может начинаться с символа /
        return False
    if P[int(i)-1] == "/" and P[int(i)] == "/":
        return False
    if len(P) < int(amount) + 1:
        return True
    else:
        return False
    
#функция поиска подстроки (на данный момент 22.07.2022 не используется)
def find_string(string, substring):
       count = 0
       i = -1
       while True:
           i = string.find(substring, i+1)
           if i == -1:
               return count
           count += 1


#для поля help_entry
def check_help_entry(i):
        
        if(int(i) < 30):#длина строки не больше 29 символов
                return True
        else:
                return False


#проверка поля с датой (допускаются только цифры и точка)
def check_date(P, i)->bool:
    if P =="":#обязательное на данный момент условие(02.06.2022) на пустую строку в entry
        return True
    if int(i) < 10 and (str.isdigit(P[-1]) or (P[-1]== ".")):
        return True
    return False

#ввод только больших латинских букв и цифр
def upper_selected_entry(self, selected_entry)->None:
    if(re.findall(r"[a-яА-Я]",selected_entry.get().upper())):
       selected_entry.set(selected_entry.get().upper()[:-1])#пропускаем русские буквы, если идёт ввод руской буквы, то её отсекаем self.entry.get().upper()[:-1]
    else:
        selected_entry.set(selected_entry.get().upper())

#проверка даты(допускается формат(dd.mm.yyyy)    
def validate_date(self, date):
    if self.pattern.match(date.get()):
        print("Ok")
    else:
        print("Некорректна введена дата")

def print_error():
    print("Запрещенный символ")

#------------------------Конец блока проверочных функций -------------------------------------------------------------------#
#############################################################################################################################
#----------------Вспомогательные функции -----------------------------------------------------------------------------------#

def show_advanced_entry(self, check_entry, advanced_entry, row, column):
    if len(check_entry.get()) in range(2): #если мы нажали / и это первый слэш
       advanced_entry.grid(row=row, column=column, padx=10, pady=10, sticky=tk.W)


def hide_advanced_entry(self, check_entry, advanced_entry, event):
    print(check_entry.get())
    if len(check_entry.get()) == 1: #тут сравниваем с 1 т.к. событие наступает раньше чем уменьшение текста
        advanced_entry.grid_forget()


def show_advanced_entry_bic(self, check_entry, advanced_entry, row, column):
    if len(check_entry.get()) in range(2): #если мы нажали / и это первый слэш
       advanced_entry.grid(row=row, column=column, padx=10, pady=10, sticky=tk.W)


def hide_advanced_entry_bic(self, check_entry, advanced_entry, event):
    print(check_entry.get())
    if len(check_entry.get()) == 1: #тут сравниваем с 1 т.к. событие наступает раньше чем уменьшение текста
        advanced_entry.grid_forget()
      
#-----------------------Конец блока вспомогательных функций------------------------------------------------------------------#
##############################################################################################################################
#-----------------------Очистка данных---------------------------------------------------------------------------------------#

def clear_fields():
    tabs.clear_fields()


#-----------------------Загрузка и выгрузка данных---------------------------------------------------------------------------#
#загружаем данные
def download_data():
    #выбор файла отчета
    filetypes = (
        ('text files', '*.txt'),
        ('All files', '*.*')
    )
    
    file_name = filedialog.askopenfilename(
                    title="Файл_мт_103:",
                    initialdir=".",
                    filetypes=filetypes)
    if not file_name:
        return
    data = GetFieldsFromTxt().get_fields_from_txt(file_name)
##    print(data)
    #Очищаем данные
    clear_fields()

    #Загружаем данные
    tabs.set_fields(data)

 
#############################################################################################################################
#сохранение данных
def test_save():
    data_settings = ReaderDBF(path_to_settings).dbf_data[0]
    sender = data_settings.s_kp
    #нужно для загрузки в spfs (у них реализована загрузка, только если есть лишний символ (4 с конца))
    sender_left=sender[:-3]
    sender_center="0"
    sender_rigth=sender[-3:]
    sender="".join([sender_left,sender_center,sender_rigth])
    
    recipient = data_settings.r_kp
    #нужно для загрузки в spfs 
    recipient_left=recipient[:-3]
    recipient_center="0"
    recipient_right=recipient[-3:]
    recipient="".join([recipient_left,recipient_center,recipient_right])
    number = f"{int(data_settings.number):010}"
    my_uuid = str(uuid.uuid4())

    block_1 = "{" +f"1:F01{sender}{number}"+ "}"
    block_2 = "{" +f"2:I103{recipient}N"+ "}"
    block_3 = r"{3:{121:" +f"{my_uuid}"+r"}}"
  
    #Заполнение тела сообщения блок 4
    fields = tabs.get_fields()
    print(fields)
    list_block_4 = []
    #Запись поля 20 (обязательное)
    if fields["field_20"] is None:
        tk.messagebox.showinfo("Ошибка сохранения", "Не заполненно обязательное поле 20:")
        return
    field_20 = f":20:{fields['field_20']}\n"
    list_block_4.append(field_20)

    #Запись поля 23B (обязательное)
    if fields["field_23B"] is None: 
        tk.messagebox.showinfo("Ошибка сохранения", "Не заполненно обязательное поле 23B:")
        return    
    field_23B = f":23B:{fields['field_23B']}\n"
    list_block_4.append(field_23B)


    #Запись поля 23Е
    if not fields['field_23E'] is None:
        print(fields['field_23E'])
        field_23E = ""
        for elem in fields['field_23E']:
            if len(elem) > 1:
                field_23E += f":23E:{elem[0]}{elem[1]}\n"
            else:
                field_23E += f":23E:{elem[0]}\n"
        if field_23E !="":
            list_block_4.append(field_23E)

    #Запись поля 26T
    if not  fields['field_26T'] is None:
        field_26T = f":26T:{fields['field_26T']}\n"
        list_block_4.append(field_26T)

    #Запись поля 32А (обязательное)
    if fields['field_32A'] is None:
        tk.messagebox.showinfo("Ошибка сохранения", "Не заполненно обязательное поле 32A:")
        return
    field_32A = f":32A:{fields['field_32A'][0]}{fields['field_32A'][1]}{fields['field_32A'][2]}\n"
    list_block_4.append(field_32A)

    #Запись поля 33B
    if not fields['field_33B'] is None:
        field_33B = f":33B:{fields['field_33B'][0]}{fields['field_33B'][1]}\n"
        list_block_4.append(field_33B)

    #Запись поля 36
    if not fields['field_36'] is None:
        field_36 = f":36:{fields['field_36']}\n"
        list_block_4.append(field_36)


    #Запись поля 50
    if fields['field_50'] is None:
        tk.messagebox.showinfo("Ошибка сохранения", "Не заполненно обязательное поле 50:")
        return
    field_50 = f":50{fields['field_50'][0]}:"
    for elem in fields['field_50'][1:]:
        if elem !="":
            field_50 += f"{elem}\n"
    list_block_4.append(field_50)

    #Запись поля 52 (обязательное)
    if fields['field_52'] is None:
        tk.messagebox.showinfo("Ошибка сохранения", "Не заполненно обязательное поле 52:")
        return
    if fields['field_52'][1] != "": #вообщем это у нас плавающее поле (здесь по кнопке "/") мы можем добавлять элементы и заново скрывать (но на выходе они зафиксированы(1-буква, 2-счет, 3-бик и т.д) поэтому чтобы если счета нет то подставляем сразу бик
        field_52 = f":52{fields['field_52'][0]}:"
        for elem in fields['field_52'][1:]:
            if elem == "": #пустые пропускаем
                continue
            if elem == fields['field_52'][6] and elem == fields['field_52'][6] != "": # если мы получили информацию из текстового поля бик (там последний элемент адрес через запятую)
                continue #для spfs не будем заполнять эти поля
                addr_list = fields['field_52'][6].split(",")#разделяем адрес
                for el in addr_list:
                    field_52 += f"{el.strip()}\n"
                continue
            field_52 += f"{elem}\n"
    else:
        field_52 = f":52{fields['field_52'][0]}:"
        for elem in fields['field_52'][2:]:
            if elem == "": #пустые пропускаем
                continue
            if elem == fields['field_52'][6] and elem == fields['field_52'][6] != "": # если мы получили информацию из текстового поля бик (там последний элемент адрес через запятую)
                continue #для spfs не будем заполнять эти поля
                addr_list = fields['field_52'][6].split(",")#разделяем адрес
                for el in addr_list:
                    field_52 += f"{el.strip()}\n"
                continue
            field_52 += f"{elem}\n"
    list_block_4.append(field_52)


    #Запись поля 53
    if not fields['field_53'] is None:
        if fields['field_53'][1] != "": #вообщем это у нас плавающее поле (здесь по кнопке "/") мы можем добавлять элементы и заново скрывать (но на выходе они зафиксированы(1-буква, 2-счет, 3-бик и т.д) поэтому чтобы если счета нет то подставляем сразу бик
            field_53 = f":53{fields['field_53'][0]}:"
            for elem in fields['field_53'][1:]:
                if elem == "": #пустые пропускаем
                    continue
                field_53 += f"{elem}\n"
        else:
            field_53 = f":53{fields['field_53'][0]}:"
            for elem in fields['field_53'][2:]:
                if elem == "": #пустые пропускаем
                    continue
                field_53 += f"{elem}\n"
        list_block_4.append(field_53)


    #Запись поля 56
    if not fields['field_56'] is None:
        if fields['field_56'][1] != "": #вообщем это у нас плавающее поле (здесь по кнопке "/") мы можем добавлять элементы и заново скрывать (но на выходе они зафиксированы(1-буква, 2-счет, 3-бик и т.д) поэтому чтобы если счета нет то подставляем сразу бик
            field_56 = f":56{fields['field_56'][0]}:"
            for elem in fields['field_56'][1:]:
                if elem == "": #пустые пропускаем
                    continue
                if elem == fields['field_56'][6] and elem == fields['field_56'][6] != "": # если мы получили информацию из текстового поля бик (там последний элемент адрес через запятую)
                    continue #для spfs не будем заполнять эти поля
                    addr_list = fields['field_56'][6].split(",")#разделяем адрес
                    for el in addr_list:
                        field_56 += f"{el.strip()}\n"
                    continue
                field_56 += f"{elem}\n"
        else:
            field_56 = f":56{fields['field_56'][0]}:"
            for elem in fields['field_56'][2:]:
                if elem == "": #пустые пропускаем
                    continue
                if elem == fields['field_56'][6] and elem == fields['field_56'][6] != "": # если мы получили информацию из текстового поля бик (там последний элемент адрес через запятую)
                    continue #для spfs не будем заполнять эти поля
                    addr_list = fields['field_56'][6].split(",")#разделяем адрес
                    for el in addr_list:
                        field_56 += f"{el.strip()}\n"
                    continue
                field_56 += f"{elem}\n"
        list_block_4.append(field_56)


    #Запись поля 57
    if not fields['field_57'] is None:
        if fields['field_57'][1] != "": #вообщем это у нас плавающее поле (здесь по кнопке "/") мы можем добавлять элементы и заново скрывать (но на выходе они зафиксированы(1-буква, 2-счет, 3-бик и т.д) поэтому чтобы если счета нет то подставляем сразу бик
            field_57 = f":57{fields['field_57'][0]}:"
            for elem in fields['field_57'][1:]:
                if elem == "": #пустые пропускаем
                    continue
                if elem == fields['field_57'][6] and elem == fields['field_57'][6] != "": # если мы получили информацию из текстового поля бик (там последний элемент адрес через запятую)
                    continue #для spfs не будем заполнять эти поля
                    addr_list = fields['field_57'][6].split(",")#разделяем адрес
                    for el in addr_list:
                        field_57 += f"{el.strip()}\n"
                    continue
                field_57 += f"{elem}\n"
        else:
            field_57 = f":57{fields['field_57'][0]}:"
            for elem in fields['field_57'][2:]:
                if elem == "": #пустые пропускаем
                    continue
                if elem == fields['field_57'][6] and elem == fields['field_57'][6] != "": # если мы получили информацию из текстового поля бик (там последний элемент адрес через запятую)
                    continue #для spfs не будем заполнять эти поля
                    addr_list = fields['field_57'][6].split(",")#разделяем адрес
                    for el in addr_list:
                        field_57 += f"{el.strip()}\n"
                    continue
                field_57 += f"{elem}\n"
        list_block_4.append(field_57)
   
   
    #Запись поля 59(обязательное)
    if fields['field_59'] is None:
        tk.messagebox.showinfo("Ошибка сохранения", "Не заполненно обязательное поле 59:")
        return
    if fields['field_59'][1] != "": #вообщем это у нас плавающее поле (здесь по кнопке "/") мы можем добавлять элементы и заново скрывать (но на выходе они зафиксированы(1-буква, 2-счет, 3-бик и т.д) поэтому чтобы если счета нет то подставляем сразу бик
        field_59 = f":59:"
        for elem in fields['field_59'][1:]:
            if elem == "": #пустые пропускаем
                continue
            field_59 += f"{elem}\n"
    else:
        field_59 = f":59:"
        for elem in fields['field_59'][2:]:
            if elem == "": #пустые пропускаем
                continue
            field_59 += f"{elem}\n"
    list_block_4.append(field_59)

    #Запись поля 70
    if not fields['field_70'] is None:
        field_70 = f":70:"
        for elem in fields['field_70']:
            if elem != "":
                field_70 += f"{elem}\n"
        list_block_4.append(field_70)
   
    #Запись поля 71A (обязательное)
    if fields["field_71A"] is None: 
        tk.messagebox.showinfo("Ошибка сохранения", "Не заполненно обязательное поле 23B:")
        return    
    field_71A = f":71A:{fields['field_71A']}\n"
    list_block_4.append(field_71A)


    #Запись поля 71F
    if not fields['field_71F'] is None:
        field_71F = ""
        for elem in fields['field_71F']:
            field_71F += f":71F:{elem[0].strip()}{elem[1]}\n"
        if field_71F !="":
            list_block_4.append(field_71F)

    
    #Запись поля 71G
    if not fields['field_71G'] is None:
        field_71G = f":71G:{fields['field_71G'][0]}{fields['field_71G'][1]}\n"
        list_block_4.append(field_71G)
    
    
    #Запись поля 72
    if not fields['field_72'] is None:
        field_72 = f":72:"
        for elem in fields['field_72']:
            if elem != "":
                field_72 += f"{elem}\n"
        list_block_4.append(field_72)


    #Запись поля 77B
    if not fields['field_77B'] is None:
        field_77B = f":77B:"
        for elem in fields['field_77B']:
            if elem != "":
                field_77B += f"{elem}\n"
        list_block_4.append(field_77B)
    
    
    block_4_start = "{4:\n"
    block_4_end = "-}"
    body_block_4 = ""
    for el in list_block_4:
        body_block_4 += el

    block_4 = block_4_start + body_block_4 + block_4_end
    print(block_4)

    #выбор файла отчета
    try:
        filetypes = (
            ('text files', '*.txt'),
            ('All files', '*.*')
        )

        file= filedialog.asksaveasfile(
                        title="Файл_мт_103:",
                        initialdir=".",
                        filetypes=filetypes,
                        defaultextension=".txt")
        
        file_name = file.name
    except:
        pass
 
 
    try:
        with open(file_name, mode="w") as f:
            f.write(block_1)
            f.write(block_2)
            f.write(block_3)
            f.write(block_4)
    except:
        print("Не удалось открыть файл")
##


def test_save_2():
    data_settings = ReaderDBF(path_to_settings).dbf_data[0]
    sender = data_settings.s_kp
    #нужно для загрузки в spfs 
    sender_left=sender[:-3]
    sender_center="0"
    sender_rigth=sender[-3:]
    sender="".join([sender_left,sender_center,sender_rigth])
    
    recipient = data_settings.r_kp
    #нужно для загрузки в spfs 
    recipient_left=recipient[:-3]
    recipient_center="0"
    recipient_right=recipient[-3:]
    recipient="".join([recipient_left,recipient_center,recipient_right])
    number = f"{int(data_settings.number):010}"
    my_uuid = str(uuid.uuid4())

    block_1 = "{" +f"1:F01{sender}{number}"+ "}"
    block_2 = "{" +f"2:I202{recipient}N"+ "}"
    block_3 = r"{3:{121:" +f"{my_uuid}"+r"}}"
    

    #Заполнение тела сообщения блок 4
    fields = tabs.get_fields()
    print(fields)
    list_block_4 = []
    #Запись поля 20 (обязательное)
    if fields["field_20"] is None:
        tk.messagebox.showinfo("Ошибка сохранения", "Не заполненно обязательное поле 20:")
        return
    field_20 = f":20:{fields['field_20']}\n"
    list_block_4.append(field_20)

    #Запись поля 21 (обязательное)
    if fields["field_21"] is None:
        tk.messagebox.showinfo("Ошибка сохранения", "Не заполненно обязательное поле 20:")
        return
    field_21 = f":21:{fields['field_21']}\n"
    list_block_4.append(field_21)

    #Запись поля 32А (обязательное)
    if fields['field_32A'] is None:
        tk.messagebox.showinfo("Ошибка сохранения", "Не заполненно обязательное поле 32A:")
        return
    field_32A = f":32A:{fields['field_32A'][0]}{fields['field_32A'][1]}{fields['field_32A'][2]}\n"
    list_block_4.append(field_32A)

    #Запись поля 52 (обязательное)
    if fields['field_52'] is None:
        tk.messagebox.showinfo("Ошибка сохранения", "Не заполненно обязательное поле 52:")
        return
    if fields['field_52'][1] != "": #вообщем это у нас плавающее поле (здесь по кнопке "/") мы можем добавлять элементы и заново скрывать (но на выходе они зафиксированы(1-буква, 2-счет, 3-бик и т.д) поэтому чтобы если счета нет то подставляем сразу бик
        field_52 = f":52{fields['field_52'][0]}:"
        for elem in fields['field_52'][1:]:
            if elem == "": #пустые пропускаем
                continue
            if elem == fields['field_52'][6] and elem == fields['field_52'][6] != "": # если мы получили информацию из текстового поля бик (там последний элемент адрес через запятую)
                continue #для spfs не будем заполнять эти поля
                addr_list = fields['field_52'][6].split(",")#разделяем адрес
                for el in addr_list:
                    field_52 += f"{el.strip()}\n"
                continue
            field_52 += f"{elem}\n"
    else:
        field_52 = f":52{fields['field_52'][0]}:"
        for elem in fields['field_52'][2:]:
            if elem == "": #пустые пропускаем
                continue
            if elem == fields['field_52'][6] and elem == fields['field_52'][6] != "": # если мы получили информацию из текстового поля бик (там последний элемент адрес через запятую)
                continue #для spfs не будем заполнять эти поля
                addr_list = fields['field_52'][6].split(",")#разделяем адрес
                for el in addr_list:
                    field_52 += f"{el.strip()}\n"
                continue
            field_52 += f"{elem}\n"
    list_block_4.append(field_52)

    #Запись поля 53
    if not fields['field_53'] is None:
        if fields['field_53'][1] != "": #вообщем это у нас плавающее поле (здесь по кнопке "/") мы можем добавлять элементы и заново скрывать (но на выходе они зафиксированы(1-буква, 2-счет, 3-бик и т.д) поэтому чтобы если счета нет то подставляем сразу бик
            field_53 = f":53{fields['field_53'][0]}:"
            for elem in fields['field_53'][1:]:
                if elem == "": #пустые пропускаем
                    continue
                field_53 += f"{elem}\n"
        else:
            field_53 = f":53{fields['field_53'][0]}:"
            for elem in fields['field_53'][2:]:
                if elem == "": #пустые пропускаем
                    continue
                field_53 += f"{elem}\n"
        list_block_4.append(field_53)

    #Запись поля 56
    if not fields['field_56'] is None:
        if fields['field_56'][1] != "": #вообщем это у нас плавающее поле (здесь по кнопке "/") мы можем добавлять элементы и заново скрывать (но на выходе они зафиксированы(1-буква, 2-счет, 3-бик и т.д) поэтому чтобы если счета нет то подставляем сразу бик
            field_56 = f":56{fields['field_56'][0]}:"
            for elem in fields['field_56'][1:]:
                if elem == "": #пустые пропускаем
                    continue
                if elem == fields['field_56'][6] and elem == fields['field_56'][6] != "": # если мы получили информацию из текстового поля бик (там последний элемент адрес через запятую)
                    continue #для spfs не будем заполнять эти поля
                    addr_list = fields['field_56'][6].split(",")#разделяем адрес
                    for el in addr_list:
                        field_56 += f"{el.strip()}\n"
                    continue
                field_56 += f"{elem}\n"
        else:
            field_56 = f":56{fields['field_56'][0]}:"
            for elem in fields['field_56'][2:]:
                if elem == "": #пустые пропускаем
                    continue
                if elem == fields['field_56'][6] and elem == fields['field_56'][6] != "": # если мы получили информацию из текстового поля бик (там последний элемент адрес через запятую)
                    continue #для spfs не будем заполнять эти поля
                    addr_list = fields['field_56'][6].split(",")#разделяем адрес
                    for el in addr_list:
                        field_56 += f"{el.strip()}\n"
                    continue
                field_56 += f"{elem}\n"
        list_block_4.append(field_56)

    #Запись поля 57
    if not fields['field_57'] is None:
        if fields['field_57'][1] != "": #вообщем это у нас плавающее поле (здесь по кнопке "/") мы можем добавлять элементы и заново скрывать (но на выходе они зафиксированы(1-буква, 2-счет, 3-бик и т.д) поэтому чтобы если счета нет то подставляем сразу бик
            field_57 = f":57{fields['field_57'][0]}:"
            for elem in fields['field_57'][1:]:
                if elem == "": #пустые пропускаем
                    continue
                if elem == fields['field_57'][6] and elem == fields['field_57'][6] != "": # если мы получили информацию из текстового поля бик (там последний элемент адрес через запятую)
                    continue #для spfs не будем заполнять эти поля
                    addr_list = fields['field_57'][6].split(",")#разделяем адрес
                    for el in addr_list:
                        field_57 += f"{el.strip()}\n"
                    continue
                field_57 += f"{elem}\n"
        else:
            field_57 = f":57{fields['field_57'][0]}:"
            for elem in fields['field_57'][2:]:
                if elem == "": #пустые пропускаем
                    continue
                if elem == fields['field_57'][6] and elem == fields['field_57'][6] != "": # если мы получили информацию из текстового поля бик (там последний элемент адрес через запятую)
                    continue #для spfs не будем заполнять эти поля
                    addr_list = fields['field_57'][6].split(",")#разделяем адрес
                    for el in addr_list:
                        field_57 += f"{el.strip()}\n"
                    continue
                field_57 += f"{elem}\n"
        list_block_4.append(field_57)
    
    #Запись поля 58(обязательное)
    if fields['field_58'] is None:
        tk.messagebox.showinfo("Ошибка сохранения", "Не заполненно обязательное поле 58:")
        return
    if not fields['field_58'] is None:
        if fields['field_58'][1] != "": #вообщем это у нас плавающее поле (здесь по кнопке "/") мы можем добавлять элементы и заново скрывать (но на выходе они зафиксированы(1-буква, 2-счет, 3-бик и т.д) поэтому чтобы если счета нет то подставляем сразу бик
            field_58 = f":58{fields['field_58'][0]}:"
            for elem in fields['field_58'][1:]:
                if elem == "": #пустые пропускаем
                    continue
                if elem == fields['field_58'][6] and elem == fields['field_58'][6] != "": # если мы получили информацию из текстового поля бик (там последний элемент адрес через запятую)
                    continue #для spfs не будем заполнять эти поля
                    addr_list = fields['field_58'][6].split(",")#разделяем адрес
                    for el in addr_list:
                        field_58 += f"{el.strip()}\n"
                    continue
                field_58 += f"{elem}\n"
        else:
            field_58 = f":58{fields['field_58'][0]}:"
            for elem in fields['field_58'][2:]:
                if elem == "": #пустые пропускаем
                    continue
                if elem == fields['field_58'][6] and elem == fields['field_58'][6] != "": # если мы получили информацию из текстового поля бик (там последний элемент адрес через запятую)
                    continue #для spfs не будем заполнять эти поля
                    addr_list = fields['field_58'][6].split(",")#разделяем адрес
                    for el in addr_list:
                        field_58 += f"{el.strip()}\n"
                    continue
                field_58 += f"{elem}\n"
        list_block_4.append(field_58)

    
    #Запись поля 72
    if not fields['field_72'] is None:
        field_72 = f":72:"
        for elem in fields['field_72']:
            if elem != "":
                field_72 += f"{elem}\n"
        list_block_4.append(field_72)

    
    block_4_start = "{4:\n"
    block_4_end = "-}"
    body_block_4 = ""
    for el in list_block_4:
        body_block_4 += el

    block_4 = block_4_start + body_block_4 + block_4_end
    print(block_4)

    #выбор файла отчета
    try:
        filetypes = (
            ('text files', '*.txt'),
            ('All files', '*.*')
        )

        file= filedialog.asksaveasfile(
                        title="Файл_мт_103:",
                        initialdir=".",
                        filetypes=filetypes,
                        defaultextension=".txt")
        
        file_name = file.name
    except:
        pass
    
    try:
        with open(file_name, mode="w") as f:
            f.write(block_1)
            f.write(block_2)
            f.write(block_3)
            f.write(block_4)
    except:
        print("Не удалось открыть файл")
##


def test_save_3():
    data_settings = ReaderDBF(path_to_settings).dbf_data[0]
    sender = data_settings.s_kp
    #нужно для загрузки в spfs 
    sender_left=sender[:-3]
    sender_center="0"
    sender_rigth=sender[-3:]
    sender="".join([sender_left,sender_center,sender_rigth])
    
    recipient = data_settings.r_kp
    #нужно для загрузки в spfs 
    recipient_left=recipient[:-3]
    recipient_center="0"
    recipient_right=recipient[-3:]
    recipient="".join([recipient_left,recipient_center,recipient_right])
    number = f"{int(data_settings.number):010}"
    my_uuid = str(uuid.uuid4())

    block_1 = "{" +f"1:F01{sender}{number}"+ "}"
    block_2 = "{" +f"2:I199{recipient}N"+ "}"
    block_3 = r"{3:{121:" +f"{my_uuid}"+r"}}"
    

    #Заполнение тела сообщения блок 4
    fields = tabs.get_fields()
    print(fields)
    list_block_4 = []
    #Запись поля 20 (обязательное)
    if fields["field_20"] is None:
        tk.messagebox.showinfo("Ошибка сохранения", "Не заполненно обязательное поле 20:")
        return
    field_20 = f":20:{fields['field_20']}\n"
    list_block_4.append(field_20)

    #Запись поля 21 (обязательное)
    if fields["field_21"] is None:
        tk.messagebox.showinfo("Ошибка сохранения", "Не заполненно обязательное поле 20:")
        return
    field_21 = f":21:{fields['field_21']}\n"
    list_block_4.append(field_21)

    #Запись поля 79
    if not fields['field_79'] is None:
        field_79 = f":79:"
        for elem in fields['field_79']:
            if elem != "":
                field_79 += f"{elem}\n"
        list_block_4.append(field_79)

    
    block_4_start = "{4:\n"
    block_4_end = "-}"
    body_block_4 = ""
    for el in list_block_4:
        body_block_4 += el

    block_4 = block_4_start + body_block_4 + block_4_end
    print(block_4)

    #выбор файла отчета
    try:
        filetypes = (
            ('text files', '*.txt'),
            ('All files', '*.*')
        )

        file= filedialog.asksaveasfile(
                        title="Файл_мт_199:",
                        initialdir=".",
                        filetypes=filetypes,
                        defaultextension=".txt")
        
        file_name = file.name
    except:
        pass
    
    try:
        with open(file_name, mode="w") as f:
            f.write(block_1)
            f.write(block_2)
            f.write(block_3)
            f.write(block_4)
    except:
        print("Не удалось открыть файл")
##




#-----------------------Конец блока загрузки и выгрузки данных ----------------------------------#
##################################################################################################
def close_main_window():
    app.destroy()

##########################################
#----------------------------------Окно для показа настроек -------------------------------------#

def show_settings():
    new_settings_window = Settings()


class Settings(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.title("Настройки отправки")
        self.geometry("750x170+600+300")
        self.resizable(0,0)
        self.grab_set()
        
        style = Styles(self)

        self.left_main_frame = tk.LabelFrame(self)
        #Отправитель
        self.sender_frame = tk.Frame(self.left_main_frame)
        self.top_kp = ttk.Label(self.sender_frame,
                                        text="Код КП", 
                                        **style.label_top)
        self.top_name = ttk.Label(self.sender_frame,
                                        text="Наименование", 
                                        **style.label_top)
        self.sender_label = ttk.Label(self.sender_frame,
                                        text="Отправитель сообщения:",
                                        **style._label)
        self.sender_name = ttk.Label(self.sender_frame, 
                                        text="Новокиб", wraplength=300,
                                        **style.label)
        self.sender_kp = ttk.Label(self.sender_frame, 
                                        text="Новокиб",
                                         **style.label)
        self.sender_btn = Button(self.sender_frame, text="Выбрать", command=lambda: self.show_table_bic_spfs(self.sender_kp,self.sender_name))

        self.top_kp.grid(row=0,column=1,padx=5, pady=5, sticky=tk.E+tk.W)
        self.top_name.grid(row=0,column=2,padx=5, pady=5, sticky=tk.E+tk.W)
        self.sender_label.grid(row=1,column=0,padx=5, pady=5, sticky=tk.E+tk.W)
        self.sender_kp.grid(row=1,column=1,padx=5, sticky=tk.W)
        self.sender_name.grid(row=1,column=2,padx=5, sticky=tk.W)
        self.sender_btn.grid(row=1,column=3,padx=5, sticky=tk.E)
        self.sender_frame.pack(side=TOP, anchor=tk.N, fill=X, ipady=5)
        #Получатель
        # self.recipient_frame = tk.Frame(self.left_main_frame)       

        self.recipient_label = ttk.Label(self.sender_frame,
                                        text="Получатель сообщения:", 
                                       **style._label)
        self.recipient_name = ttk.Label(self.sender_frame, 
                                        text="Новокиб", wraplength=300,
                                        **style.label)
        self.recipient_kp = ttk.Label(self.sender_frame, 
                                        text="Новокиб",
                                        **style.label)
        self.recipient_btn = Button(self.sender_frame, text="Выбрать", command=lambda: self.show_table_bic_spfs(self.recipient_kp,  self.recipient_name))

        self.recipient_label.grid(row=2,column=0,padx=5, pady=5, sticky=tk.E+tk.W)
        self.recipient_kp.grid(row=2,column=1,padx=5, sticky=tk.W)
        self.recipient_name.grid(row=2,column=2,padx=5, sticky=tk.W)
        self.recipient_btn.grid(row=2,column=3,padx=5, sticky=tk.W)
        # self.recipient_frame.pack(side=TOP, anchor=tk.N, fill=X, ipady=20)
        
        self.label_number = ttk.Label(self.sender_frame,
                                        text="Номер сообщения:", 
                                       **style._label)
        self.number = ttk.Entry(self.sender_frame, **style.settings_entry)
        self.label_number.grid(row=3,column=0,padx=5, pady=5, sticky=tk.E+tk.W)
        self.number.grid(row=3,column=1,padx=5, sticky=tk.W)
        self.save_btn = Button(self.sender_frame, text="Сохранить Настройки", command=self.save_settings)
        self.save_btn.grid(row=4, column=0, padx=5, pady=10, sticky=tk.W)
        self.left_main_frame.pack(anchor=tk.N, side=TOP, fill=X)
        self.init_settings()
        

    def init_settings(self):
        # data_settings = ReaderDBF(path_to_settings).dbf_data[0]
        data_settings = ReaderDBF(path_to_settings).dbf_data[0]
        self.sender_kp.configure(text=data_settings.s_kp)
        self.sender_name.configure(text=data_settings.s_name)
        self.recipient_kp.configure(text=data_settings.r_kp)
        self.recipient_name.configure(text=data_settings.r_name)
        self.number.insert(0,data_settings.number)

    def show_table_bic_spfs(self, _kp, _name):
        SettingsSPFS(self,  _kp, _name)

    def save_settings(self):
        data = {
                "s_kp":self.sender_kp["text"],
                "s_name":self.sender_name["text"],
                "r_kp":self.recipient_kp["text"],
                "r_name":self.recipient_name["text"],
                "date": date.today(),
                "number": self.number.get()
            }

        ExportDBF(path_to_settings).save_dbf(data)
        self.destroy()
       
#----------------------------------Конец окна для показа настроек ------------------------------ #
###################################################################################################
###################################################################################################
###################################################################################################
#-----------------------Окно для показа bic-------------------------------------------------------"
def show_table_bic(self, entry, text):
    new_bic_window = BicWindow(self, entry, text)

class BicWindow(tk.Toplevel):
    def __init__(self, master, entry, text):
        super().__init__(master)
        self.title("Справочник БИК")
        self.geometry("1600x800+100+100")
        self.resizable(0,0)
        self.grab_set()
       
        self.frame = tk.Frame(self)
        style = Styles(self.frame)
        self.entry = entry
        self.text = text

        columns = ("#1","#2","#3","#4","#5","#6","#7")
        self.tree_instruction_code = ttk.Treeview(self.frame, show="headings", columns=columns, height=35)
        self.tree_instruction_code.column("#1", width=70)
        self.tree_instruction_code.column("#2", width=500)
        self.tree_instruction_code.column("#3", width=100)
        self.tree_instruction_code.column("#4", width=100)
        self.tree_instruction_code.column("#5", width=100)
        self.tree_instruction_code.column("#6", width=100)
        self.tree_instruction_code.column("#7", width=100)
        self.tree_instruction_code.heading("#1", text="БИК")
        self.tree_instruction_code.heading("#2", text="Наименование Банка")
        self.tree_instruction_code.heading("#3", text="Город")
        self.tree_instruction_code.heading("#4", text="Адрес_1")
        self.tree_instruction_code.heading("#5", text="Адрес_2")
        self.tree_instruction_code.heading("#6", text="Адрес_3")
        self.tree_instruction_code.heading("#7", text="Адрес_4")
        self.tree_instruction_code.pack(side=LEFT, expand=1, fill=X)
        sb = Scrollbar(self.frame, orient=VERTICAL)
        sb.pack(side=RIGHT, fill=Y)
        self.tree_instruction_code.config(yscrollcommand=sb.set)
        sb.config(command=self.tree_instruction_code.yview)
        bic_list = swift_data#Bic(path_to_bic).bic_list
        for elem in bic_list:
            self.tree_instruction_code.insert("", tk.END, values=(elem.bic,elem.name,
                                                                  elem.city_head,
                                                                  elem.address1,
                                                                  elem.address2,
                                                                  elem.address3,
                                                                  elem.address4))
        self.tree_list = self.tree_instruction_code.get_children()
        #индексируем элементы
        self.dictionary = {}
        for children in self.tree_list:
            self.dictionary.setdefault(children, self.tree_instruction_code.item(children)["values"][0])

        self.tree_instruction_code.bind("<Double-Button-1>", func=lambda event:self.on_treeview_double_click())

        self.search_frame = tk.Frame(self)
        self.search_entry_label = ttk.Label(self.search_frame,text="Поиск по БИК:", style="Heading.TLabel",width=15)
        self.search_entry_bic = tk.Entry(self.search_frame,
                                         **style.entry_search_conf)
        self.search_entry_bic.bind("<Return>",func=lambda event: self.search_bic())
        self.search_entry_bic.bind("<F3>",func=lambda event: self.search_next())
        
        self.search_entry_label.pack(side=LEFT)
        self.search_entry_bic.pack(side=LEFT)
        self.frame.pack(fill=X)
        self.search_frame.pack(fill=X)

    def on_treeview_double_click(self):
        item = self.tree_instruction_code.focus()
        self.values = self.tree_instruction_code.item(item, option="values")
        print(self.values)
        self.fill_bic_information(self.values)
        self.destroy()
          
    def fill_bic_information(self, values):
        self.entry.delete(0, END)
        self.text.delete(1.0, END)
        for elem in values:
            self.entry.insert(0,values[0])
            bic_info_list =[el for el in values[1:] if el != ""]#делаем срез и убираем пустые значения
            string = ",".join(bic_info_list)
            print(elem)
            self.text.insert(1.0,string)
            break
    
    def search_bic(self):
        query = str(self.search_entry_bic.get())
        self.selections=[]
        for key, value in self.dictionary.items():
            if query.lower() in value.lower():
                self.selections.append(key)
                
        if not self.selections is None:
            self.tree_instruction_code.selection_set(self.selections[0]) #устанавливаем курсор на первом элементе
            self.tree_instruction_code.focus()#делаем на нём фокусировку
            self.tree_instruction_code.see(self.selections[0])#выделяем его
            #для дальнейшего поиска (если у нас будут ещё элементы удовлетворяющие условиям) используем итератор
            self.itr = iter(self.selections)#итератор
            self.element = next(self.itr, self.selections[len(self.selections)-1])#устанавливаем курсор на первом элементе        

    #поиск по кнопке далее
    def search_next(self):
        if not self.selections is None:
            self.element = next(self.itr, self.selections[len(self.selections)-1])#получаем следующий элемент
            if(self.element == self.selections[len(self.selections)-1]): 
                self.itr = iter(self.selections) #если дошли до последнего элемента, обнуляем итератор
            self.tree_instruction_code.selection_set(self.element)
            self.tree_instruction_code.focus()
            self.tree_instruction_code.see(self.element)    
    
    def show_window():
        pass


#-----------------------Окно для показа spfs------------------------------------------------------------"
def show_table_bic_spfs(self, entry, text):
    new_bic_window = BicSpfsWindow(self, entry, text)

class BicSpfsWindow(tk.Toplevel):

    def __init__(self, master, entry, text):
        super().__init__(master)
        self.title("Справочник БИК")
        self.geometry("800x800+600+100")
        self.resizable(0,0)
        self.grab_set()
       
        self.frame = tk.Frame(self)
        style = Styles(self.frame)
        self.entry = entry
        self.text = text
        
        
        columns = ("#1","#2")#,"#3","#4","#5","#6","#7")
        self.tree_instruction_code = ttk.Treeview(self.frame, show="headings", columns=columns, height=35)
        self.tree_instruction_code.column("#1", width=150)
        self.tree_instruction_code.column("#2", width=750)
##        self.tree_instruction_code.column("#3", width=100)
##        self.tree_instruction_code.column("#4", width=100)
##        self.tree_instruction_code.column("#5", width=100)
##        self.tree_instruction_code.column("#6", width=100)
##        self.tree_instruction_code.column("#7", width=100)
        self.tree_instruction_code.heading("#1", text="КП")
        self.tree_instruction_code.heading("#2", text="Наименование Банка")
##        self.tree_instruction_code.heading("#3", text="Город")
##        self.tree_instruction_code.heading("#4", text="Адрес_1")
##        self.tree_instruction_code.heading("#5", text="Адрес_2")
##        self.tree_instruction_code.heading("#6", text="Адрес_3")
##        self.tree_instruction_code.heading("#7", text="Адрес_4")
        
        
        sbY = Scrollbar(self.frame, orient=VERTICAL)
        sbY.pack(side=RIGHT, fill=Y)
        self.tree_instruction_code.config(yscrollcommand=sbY.set)
        sbY.config(command=self.tree_instruction_code.yview)
        sbX = Scrollbar(self.frame, orient=HORIZONTAL)
        sbX.pack(side=BOTTOM, fill=X)
        self.tree_instruction_code.config(xscrollcommand=sbX.set)
        sbX.config(command=self.tree_instruction_code.xview)
        self.tree_instruction_code.pack(side=LEFT, expand=1, fill=BOTH, anchor="n")
        # sb = Scrollbar(self.frame, orient=VERTICAL)
        # sb.pack(side=RIGHT, fill=Y)
        # self.tree_instruction_code.config(yscrollcommand=sb.set)
        # sb.config(command=self.tree_instruction_code.yview)
        bic_list = spfs_data #GetSpfsBic().get_fields_from_txt(path_to_bic_spfs)
        for elem in bic_list:
            if elem["КП"] == "":
                continue
            self.tree_instruction_code.insert("", tk.END, values=(elem["КП"],elem["Наименование"]))#,
##                                                                  elem.city_head,
##                                                                  elem.address1,
##                                                                  elem.address2,
##                                                                  elem.address3,
##                                                                  elem.address4))

        self.tree_list = self.tree_instruction_code.get_children()
        #индексируем элементы
        self.dictionary = {}
        for children in self.tree_list:
            self.dictionary.setdefault(children, self.tree_instruction_code.item(children)["values"][1])

        self.tree_instruction_code.bind("<Double-Button-1>", func=lambda event:self.on_treeview_double_click())
        self.search_frame = tk.Frame(self)
        self.search_entry_label = ttk.Label(self.search_frame,text="Поиск по названию:", style="Heading.TLabel",width=17)
        self.search_entry_bic = tk.Entry(self.search_frame,
                                         **style.entry_search_conf)
        self.search_entry_bic.bind("<Return>",func=lambda event: self.search_bic())
        self.search_entry_bic.bind("<F3>",func=lambda event: self.search_next())
        
        self.search_entry_label.pack(side=LEFT)
        self.search_entry_bic.pack(side=LEFT)
        self.frame.pack(fill=X)
        self.search_frame.pack(fill=X)


    def search_bic(self):
        query = str(self.search_entry_bic.get())
        self.selections=[]
        for key, value in self.dictionary.items():
            if query.lower() in value.lower():
                self.selections.append(key)
                
        if not self.selections is None:
            self.tree_instruction_code.selection_set(self.selections[0]) #устанавливаем курсор на первом элементе
            self.tree_instruction_code.focus()#делаем на нём фокусировку
            self.tree_instruction_code.see(self.selections[0])#выделяем его
            #для дальнейшего поиска (если у нас будут ещё элементы удовлетворяющие условиям) используем итератор
            self.itr = iter(self.selections)#итератор
            self.element = next(self.itr, self.selections[len(self.selections)-1])#устанавливаем курсор на первом элементе        

    #поиск по кнопке далее
    def search_next(self):
        if not self.selections is None:
            self.element = next(self.itr, self.selections[len(self.selections)-1])#получаем следующий элемент
            if(self.element == self.selections[len(self.selections)-1]): 
                self.itr = iter(self.selections) #если дошли до последнего элемента, обнуляем итератор
            self.tree_instruction_code.selection_set(self.element)
            self.tree_instruction_code.focus()
            self.tree_instruction_code.see(self.element)          
            
    
    def on_treeview_double_click(self):
        item = self.tree_instruction_code.focus()
        self.values = self.tree_instruction_code.item(item, option="values")
        print(self.values)
        self.fill_bic_information(self.values)
        self.destroy()


    def fill_bic_information(self, values):
        self.entry.delete(0, END)
        self.text.delete(1.0, END)
        for elem in values:
            self.entry.insert(0,values[0])
            bic_info_list =[el for el in values[1:] if el != ""]#делаем срез и убираем пустые значения
            string = ",".join(bic_info_list)
            print(elem)
            self.text.insert(1.0,string)
            break


class SettingsSPFS(BicSpfsWindow):
    def __init__(self, master, label_name, label_kp):
        super().__init__(master, label_name, label_kp)
        self.label_name = label_name
        self.label_kp = label_kp

    def fill_bic_information(self, values):
        for elem in values:
            self.label_name.config(text=values[0].strip())
            # self.entry.insert(0,values[0])
            bic_info_list =[el for el in values[1:] if el != ""]#делаем срез и убираем пустые значения
            string = ",".join(bic_info_list)
            print(elem)
            # self.text.insert(1.0,string)
            self.label_kp.config(text=string)
            break
        

def create_code_word_window(self):
    new_code_word_window =CodeWordWindow(self)

class CodeWordWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Кодовые слова")
        self.geometry("800x370+600+200")
        self.resizable(0,0)
        self.grab_set()
        self.frame = tk.Frame(self)
        style = Styles(self.frame)
        self.tree = master.tree_instruction_code
        
        columns = ("#1","#2")
        self.tree_instruction_code = ttk.Treeview(self.frame, show="headings", columns=columns, height=15)
        self.tree_instruction_code.column("#1", width=50)
        self.tree_instruction_code.column("#2", width=900)
        self.tree_instruction_code.heading("#1", text="Код")
        self.tree_instruction_code.heading("#2", text="Описание")
        sbY = Scrollbar(self.frame, orient=VERTICAL)
        sbY.pack(side=RIGHT, fill=Y)
        self.tree_instruction_code.config(yscrollcommand=sbY.set)
        sbY.config(command=self.tree_instruction_code.yview)
        sbX = Scrollbar(self.frame, orient=HORIZONTAL)
        sbX.pack(side=BOTTOM, fill=X)
        self.tree_instruction_code.config(xscrollcommand=sbX.set)
        sbX.config(command=self.tree_instruction_code.xview)
        codes = InstructionCodes(path_to_codes).currency_list
        
        list_of_codes = []
        index = 0
        for item in codes:
            if item[0] == "SDVA":
                index = 0
                list_of_codes.append([index,item])
            elif item[0] == "INTC":
                index = 1
                list_of_codes.append([index,item])
            elif item[0] == "CORT":
                index = 2
                list_of_codes.append([index,item])
            elif item[0] == "BONL":
                index = 3
                list_of_codes.append([index,item])
            elif item[0] == "HOLD/":
                index = 4
                list_of_codes.append([index,item])
            elif item[0] == "CHQB":
                index = 5
                list_of_codes.append([index,item])
            elif item[0] == "PHOB/":
                index = 6
                list_of_codes.append([index,item])
            elif item[0] == "TELB/":
                index = 7
                list_of_codes.append([index,item])
            elif item[0] == "PHON/":
                index = 8
                list_of_codes.append([index,item])
            elif item[0] == "TELE/":
                index = 9
                list_of_codes.append([index,item])
            elif item[0] == "PHOI/":
                index = 10
                list_of_codes.append([index,item])
            elif item[0] == "TELI/":
                index = 11
                list_of_codes.append([index,item])
            else:
                continue
        list_of_codes.sort()    
        print(list_of_codes)   
        for elem in list_of_codes:
           index = elem[0]
           values = elem[1] 
           self.tree_instruction_code.insert("", tk.END, values=elem[1], tags=index)
           self.tree_instruction_code.tag_bind(index, "<<TreeviewSelect>>", self.item_clicked)
           self.tree_instruction_code.tag_bind(index, "<Double-Button-1>", self.item_double_clicked)
           self.tree_instruction_code.tag_bind(index, "<Return>", self.item_double_clicked)

        self.tree_instruction_code.pack(side=LEFT, expand=1, fill=BOTH, anchor="n")
        self.frame.pack(fill=BOTH)
        self.info_frame = tk.Frame(self)
        self.selected_info_entry = tk.StringVar()
        vcmd_selected_info_entry = (self.register(check_help_entry),"%i")
        self.info_entry_label = ttk.Label(self.info_frame,text="Дополнительные данные", style="Heading.TLabel", width=21)
        self.info_entry = tk.Entry(self.info_frame,
                                               validate="key",
                                               validatecommand= vcmd_selected_info_entry,
                                               invalidcommand=print_error,
                                               textvariable=self.selected_info_entry,
                                              **style.entry_conf)
        self.info_entry.configure(state="disabled")
        self.info_entry.bind("<Return>", self.item_double_clicked)
        self.info_entry_label.pack(side=LEFT, padx=10)
        self.info_entry.pack(side=LEFT)
        self.info_frame.pack(fill=BOTH)
        
        
    def item_clicked(self, event):
        self.info_entry.delete(0, END)
        self.item = self.tree_instruction_code.focus()
        self.values = self.tree_instruction_code.item(self.item, option="values")
        if not self.values[0].endswith("/"):
            self.info_entry.configure(state="disabled")
        else:
            self.info_entry.configure(state="normal")

    def item_double_clicked(self, event):
        self.tree.insert("", tk.END, values=(self.values[0],self.info_entry.get()))
        self.destroy()


def create_country_window(self, entry):
    new_country_window = CountryWindow(self, entry)
    

class CountryWindow(tk.Toplevel):
    def __init__(self, master, entry):
        super().__init__(master)
        self.title("Кодовые слова")
        self.geometry("400x400+300+100")
        self.resizable(0,0)
        self.grab_set()
        self.frame = tk.Frame(self)
        style = Styles(self.frame)
        self.entry = entry
        columns = ("#1","#2")
        self.num = 0 #переменная для поиска , чтобы по F3 шагали к следующему элементу (по другому пока не придумал)
        self.tree_instruction_code = ttk.Treeview(self.frame, show="headings", columns=columns, height=15)
        self.tree_instruction_code.column("#1", width=10)
        self.tree_instruction_code.column("#2", width=200)
        self.tree_instruction_code.heading("#1", text="Код")
        self.tree_instruction_code.heading("#2", text="Cтрана")
        sb = Scrollbar(self.frame, orient=VERTICAL)
        sb.pack(side=RIGHT, fill=Y)
        self.tree_instruction_code.config(yscrollcommand=sb.set)
        sb.config(command=self.tree_instruction_code.yview)

        countries = Countries(path_to_country).country_list
        for index, item in enumerate(countries):
            self.tree_instruction_code.insert("", tk.END, values=item, tags=index)
            self.tree_instruction_code.tag_bind(index, "<<TreeviewSelect>>", self.item_clicked)

        self.tree_instruction_code.pack(side=LEFT, expand=1, fill=X)

        self.search_frame = tk.Frame(self)
        
        
        self.search_entry_label = ttk.Label(self.search_frame,text="Поиск по стране:", style="Heading.TLabel", width=15)
        self.search_entry_country = tk.Entry(self.search_frame,
                                             
                                              **style.entry_search_conf)
        self.search_entry_country.bind("<Return>",func=lambda event: self.search_country())
        self.search_entry_country.bind("<F3>",func=lambda event: self.search_next())
        self.search_entry_label.pack(side=LEFT)
        self.search_entry_country.pack(side=LEFT)

        self.frame.pack(fill=BOTH)
        self.search_frame.pack(fill=BOTH)
            

    def item_clicked(self,event):
        for selection in self.tree_instruction_code.selection():
            item = self.tree_instruction_code.item(selection)
            code = item["values"][0]
            self.entry.delete(0,END)
            self.entry.insert(0,f"/BENEFRES/{code}//")
            self.destroy()

    
    #функция ищет элемент по назначаемой кнопке
    def search_country(self):
          query = str(self.search_entry_country.get()) # 
          
        #   print(query)
          self.selections = []
          #проверяем есть ли строки в treeview удовлетворяющие условиям поиска
          for child in self.tree_instruction_code.get_children(): 
              if query.lower() in str("".join(self.tree_instruction_code.item(child)["values"][1])).lower():
                  self.selections.append(child) #если есть до добавляем их в массив
##                  self.tree_instruction_code.selection_set(selections)
##                  self.tree_instruction_code.focus()
##                  self.tree_instruction_code.see(child)
##                  return
##          print(self.selections)

          if not self.selections is None:
              self.tree_instruction_code.selection_set(self.selections[0]) #устанавливаем курсор на первом элементе
              self.tree_instruction_code.focus()#делаем на нём фокусировку
              self.tree_instruction_code.see(self.selections[0])#выделяем его
              #здесь для дальнейшего поиска после установки на первом элементе создаём итератор и сдвигаем значение на 1, чтобы по кнопке даллее уже сразу выделялся следующий элемент
              self.itr = iter(self.selections)#итератор
              self.element = next(self.itr, self.selections[len(self.selections)-1])#сдвиг на следующий элемент

          
    #поиск по кнопке далее
    def search_next(self):
        if not self.selections is None:
            self.element = next(self.itr, self.selections[len(self.selections)-1])#получаем текущий элемент
            if(self.element == self.selections[len(self.selections)-1]):
                self.itr = iter(self.selections)
            self.tree_instruction_code.selection_set(self.element)
            self.tree_instruction_code.focus()
            self.tree_instruction_code.see(self.element)
        
    
#---------------------------------------------------------------------------------------------------------------------------------------------------#
                
def create_simple_help_window(self, entry, check):
    new_simple_help_window = SimpleHelpCodeWindow(self,entry,check)

class SimpleHelpCodeWindow(tk.Toplevel):
    def __init__(self, master, entry, check):
                super().__init__(master)
                self.title("Кодовые слова")
                self.geometry("400x150+300+100")
                self.resizable(0,0)
                self.grab_set()
                   
                self.frame = tk.Frame(self)
                style = Styles(self.frame)
                self.entry = entry

                code_words = []
                code_words.append(("//","начало строки(кроме первой)"))
                code_words.append(("/ACC/","инструкции для банка(указанного в поле 57)"))
                code_words.append(("/IBK/","банк посредник"))
                code_words.append(("/INS/","банк отправитель"))
                code_words.append(("/OUROUR/","гарантия получения полной суммы платежа"))
                columns = ("#1","#2")
                self.tree_instruction_code = ttk.Treeview(self.frame, show="headings", columns=columns, height=35)
                self.tree_instruction_code.column("#1", width=10)
                self.tree_instruction_code.column("#2", width=200)
                self.tree_instruction_code.heading("#1", text="Код")
                self.tree_instruction_code.heading("#2", text="Описание")

                for index, item in enumerate(code_words):
                    self.tree_instruction_code.insert("", tk.END, values=item, tags=index)
                    if check == True:
                        self.tree_instruction_code.tag_configure(index, background="grey")
                        check = False
                        continue
                    self.tree_instruction_code.tag_bind(index, "<<TreeviewSelect>>", self.item_clicked)

                self.tree_instruction_code.pack(side=LEFT, expand=1, fill=X)
                self.frame.pack(fill=X)

    def item_clicked(self,event):
        for selection in self.tree_instruction_code.selection():
            item = self.tree_instruction_code.item(selection)
            code = item["values"][0]
            self.entry.delete(0,END)
            self.entry.insert(0,code)
            self.destroy()
        
        
        
    

#---------вспомогательное окно, для заполнения treeview--------#
##def create_help_window(self):
##        new_help_window = HelpWindow(self)
class HelpWindow(tk.Toplevel):

        def __init__(self, master):
                super().__init__(master)
                self.title("Ok")
                self.geometry("600x100+600+300")
                self.resizable(0,0)
                self.grab_set()
                self.selected_help_entry = tk.StringVar()
##                vcmd_selected_help_entry = (self.register(check_entry_settled_amount),"%P","%i")
                vcmd_selected_help_entry = (self.register(check_help_entry),"%i")
                
                
                self.tree = master.tree_instruction_code
                self.frame = tk.Frame(self)
                style = Styles(self.frame)
                self.label_combo_currency_top = ttk.Label(self.frame, text="Кодовое слово", style="Heading.TLabel", width=22)
                self.combo_currency = ttk.Combobox(self.frame, values=InstructionCodes(path_to_codes).currency_list, state="readonly", **style.help_combobox_conf)
                self.combo_currency.bind("<<ComboboxSelected>>", self.callback_combobox)
                self.label_combo_currency_top.grid(row=0, column=0, padx=10, sticky=tk.W + tk.E)
                self.combo_currency.grid(row=1,column=0, padx=10, sticky=tk.W + tk.E)

                self.label_entry = ttk.Label(self.frame, text="Информация", style="Heading.TLabel", width=22)
                self.help_entry = ttk.Entry(self.frame,
                                      validate="key",
                                      validatecommand= vcmd_selected_help_entry,
                                      invalidcommand=print_error,
                                      textvariable=self.selected_help_entry,
                                      **style.help_combobox_conf)
                
                self.label_entry.grid(row=2, column=0, padx=10, sticky=tk.W + tk.E)
                self.help_entry.grid(row=3, column=0, padx=10, pady=5, sticky=tk.W + tk.E)

                self.protocol("WM_DELETE_WINDOW", self.on_closing)

                self.frame.pack(side=LEFT, fill=X)
                
        def on_closing(self ):
            combo_list = self.combo_currency.get().split("-")
            self.tree.insert("",tk.END,values=(combo_list[0],self.help_entry.get()))
            self.destroy()

        def callback_combobox(self, event):
             combo_head = self.combo_currency.get().split("-")[0].strip()
             print(combo_head.endswith("/"))
             if not combo_head.endswith("/"):
                 self.help_entry.configure(state="disabled")
             else:
                 self.help_entry.configure(state="enabled")
            
class HelpWindowWithAmount(HelpWindow):
     def __init__(self, master):
         super().__init__(master)
         style = Styles(self.frame)
         self.geometry("220x100+600+600")
         self.vcmd_selected_help_entry = (self.register(check_entry_settled_amount),"%P", "%i", "%d", 13)
         self.label_combo_currency_top.config(text="Валюта")
         self.label_entry.config(text="Cумма")
         self.combo_currency.config(width=5)
         self.help_entry.config(width=5)
         self.help_entry.config(validatecommand=self.vcmd_selected_help_entry)
         self.combo_currency.config(values=Currency(path_to_currency_file).currency_list)

     def on_closing(self ):
         combo_list = self.combo_currency.get().split("-")
         if self.help_entry.get() == "" and (self.combo_currency.get() == "" ):
             self.destroy()
         elif self.help_entry.get() == "":
             tk.messagebox.showinfo("Ошибка","Заполните сумму")
         elif self.combo_currency.get() == "":
             tk.messagebox.showinfo("Ошибка", "Выберите валюту")
         else:
             self.tree.insert("",tk.END,values=(combo_list[0],self.help_entry.get()))
             self.destroy()

     def callback_combobox(self, event):
             pass
         
#---------вспомогательное окно, для заполнения treeview  конец--------#               
 
class SimpleEntry(tk.Frame):
    def get_field(self):
        if self.entry_1.get() == "" and self.entry_2.get() == "" and self.entry_3.get() == "" and self.entry_4.get() == "": # ни одно из полей не заполнено
                return None
        entry_field = []
        entry_field.append(self.combobox.get())
        entry_field.append(self.entry_1.get())
        entry_field.append(self.entry_2.get())
        entry_field.append(self.entry_3.get())
        entry_field.append(self.entry_4.get())
        return entry_field
    

    def clear_field(self):
        self.entry_1.delete(0, END)
        self.entry_2.delete(0, END)
        self.entry_3.delete(0, END)
        self.entry_4.delete(0, END)


    def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master, padx=10, pady=10)
        self.frame = tk.Frame(master)
        style = Styles(self.frame)
        self.frame.pack(side=side, anchor=anchor)

        self.selected_entry_1 = tk.StringVar()
        self.selected_entry_1.trace("w", lambda x, y, z : upper_selected_entry(self, self.selected_entry_1))
        self.selected_entry_2 = tk.StringVar()
        self.selected_entry_2.trace("w", lambda x, y, z : upper_selected_entry(self, self.selected_entry_2))
        self.selected_entry_3 = tk.StringVar()
        self.selected_entry_3.trace("w", lambda x, y, z : upper_selected_entry(self, self.selected_entry_3))
        self.selected_entry_4 = tk.StringVar()
        self.selected_entry_4.trace("w", lambda x, y, z : upper_selected_entry(self, self.selected_entry_4))

        
        self.vcmd_customer_entry = (self.register(check_entry),"%P","%i", "%d", 35) 

        self.label_top = ttk.Label(self.frame, text=label_top_text, style="Heading.TLabel")
        self.label = ttk.Label(self.frame, text=label_text, style="Mandatory.TLabel")
        self.combobox = ttk.Combobox(self.frame, values=["K","F"], state="readonly", width=5)
        self.combobox.current(1)
        self.entry_1 = ttk.Entry(self.frame,
                                           validate="key",
                                           validatecommand=self.vcmd_customer_entry,
                                           textvariable=self.selected_entry_1,  
                                           **style.entry_amount_conf_big)
        self.entry_2 = ttk.Entry(self.frame,
                                           validate="key",
                                           validatecommand=self.vcmd_customer_entry,
                                           textvariable=self.selected_entry_2,
                                           **style.entry_amount_conf_big)
        self.entry_3 = ttk.Entry(self.frame,
                                           validate="key",
                                           validatecommand=self.vcmd_customer_entry,
                                           textvariable=self.selected_entry_3,
                                           **style.entry_amount_conf_big)
        self.entry_4 = ttk.Entry(self.frame,
                                           validate="key",
                                           validatecommand=self.vcmd_customer_entry,
                                           textvariable=self.selected_entry_4,
                                           **style.entry_amount_conf_big)

        self.label_top.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.label.grid(row=1, column=0, padx=5, sticky=tk.W)
        self.combobox.grid(row=1, column=1, padx=5,  sticky=tk.W)
        self.entry_1.grid(row=1, column=2, padx=10, pady=5, sticky=tk.W)
        self.entry_2.grid(row=2, column=2, padx=10, pady=5, sticky=tk.W)
        self.entry_3.grid(row=3, column=2, padx=10, pady=5, sticky=tk.W)
        self.entry_4.grid(row=4, column=2, padx=10, pady=5, sticky=tk.W)

        
        
class MainEntry(tk.Frame):

    def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master, padx=10, pady=10)
        self.frame = tk.Frame(master)
        style = Styles(self.frame)
        widget_var = tk.StringVar()
        vcmd_customer_entry = (self.register(check_entry),"%P", "%i", "%d", 34)
        self.frame.pack(side=side, anchor=anchor)
        self.label_top = ttk.Label(self.frame, text=label_top_text,  style="Heading.TLabel")
        self.label = ttk.Label(self.frame, text=label_text, style="Heading.TLabel")
        self.combobox = ttk.Combobox(self.frame, values=["A","D"], state="readonly", width=5)
        self.combobox.current(1)
        
        self.entry_1 = ttk.Entry(self.frame, validate="key",
                                             validatecommand=vcmd_customer_entry,
                                             **style.entry_amount_conf_big)
        self.entry_2 = ttk.Entry(self.frame, validate="key",
                                             validatecommand=vcmd_customer_entry,
                                             **style.entry_amount_conf_big)
        self.entry_3 = ttk.Entry(self.frame, validate="key",
                                             validatecommand=vcmd_customer_entry,
                                             **style.entry_amount_conf_big)
        self.entry_4 = ttk.Entry(self.frame, validate="key",
                                             validatecommand=vcmd_customer_entry,
                                             **style.entry_amount_conf_big)

        self.entry_5 = ttk.Entry(self.frame, validate="key",
                                             validatecommand=vcmd_customer_entry,
                                             **style.entry_amount_conf_big)
        
        self.entry_1.bind("/", self.show_advanced_entry)
        self.entry_1.bind("<BackSpace>", self.hide_advanced_entry)
        self.entry_1.bind("<Delete>", self.hide_advanced_entry_delete)
        
        self.label_top.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W+tk.S)
        self.label.grid(row=1, column=0, padx=5, sticky=tk.E)
        self.combobox.grid(row=1, column=1, padx=5,  sticky=tk.W)
        self.entry_1.grid(row=1, column=2, padx=10, pady=5, sticky=tk.W)
        self.entry_2.grid(row=2, column=2, padx=10, pady=5, sticky=tk.W)
        self.entry_3.grid(row=3, column=2, padx=10, pady=5, sticky=tk.W)
        self.entry_4.grid(row=4, column=2, padx=10, pady=5, sticky=tk.W)
        self.entry_5.grid(row=5, column=2, padx=10, pady=5, sticky=tk.W)

        self.entry_2.grid_forget()

    def show_advanced_entry(self,event):
        if int(self.entry_1.index("insert")) == 0:
            self.entry_2.grid(row=2, column=2, padx=10, pady=5, sticky=tk.W)

    def hide_advanced_entry(self, event):
        count = self.find_string(self.entry_1.get(), "/")
        if  int(self.entry_1.index("insert")) == 1 and count == 1 and self.entry_1.get()[0] == "/" and len(self.entry_1.get()) > 1: #алгоритм такой(может потом можно сократить) смотрим где курсор, смотрим чтобы / было одним и смотрим чтобы ещё были какие то знаки
            self.entry_2.delete(0,END)
            self.entry_2.grid_forget()
        elif len(self.entry_1.get()) == 1 and self.entry_1.get()[0] == "/" and int(self.entry_1.index("insert")) == 1:# здесь смотрим , что / у нас в поле только один
            self.entry_2.delete(0,END)
            self.entry_3.delete(0,END)
            self.entry_4.delete(0,END)
            self.entry_5.delete(0,END)
            self.entry_2.grid_forget()
        
        if len(self.entry_1.get()) == 1 and self.entry_1.get() == "/": #тут сравниваем с 1 т.к. событие наступает раньше чем уменьшение текста
            self.entry_2.grid_forget()
            self.entry_1.delete(0,END)
            self.entry_2.delete(0,END)
            self.entry_3.delete(0,END)
            self.entry_4.delete(0,END)
            self.entry_5.delete(0,END)

    
    def hide_advanced_entry_delete(self, event):
        count = self.find_string(self.entry_1.get(), "/")
        if  int(self.entry_1.index("insert")) == 0 and count == 1 and self.entry_1.get()[0] == "/" and len(self.entry_1.get()) > 1: #алгоритм такой(может потом можно сократить) смотрим где курсор, смотрим чтобы / было одним и смотрим чтобы ещё были какие то знаки
            self.entry_2.delete(0,END)
            self.entry_2.grid_forget()
        elif int(self.entry_1.index("insert")) == 0 and len(self.entry_1.get()) == 1 and count == 1 :# здесь смотрим , что / у нас в поле только один
            self.entry_2.delete(0,END)
            self.entry_3.delete(0,END)
            self.entry_4.delete(0,END)
            self.entry_5.delete(0,END)
            self.entry_2.grid_forget()
            

    def find_string(self, string, substring):
        count = 0
        i = -1
        while True:
            i = string.find(substring, i+1)
            if i == -1:
                return count
            count += 1


    def get_field(self):
        entry_field = []
        entry_field.append(self.combobox.get())
        if len(self.entry_2.get()) == 0:
            if self.entry_1.get() == "" and self.entry_3.get() == "" and self.entry_4.get() == "" and self.entry_5.get() == "": # ни одно из полей не заполнено
                return None
            entry_field.append("")
            entry_field.append(self.entry_1.get())
            entry_field.append(self.entry_3.get())
            entry_field.append(self.entry_4.get())
            entry_field.append(self.entry_5.get())
            return entry_field

        if self.entry_1.get() == "" and self.entry_2.get() == "" and self.entry_3.get() == "" and self.entry_4.get() == "" and self.entry_5.get() == "": # ни одно из полей не заполнено
            return None
        entry_field.append(self.entry_1.get())
        entry_field.append(self.entry_2.get())
        entry_field.append(self.entry_3.get())
        entry_field.append(self.entry_4.get())
        entry_field.append(self.entry_5.get())
        return entry_field


    def set_field(self, data, letter):
##        entry_2 = False
        self.entry_2.grid(row=2, column=2, padx=10, pady=5, sticky=tk.W)
        if letter == "B":
            self.combobox.current(0)
        
##        for index, value in enumerate(data):
##            if index == 0:
##                if (value.startswith("/"):#проверяем первое поле (есть ли у нас номер счета)
##                    self.entry_1.insert(0, value)
##                    self.entry_2.grid(row=2, column=2, padx=10, pady=5, sticky=tk.W)
##                    entry_2 =  True #если у нас есть номер счета то делаем активным self.entry_2  
##            elif index == 1 and entry_2:
##                self.entry_2.insert(0, value)
##            elif index == 1 and not entry_2:
##                self.entry_3.insert(0, value)
##            elif index == 2 and entry_2:
##                self.entry_3.insert(0, value)
##            elif index == 2 and not entry_2:
##                self.entry_4.insert(0, value)    
##            elif index == 3 and entry_2::
##                self.entry_3.insert(0, value)
        
        for index, value in enumerate(data):
            if index == 0:
                self.entry_1.insert(0, value)
            elif index == 1:
                self.entry_2.insert(0, value)
            elif index == 2:
                self.entry_3.insert(0, value)
            elif index == 3:
                self.entry_4.insert(0, value)
            elif index == 4:
                self.entry_5.insert(0, value)

    def clear_field(self):
        self.entry_1.delete(0,END)
        self.entry_2.delete(0,END)
        self.entry_3.delete(0,END)
        self.entry_4.delete(0,END)
        self.entry_5.delete(0,END)
        self.entry_2.grid_forget()


class EntryBic(tk.Frame):
    def select_combobox(self, event):
        self.entry_2.grid_forget()
        self.entry_1.delete(0,END)
        self.entry_2.delete(0,END)
        self.entry_3.delete(0,END)
        self.entry_4.delete(0,END)
        self.entry_5.delete(0,END)
        self.bic_text_area.delete(1.0,END)
        if  self.combobox.get() == "D":
            self.callback_hide_bic(event)
            self.callback_combo_show(event)
        elif self.combobox.get() == "A":
            self.callback_combo_hide(event)
            self.callback_show_bic(event)

    def callback_hide_bic(self, event):
        self.bic_button.grid_forget()
        self.bic_text_area.grid_forget()


    def callback_show_bic(self, event):
        self.bic_button.grid(row=3, column=1, padx=5, sticky=tk.W + tk.E)
        self.bic_text_area.grid(row=3, rowspan=4, column=2, padx=10, sticky=tk.W + tk.E)
        
        
    def callback_combo_show(self, event):
        self.entry_3.grid(row=3, column=2, padx=10, pady=5, sticky=tk.W)
        self.entry_4.grid(row=4, column=2, padx=10, pady=5, sticky=tk.W)
        self.entry_5.grid(row=5, column=2, padx=10, pady=5, sticky=tk.W)
        print("OK")


    def callback_combo_hide(self, event):
        self.entry_2.grid_forget()
        self.entry_3.grid_forget()
        self.entry_4.grid_forget()
        self.entry_5.grid_forget()


    def show_advanced_entry(self,event):
        if int(self.entry_1.index("insert")) == 0:
            self.entry_2.insert(0,self.entry_1.get())
            self.entry_1.delete(0,END)
            self.entry_2.grid(row=2, column=2, padx=10, pady=5, sticky=tk.W)


    def hide_advanced_entry_backspace(self, event):
        count = self.find_string(self.entry_1.get(), "/")
        if  int(self.entry_1.index("insert")) == 1 and count == 1 and self.entry_1.get()[0] == "/" and len(self.entry_1.get()) > 1: #алгоритм такой(может потом можно сократить) смотрим где курсор, смотрим чтобы / было одним и смотрим чтобы ещё были какие то знаки
            self.entry_2.delete(0,END)
            self.entry_2.grid_forget()
        elif len(self.entry_1.get()) == 1 and self.entry_1.get()[0] == "/" and int(self.entry_1.index("insert")) == 1:# здесь смотрим , что / у нас в поле только один
            self.entry_2.delete(0,END)
            self.entry_3.delete(0,END)
            self.entry_4.delete(0,END)
            self.entry_5.delete(0,END)
            self.entry_2.grid_forget()
            self.bic_text_area.delete(1.0,END)


    def hide_advanced_entry_delete(self, event):
        count = self.find_string(self.entry_1.get(), "/")
        if  int(self.entry_1.index("insert")) == 0 and count == 1 and self.entry_1.get()[0] == "/" and len(self.entry_1.get()) > 1: #алгоритм такой(может потом можно сократить) смотрим где курсор, смотрим чтобы / было одним и смотрим чтобы ещё были какие то знаки
            self.entry_2.delete(0,END)
            self.entry_2.grid_forget()
        elif self.entry_1.get()[0] == "/" and len(self.entry_1.get()) == 1 and int(self.entry_1.index("insert")) == 0:# здесь смотрим , что / у нас в поле только один
            self.entry_2.delete(0,END)
            self.entry_3.delete(0,END)
            self.entry_4.delete(0,END)
            self.entry_5.delete(0,END)
            self.entry_2.grid_forget()
            self.bic_text_area.delete(1.0,END)


    def find_string(self, string, substring):
        count = 0
        i = -1
        while True:
            i = string.find(substring, i+1)
            if i == -1:
                return count
            count += 1


    def show_bic(self):
        if len(self.entry_1.get()) >= 1 and self.entry_1.get()[0] == "/":
            show_table_bic(self,  self.entry_2, self.bic_text_area)
        else:
            show_table_bic(self,  self.entry_1, self.bic_text_area)

    def show_table_bic_spfs(self):
        if len(self.entry_1.get()) >= 1 and self.entry_1.get()[0] == "/":
            show_table_bic_spfs(self,  self.entry_2, self.bic_text_area)
        else:
            show_table_bic_spfs(self,  self.entry_1, self.bic_text_area)


    


    def clear_field(self):
        self.entry_1.delete(0,END)
        self.entry_2.delete(0,END)
        self.entry_3.delete(0,END)
        self.entry_4.delete(0,END)
        self.entry_5.delete(0,END)
        self.bic_text_area.delete(1.0,END)
        self.entry_2.grid_forget()
    


    def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master, padx=10, pady=10)
        self.frame = tk.Frame(master)
        style = Styles(self.frame)
        widget_var = tk.StringVar()
        vcmd_customer_entry = (self.register(check_entry),"%P", "%i", "%d", 34)
        self.frame.pack(side=side, anchor=anchor)
        self.label_top = ttk.Label(self.frame, text=label_top_text,  style="Heading.TLabel")
        self.label = ttk.Label(self.frame, text=label_text, style="Heading.TLabel")
        self.combobox = ttk.Combobox(self.frame, values=["A","D"], state="readonly", width=5)
        self.combobox.current(0)
        self.combobox.bind("<<ComboboxSelected>>", self.select_combobox)

        self.entry_1 = ttk.Entry(self.frame, validate="key",
                                             validatecommand=vcmd_customer_entry,
                                             **style.entry_amount_conf_big)
        self.entry_2 = ttk.Entry(self.frame, validate="key",
                                             validatecommand=vcmd_customer_entry,
                                             **style.entry_amount_conf_big)
        self.entry_3 = ttk.Entry(self.frame, validate="key",
                                             validatecommand=vcmd_customer_entry,
                                             **style.entry_amount_conf_big)
        self.entry_4 = ttk.Entry(self.frame, validate="key",
                                             validatecommand=vcmd_customer_entry,
                                             **style.entry_amount_conf_big)

        self.entry_5 = ttk.Entry(self.frame, validate="key",
                                             validatecommand=vcmd_customer_entry,
                                             **style.entry_amount_conf_big)
        

        self.bic_button = Button(self.frame, text="БИК", command=lambda : show_table_bic(self,  self.entry_1, self.bic_text_area))#self.show_table_bic_spfs)#lambda : show_table_bic(self,  self.entry_1, self.bic_text_area))
        self.bic_text_area= Text(self.frame, width=25, height=5, **style.text_conf)


        self.entry_1.bind("/", self.show_advanced_entry)
        self.entry_1.bind("<BackSpace>", self.hide_advanced_entry_backspace)
        self.entry_1.bind("<Delete>", self.hide_advanced_entry_delete)
        
        self.label_top.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W+tk.S)
        self.label.grid(row=1, column=0, padx=5, sticky=tk.E)
        self.combobox.grid(row=1, column=1, padx=5,  sticky=tk.W)
        self.entry_1.grid(row=1, column=2, padx=10, pady=5, sticky=tk.W)
        self.entry_2.grid(row=2, column=2, padx=10, pady=5, sticky=tk.W)
        self.entry_3.grid(row=3, column=2, padx=10, pady=5, sticky=tk.W)
        self.entry_4.grid(row=4, column=2, padx=10, pady=5, sticky=tk.W)
        self.entry_5.grid(row=5, column=2, padx=10, pady=5, sticky=tk.W)

        self.entry_2.grid_forget()

        self.callback_combo_hide(None)
        self.callback_show_bic(None)


    def get_field(self):
        bic_entry_field = []
        bic_entry_field.append(self.combobox.get())
        #здесь логика такая, чтобы у нас в выходном массиве позиции не менялись(то есть 1-combobox , 2 счет, 3-бик), т.к. у нас одна строка скрывается, то порядок нарушается    
        if len(self.entry_2.get()) == 0:
            if self.entry_1.get() == "" and self.entry_3.get() == "" and self.entry_4.get() == "" and self.entry_5.get() == "" and self.bic_text_area.get("1.0", "end-1c") == "": # ни одно из полей не заполнено
                return None
            bic_entry_field.append("")
            bic_entry_field.append(self.entry_1.get())
            bic_entry_field.append(self.entry_3.get())
            bic_entry_field.append(self.entry_4.get())
            bic_entry_field.append(self.entry_5.get())
            bic_entry_field.append(self.bic_text_area.get("1.0", "end-1c"))
            return bic_entry_field

        if self.entry_1.get() == "" and self.entry_2.get() == "" and self.entry_3.get() == "" and self.entry_4.get() == "" and self.entry_5.get() == "" and self.bic_text_area.get("1.0", "end-1c") == "": # ни одно из полей не заполнено
                return None    
        bic_entry_field.append(self.entry_1.get())
        bic_entry_field.append(self.entry_2.get())
        bic_entry_field.append(self.entry_3.get())
        bic_entry_field.append(self.entry_4.get())
        bic_entry_field.append(self.entry_5.get())
        bic_entry_field.append(self.bic_text_area.get("1.0", "end-1c"))
        return bic_entry_field

    def set_field_spfs(self, data, letter):
        
        if letter == "D":
            self.combobox.current(1)
            self.callback_combo_show(None)
            self.callback_hide_bic(None)
            if data[0].startswith("/"):
                self.entry_2.grid(row=2, column=2, padx=10, pady=5, sticky=tk.W)
                for index, value in enumerate(data):
                    if index == 0:
                        self.entry_1.insert(0, value)
                    elif index == 1:
                         self.entry_2.insert(0, value)
                    elif index == 2:
                         self.entry_3.insert(0, value)
                    elif index == 3:
                         self.entry_4.insert(0, value)
                    elif index == 4:
                         self.entry_5.insert(0, value)
            else:
                for index, value in enumerate(data):
                    if index == 0:
                        self.entry_1.insert(0, value)
                    elif index == 1:
                         self.entry_3.insert(0, value)
                    elif index == 2:
                         self.entry_4.insert(0, value)
                    elif index == 3:
                         self.entry_5.insert(0, value)
        if letter == "A":
            self.combobox.current(0)
            self.callback_combo_hide(None)
            self.callback_show_bic(None)
            address = ""
            if data[0].startswith("/"):
                self.entry_2.grid(row=2, column=2, padx=10, pady=5, sticky=tk.W)
                for index, value in enumerate(data):
                    if index == 0:
                        self.entry_1.insert(0, value)
                    elif index == 1:
                         self.entry_2.insert(0, value)
                         for elem in spfs_data:
                            if value ==  elem["КП"]:
                                address = elem["Наименование"]

                        #  for elem in spfs_data:


                    # else:
                    #     address += value + ","
                address = address.strip(",")
                self.bic_text_area.insert(1.0, address)

            else:
                for index, value in enumerate(data):
                    if index == 0:
                        self.entry_1.insert(0, value)
                        for elem in spfs_data:
                            if value ==  elem["КП"]:
                                address = elem["Наименование"]
                    # else:
                    #      address += value + ","
                address = address.strip(",")
                self.bic_text_area.insert(1.0, address)
    
    def set_field(self, data, letter):
        if letter == "D":
            self.combobox.current(1)
            self.callback_hide_bic(None)
            self.callback_combo_show(None)
            if data[0].startswith("/"):
                self.entry_2.grid(row=2, column=2, padx=10, pady=5, sticky=tk.W)
                for index, value in enumerate(data):
                    if index == 0:
                        self.entry_1.insert(0, value)
                    elif index == 1:
                         self.entry_2.insert(0, value)
                    elif index == 2:
                         self.entry_3.insert(0, value)
                    elif index == 3:
                         self.entry_4.insert(0, value)
                    elif index == 4:
                         self.entry_5.insert(0, value)
            else:
                for index, value in enumerate(data):
                    if index == 0:
                        self.entry_1.insert(0, value)
                    elif index == 1:
                         self.entry_3.insert(0, value)
                    elif index == 2:
                         self.entry_4.insert(0, value)
                    elif index == 3:
                         self.entry_5.insert(0, value)
        if letter == "A":
            self.combobox.current(0)
            self.callback_combo_hide(None)
            self.callback_show_bic(None)
            address = ""
            if data[0].startswith("/"):
                self.entry_2.grid(row=2, column=2, padx=10, pady=5, sticky=tk.W)
                for index, value in enumerate(data):
                    if index == 0:
                        self.entry_1.insert(0, value)
                    elif index == 1:
                         self.entry_2.insert(0, value)
                    else:
                         address += value + ","
                address = address.strip(",")
                self.bic_text_area.insert(1.0, address)

            else:
                for index, value in enumerate(data):
                    if index == 0:
                        self.entry_1.insert(0, value)
                    else:
                         address += value + ","
                address = address.strip(",")
                self.bic_text_area.insert(1.0, address)


class CurrencyWidget(tk.Frame):
    def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master, padx=10, pady=10)
        self.frame = tk.Frame(master)
        style = Styles(self.frame)
        self.entry_instructed_amount = tk.StringVar()
        vcmd_entry_instructed_amount = (self.register(check_entry_settled_amount),"%P","%i","%d",15)
        self.frame.pack(side=side, anchor=anchor, ipadx=0, pady=5)

        self.label_combo_currency_top = ttk.Label(self.frame, text=label_top_text, style="Heading.TLabel")
        self.label_combo_currency = ttk.Label(self.frame, text=label_text, style="Heading.TLabel")
        self.combo_currency = ttk.Combobox(self.frame, values=Currency(path_to_currency_file).currency_list, state="readonly", **style.combobox_conf)
        self.label_instructed_amount = ttk.Label(self.frame, text="Сумма", style="Heading.TLabel")
        self.instructed_amount = ttk.Entry(self.frame,
                                        validate="key",
                                        validatecommand=vcmd_entry_instructed_amount,
                                        textvariable=self.entry_instructed_amount,
                                        **style.entry_amount_conf)

        self.label_combo_currency_top.grid(row=0, column=1, sticky=tk.W)
        self.label_combo_currency.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W )
        self.combo_currency.grid(row=1,column=1, padx=0, sticky=tk.W + tk.E)
        self.label_instructed_amount.grid(row=0,column=2, padx=10, sticky=tk.N+tk.W)
        self.instructed_amount.grid(row=1,column=2, padx=10,  sticky=tk.W + tk.E)

    def get_field(self):
        field_list = []
        if self.combo_currency.get() != "":
            cur = str(self.combo_currency.get().split("-")[0]).strip()
        else:
            return None
        if self.instructed_amount.get() != "":            
            amount = str(self.instructed_amount.get()).strip()
        else:
            return None
        field_list.append(cur)
        field_list.append(amount)

        return field_list

    def set_field(self, data):
        value = data[0]
        currency = value[0:3]
        amount = value[3:]
        for index, elem in enumerate(self.combo_currency["values"]):
            if elem.startswith(currency):
                self.combo_currency.current(index)
                break
        self.instructed_amount.insert(0, amount)

    def clear_field(self):
        self.combo_currency.set("")
        self.instructed_amount.delete(0, END)


class WindowWidget(tk.Frame):

    def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master, padx=10, pady=10)
        self.frame = tk.Frame(master)
        style = Styles(self.frame)
        self.frame.pack(side=TOP, anchor=tk.W, pady=5, padx=45)

        columns = ("#1","#2")
        self.tree_instruction_code_top = ttk.Label(self.frame, text="{} {}".format(label_top_text,label_text), style="Heading.TLabel")
        self.tree_instruction_code = ttk.Treeview(self.frame, show="tree", columns=columns, height=10, style="mystyle.Treeview")
        self.tree_instruction_code.column("#0", width=0, stretch=NO)
        self.tree_instruction_code.column("#1", width=70, stretch=NO)
        self.tree_instruction_code.column("#2", width=440, stretch=NO)
        self.tree_instruction_code_top.grid(row=0, column=1, padx=10, ipady=5, sticky=tk.W+tk.S)
        self.tree_instruction_code.grid(row=1,column=1, padx=10, columnspan=3,rowspan=3, sticky=tk.W)

        self.button_frame = tk.Frame(master, padx=45)
        self.instruction_code_button_add = Button(self.button_frame, text="Добавить", command= lambda: HelpWindowWithAmount(self))
        self.instruction_code_button_add.grid(row=0, column=1, sticky=tk.W, pady=10, padx=10 )

        self.instruction_code_button_del = Button(self.button_frame, text="Удалить", command=self.del_line)
        self.instruction_code_button_del.grid(row=0, column=2, sticky=tk.W, pady=10 )
        self.button_frame.pack(side=TOP,anchor=tk.W)

        
    def get_field(self):
##        if self.entry_1.get() == "" and self.entry_2.get() == "" and self.entry_3.get() == "" and self.entry_4.get() == "" and self.entry_5.get() == "" and self.bic_text_area.get("1.0", "end-1c") == "": # ни одно из полей не заполнено
##                return None
        selections = []
        for child in self.tree_instruction_code.get_children():
            selections.append(self.tree_instruction_code.item(child)["values"])
        if selections != []:
            return selections

    def set_field(self, data):
        for elem in data:
            self.values = elem.split("/")
##            print(value)
            if len(self.values) == 1:
                self.tree_instruction_code.insert("", tk.END, values=(self.values[0]))
            else:
                self.tree_instruction_code.insert("", tk.END, values=(self.values[0] + "/" ,self.values[1]))
            

    def add_line(self):
        self.tree_instruction_code.insert("", tk.END, values=(self.enter.get(),))

    def del_line(self):
        item = self.tree_instruction_code.focus()
        self.tree_instruction_code.delete(item)

    def clear_field(self):
        for child in self.tree_instruction_code.get_children():
            self.tree_instruction_code.delete(child)
        
#------------------------------Поля формы ---------------------------------------------------------------#

class Field_20(tk.Frame):
    
    def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master)
        self.frame = tk.Frame(master, padx=5, pady=5)
        self.frame.pack(side=side, anchor=anchor)
        style = Styles(self.frame)
        self.selected_entry = tk.StringVar()
        self.selected_entry.trace("w", lambda x, y, z : upper_selected_entry(self, self.selected_entry))
        vcmd_entry = (self.register(check_simple_entry),"%P", "%i", "%d", 20)
        self.label_top = ttk.Label(self.frame, text=label_top_text, style="Heading.TLabel")
        self.label = ttk.Label(self.frame, text= label_text, style="Mandatory.TLabel")
        self.entry = ttk.Entry(self.frame, validate="key",
                                      validatecommand=vcmd_entry,
                                      invalidcommand=print_error,
                                      textvariable=self.selected_entry,
                                      **style.combobox_conf)
        self.label_top.grid(row=0, column=1, sticky=tk.W)
        self.label.grid(row=1, column=0, pady=5, padx=5, sticky=tk.E)
        self.entry.grid(row=1, column=1, pady=5, sticky=tk.W + tk.E)

    def get_field(self):
        if len(self.entry.get()) == 0:
            
            return None
        field_20 = self.entry.get()
        return field_20

    def set_field(self,data):
        value = data[0]
        self.entry.insert(0,value)

    def clear_field(self):
        self.entry.delete(0,END)

class Field_21(Field_20):
    def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master, label_top_text, label_text, side, anchor)


class Field_23B(tk.Frame):
    def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master)
        self.frame = tk.Frame(master, padx=5, pady=5)
        self.frame.pack(side=side, anchor=anchor)
        style = Styles(self.frame)

        self.top_label_combo_bank_operation = ttk.Label(self.frame, text=label_top_text, style="Heading.TLabel")
        self.label_combo_bank_operation = ttk.Label(self.frame, text=label_text, style="Mandatory.TLabel")
        self.combo_bank_operation = ttk.Combobox(self.frame, values=["CRED"], state="readonly", **style.combobox_conf)
        self.combo_bank_operation.config(width=5)
        self.top_label_combo_bank_operation.grid(row=0,column=1, padx=10, sticky=tk.W)
        self.label_combo_bank_operation.grid(row=1,column=0, sticky=tk.W)
        self.combo_bank_operation.grid(row=1,column=1, padx=10, sticky=tk.W)
        
    def get_field(self):
        if self.combo_bank_operation.get() != "":
            return self.combo_bank_operation.get().upper()

    def set_field(self,data):
        value = data[0]
        if value == "CRED":
            self.combo_bank_operation.current(0)
            
    def clear_field(self):
        self.combo_bank_operation.set("")

       
class Field_23E(WindowWidget):
    def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master, label_top_text, label_text, side, anchor)
        self.instruction_code_button_add.configure(command=lambda: create_code_word_window(self))
        self.frame.configure(padx=5)
        self.button_frame.configure(padx=50)


class Field_26T(tk.Frame):
    
    def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master, padx=10, pady=10)
        self.frame = tk.Frame(master)
        style = Styles(self.frame)
        self.frame.pack(side=side, anchor=anchor, pady=5, padx=15)
        self.selected_entry = tk.StringVar()
        self.selected_entry.trace("w", lambda x, y, z : upper_selected_entry(self, self.selected_entry))
        vcmd_entry_instructed_amount = (self.register(check_entry),"%P","%i", "%d", 3)

        self.label_transaction_type_code = ttk.Label(self.frame, text=":26T:", style="Heading.TLabel")  
        self.label_transaction_type_code_top = ttk.Label(self.frame, text="Код типа сделки", style="Heading.TLabel")
        self.entry = ttk.Entry(self.frame,
                                        validate="key",
                                        validatecommand=vcmd_entry_instructed_amount,
                                        textvariable=self.selected_entry,
                                        **style.entry_amount_conf_small)
        self.label_transaction_type_code_top.grid(row=0,column=1, padx=5, sticky=tk.N+tk.W)
        self.label_transaction_type_code.grid(row=1,column=0, padx=0, sticky=tk.N+tk.W)
        self.entry.grid(row=1,column=1, padx=5, sticky=tk.W)


    def get_field(self):
        if self.entry.get() != "":
            return self.entry.get()
        
    def set_field(self,data):
        value = data[0]
        self.entry.insert(0, value)
        
    def clear_field(self):
        self.entry.delete(0,END)


class Field_32A(tk.Frame):
    
    def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master)
        self.frame = tk.Frame(master, padx=5, pady=5)
        self.frame.pack(side=side, anchor=anchor)
        style = Styles(self.frame)
        self.selected_date = tk.StringVar()
        self.entry_settled_amount = tk.StringVar()
        self.pattern = re.compile(r"\d{2}.\d{2}.\d{4}")
        vcmd_entry = (self.register(check_entry),"%P","%i",16)
        vcmd_date = (self.register(check_date),"%P","%i")
        vcmd_entry_settled_amount = (self.register(check_entry_settled_amount),"%P","%i","%d",15)
        

        ttk.Separator(self.frame,orient=VERTICAL).grid(row=1, column=0, ipady=10, padx=10)

        self.label_date_top = ttk.Label(self.frame, text =label_top_text, style="Heading.TLabel")
        self.label_date = ttk.Label(self.frame, text=label_text, style="Mandatory.TLabel")
        self.entry_date = ttk.Entry(self.frame, validate="key",
                                      validatecommand=vcmd_date,
                                      invalidcommand=print_error,
                                      textvariable=self.selected_date,
                                      **style.date_entry_conf)
        self.entry_date.bind("<FocusOut>", lambda event, self=self, date=self.entry_date : validate_date(self, date))
        self.button_date = ttk.Button(self.frame, width=3, text="...", command= lambda: get_date(self.selected_date))

        self.label_date_top.grid(row=0,column=2, sticky=tk.W)
        self.label_date.grid(row=1, column=1, pady=5, sticky=tk.W)
        self.entry_date.grid(row=1, column=2, pady=5, sticky=tk.W)
        self.button_date.grid(row=1, column=3, sticky=tk.W)

        self.label_combo_currency = ttk.Label(self.frame, text="Валюта перевода", style="Heading.TLabel", width=22)
        self.combo_currency = ttk.Combobox(self.frame, values=Currency(path_to_currency_file).currency_list, state="readonly", **style.combobox_conf)
        self.label_combo_currency.grid(row=0, column=4, padx=30, sticky=tk.W + tk.E)
        self.combo_currency.grid(row=1,column=4, padx=30, sticky=tk.W + tk.E)


        self.label_settled_amount = ttk.Label(self.frame, text="Сумма", style="Heading.TLabel")
        self.settled_amount = ttk.Entry(self.frame,
                                        validate="key",
                                        validatecommand=vcmd_entry_settled_amount,
                                        textvariable=self.entry_settled_amount,
                                        **style.entry_amount_conf)

        self.label_settled_amount.grid(row=0,column=5, padx=0, sticky=tk.N+tk.W)
        self.settled_amount.grid(row=1,column=5, padx=0, sticky=tk.W + tk.E)

        def get_date(selected_date):
            cd = CalendarDialog(self)
            result = cd.result
            if not result is None:
                selected_date.set(result.strftime("%d.%m.%Y"))
           
            
    def get_field(self):
        field_32 = []
        if len(self.entry_date.get()) == 0 or len(self.combo_currency.get()) == 0 or len(self.settled_amount.get()) == 0:
            return None
        date_list =  self.entry_date.get().split(".")
        area_32_date = str("".join([date_list[2][-2:],date_list[1],date_list[0]])).strip()
        field_32.append(area_32_date)
        area_32_cur = str(self.combo_currency.get().split("-")[0]).strip()
        field_32.append(area_32_cur)
        area_32_amount = str(self.settled_amount.get()).strip()
        field_32.append(area_32_amount)
        return field_32
    

    def set_field(self, data):
        value = data[0]
        print(value)
        year = "20" +value[:2]
        month = value[2:4]
        day = value[4:6]
        date = ".".join([day,month,year])
        currency = value[6:9]
        amount = value[9:]
        for index, elem in enumerate(self.combo_currency["values"]):
            if elem.startswith(currency):
                self.combo_currency.current(index)
                break
        self.settled_amount.insert(0, amount)
        self.entry_date.insert(0, date)
        

    def clear_field(self):
        self.entry_date.delete(0, END)
        self.combo_currency.set("")
        self.settled_amount.delete(0, END)
        

class Field_33B(CurrencyWidget):
    def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master, label_top_text, label_text, side, anchor)
       

class Field_36(tk.Frame):

    def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master)
        self.frame = tk.Frame(master, padx=5, pady=5)
        self.frame.pack(side=side, anchor=anchor, padx=15)
        style = Styles(self.frame)
        self.exchange_rate = tk.StringVar()
        vcmd_exchange_rate = (self.register(check_entry_settled_amount),"%P","%i","%d",13)
        self.label_exchange_rate_top = ttk.Label(self.frame, text=label_top_text, style="Heading.TLabel")
        self.label_exchange_rate = ttk.Label(self.frame, text=label_text, style="Heading.TLabel")
        self.exchange_rate = ttk.Entry(self.frame,
                                        validate="key",
                                        validatecommand=vcmd_exchange_rate,
                                        textvariable=self.exchange_rate,
                                        **style.entry_amount_conf)

        self.label_exchange_rate_top.grid(row=0, column=1, padx=5, ipady=5, sticky=tk.W+tk.N)
        self.label_exchange_rate.grid(row=1,column=0,padx=5, sticky=tk.W+tk.N)
        self.exchange_rate.grid(row=1,column=1, padx=0, sticky=tk.W+tk.N)
        

    def get_field(self):
        if self.exchange_rate.get() != "":
            return self.exchange_rate.get()
        

    def set_field(self,data):
        value = data[0]
        self.exchange_rate.insert(0, value)


    def clear_field(self):
        self.exchange_rate.delete(0, END)


class Field_50(SimpleEntry):
    
    def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master, label_top_text, label_text, side, anchor)
        self.label.config(style="Mandatory.TLabel")
        style = Styles(self.frame)
        self.selected_entry_5 = tk.StringVar()
        self.selected_entry_5.trace("w", lambda x, y, z : upper_selected_entry(self, self.selected_entry_5))
        
        self.entry_5 = ttk.Entry(self.frame,
                                           validate="key",
                                           validatecommand=self.vcmd_customer_entry,
                                           textvariable=self.selected_entry_5,
                                           **style.entry_amount_conf_big)
        self.entry_5.grid(row=5, column=2, padx=10, pady=5, sticky=tk.W)

    def get_field(self):
        
        field_50 = []
        field_50.append(self.combobox.get())
        
        if self.entry_1.get() == "" and self.entry_2.get() == "" and self.entry_3.get() == "" and self.entry_4.get() == "" and self.entry_5.get() == "": # ни одно из полей не заполнено
            return None

        field_50.append(self.entry_1.get())
        field_50.append(self.entry_2.get())
        field_50.append(self.entry_3.get())
        field_50.append(self.entry_4.get())
        field_50.append(self.entry_5.get())

        return field_50

    def set_field(self, data, letter):
        if letter == "K":
            self.combobox.current(0)
        elif letter == "F":
            self.combobox.current(1)
        for index, value in enumerate(data):
            if index == 0:
                self.entry_1.insert(0, value)
            elif index == 1:
                self.entry_2.insert(0, value)
            elif index == 2:
                self.entry_3.insert(0, value)
            elif index == 3:
                self.entry_4.insert(0, value)
            elif index == 4:
                self.entry_5.insert(0, value)
                

    def clear_field(self):
        super().clear_field()#вызываем метод родительского класса
        self.entry_5.delete(0, END)


class Field_52(EntryBic):

    def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master, label_top_text, label_text, side, anchor)
        self.label.config(style="Mandatory.TLabel")

class Field_53(MainEntry):
    def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master, label_top_text, label_text, side, anchor)
        self.combobox.config(values=["B"])
        self.combobox.current(0)
        self.entry_1.insert(0,"/")
        self.entry_2.grid(row=2, column=2, padx=10, pady=5, sticky=tk.W)


class Field_56(EntryBic):
     def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master, label_top_text, label_text, side, anchor)


class Field_57(EntryBic):
     def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master, label_top_text, label_text, side, anchor)


class Field_58(EntryBic):
     def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master, label_top_text, label_text, side, anchor)
        self.label.config(style="Mandatory.TLabel")
        
        
class Field_59(MainEntry):
    def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master, label_top_text, label_text, side, anchor)
        self.label.config(style="Mandatory.TLabel")
        self.combobox.config(values=[""], state="disabled")
        self.combobox.current(0)


class Field_70(SimpleEntry):
    def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master, label_top_text, label_text, side, anchor)
        
        self.label.config(style="Heading.TLabel")
        self.combobox.grid_forget()

    def get_field(self):
        if self.entry_1.get() == "" and self.entry_2.get() == "" and self.entry_3.get() == "" and self.entry_4.get() == "": # ни одно из полей не заполнено
                return None
        entry_field = []
        entry_field.append(self.entry_1.get())
        entry_field.append(self.entry_2.get())
        entry_field.append(self.entry_3.get())
        entry_field.append(self.entry_4.get())
        return entry_field

    def set_field(self, data):
        for index, value in enumerate(data):
            if index == 0:
                self.entry_1.insert(0, value)
            elif index == 1:
                self.entry_2.insert(0, value)
            elif index == 2:
                self.entry_3.insert(0, value)
            elif index == 3:
                self.entry_4.insert(0, value)

class Field_71A(tk.Frame):
    def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master, padx=10, pady=10)
        self.frame = tk.Frame(master)
        style = Styles(self.frame)
        self.frame.pack(side=side, anchor=anchor, ipadx=195, pady=5)
        self.label_top = ttk.Label(self.frame, text=label_top_text,  style="Heading.TLabel")
        self.label = ttk.Label(self.frame, text=label_text, style="Mandatory.TLabel")
        self.combobox = ttk.Combobox(self.frame, 
                                    values=["OUR","BEN","SHA"], state="readonly", **style.combobox_conf)
        self.combobox.config(width=5)

        self.label_top.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.S)
        self.label.grid(row=1, column=0, padx=5, sticky=tk.E)
        self.combobox.grid(row=1, column=1, padx=5,  sticky=tk.W)
        
        
    def get_field(self):
        if self.combobox.get() == "":
            tk.messagebox.showinfo("Ошибка сохранения", "Не заполненно обязательное поле 71А:")
            return
        return self.combobox.get()
    

    def set_field(self,data):
        
        for value in data:
            if value == "OUR":
                self.combobox.current(0)
            elif value == "BEN":
                self.combobox.current(1)
            elif value == "SHA":
                self.combobox.current(2)

    def clear_field(self):
        self.combobox.set("")

    
        
class Field_71F(WindowWidget):
    def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master, label_top_text, label_text, side, anchor)
        self.tree_instruction_code.column("#2", width=300, stretch=NO)

    def set_field(self, data):
        for elem in data:
            currency = re.search("\D+", elem)
            amoutn = elem[currency.end():]
            self.tree_instruction_code.insert("", tk.END, values=(currency[0] ,amoutn))


class Field_71G(CurrencyWidget):
    def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master, label_top_text, label_text, side, anchor)
        self.frame.pack(side=side, anchor=anchor, ipadx=60, pady=5)
        

class Field_72(tk.Frame):
    def get_field(self):
        if self.entry_1.get() == "" and self.entry_2.get() == "" \
           and self.entry_3.get() == "" and self.entry_4.get() == "" and self.entry_5.get() == "" and self.entry_6.get() == "": # ни одно из полей не заполнено
                return None
        field_72 = []
        field_72.append(self.entry_1.get())
        field_72.append(self.entry_2.get())
        field_72.append(self.entry_3.get())
        field_72.append(self.entry_4.get())
        field_72.append(self.entry_5.get())
        field_72.append(self.entry_6.get())
        return field_72

    def set_field(self, data):
        for index, value in enumerate(data):
            if index == 0:
                self.entry_1.insert(0, value)
            elif index == 1:
                self.entry_2.insert(0, value)
            elif index == 2:
                self.entry_3.insert(0, value)
            elif index == 3:
                self.entry_4.insert(0, value)
            elif index == 4:
                self.entry_5.insert(0, value)
            elif index == 5:
                self.entry_6.insert(0, value)
    
    def show_code(self):
        current_entry = self.focus_get()
        if str(current_entry) == str(self.entry_1):
            create_simple_help_window(self, current_entry, True)
        elif str(current_entry) == str(self.entry_2):
            create_simple_help_window(self, current_entry, False)
        elif str(current_entry) == str(self.entry_3):
            create_simple_help_window(self, current_entry, False)
        elif str(current_entry) == str(self.entry_4):
            create_simple_help_window(self, current_entry, False)
        elif str(current_entry) == str(self.entry_5):
            create_simple_help_window(self, current_entry, False)
        elif str(current_entry) == str(self.entry_6):
            create_simple_help_window(self, current_entry, False)
        else:
            current_entry = self.entry_1
            create_simple_help_window(self, current_entry, True)
            

    def clear_field(self):
        self.entry_1.delete(0, END)
        self.entry_2.delete(0, END)
        self.entry_3.delete(0, END)
        self.entry_4.delete(0, END)
        self.entry_5.delete(0, END)
        self.entry_6.delete(0, END)
        
        


    def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master, padx=10, pady=10)
        self.frame = tk.Frame(master)
        style = Styles(self.frame)
        widget_var = tk.StringVar()
        vcmd_customer_entry = (self.register(check_entry),"%P","%i","%d",35)
        self.frame.pack(side=side, anchor=anchor)
        self.label_top = ttk.Label(self.frame, text=label_top_text,  style="Heading.TLabel")
        self.label = ttk.Label(self.frame, text=label_text, style="Heading.TLabel")
        self.entry_1 = ttk.Entry(self.frame, validate="key",
                                             name="entry_1",
                                             validatecommand=vcmd_customer_entry,
                                             **style.entry_amount_conf_big)
        self.entry_2 = ttk.Entry(self.frame, validate="key",
                                             name="entry_2",
                                             validatecommand=vcmd_customer_entry,
                                             **style.entry_amount_conf_big)
        self.entry_3 = ttk.Entry(self.frame, validate="key",
                                             name="entry_3",
                                             validatecommand=vcmd_customer_entry,
                                             **style.entry_amount_conf_big)
        self.entry_4 = ttk.Entry(self.frame, validate="key",
                                             name="entry_4",
                                             validatecommand=vcmd_customer_entry,
                                             **style.entry_amount_conf_big)

        self.entry_5 = ttk.Entry(self.frame, validate="key",
                                             name="entry_5",
                                             validatecommand=vcmd_customer_entry,
                                             **style.entry_amount_conf_big)

        self.entry_6 = ttk.Entry(self.frame, validate="key",
                                             name="entry_6",
                                             validatecommand=vcmd_customer_entry,
                                             **style.entry_amount_conf_big)

        self.bic_button = Button(self.frame, text="Код",width=5, height=2, command=self.show_code)

        self.label_top.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W+tk.S)
        self.label.grid(row=1, column=0, padx=5, sticky=tk.E)
        self.bic_button.grid(row=2, column=0, rowspan=2, padx=5, sticky=tk.E)
        self.entry_1.grid(row=1, column=2, padx=10, pady=5, sticky=tk.W)
        self.entry_2.grid(row=2, column=2, padx=10, pady=5, sticky=tk.W)
        self.entry_3.grid(row=3, column=2, padx=10, pady=5, sticky=tk.W)
        self.entry_4.grid(row=4, column=2, padx=10, pady=5, sticky=tk.W)
        self.entry_5.grid(row=5, column=2, padx=10, pady=5, sticky=tk.W)
        self.entry_6.grid(row=6, column=2, padx=10, pady=5, sticky=tk.W)


class Field_77B(tk.Frame):
    def get_field(self):
        if self.entry_1.get() == "" and self.entry_2.get() == "" and self.entry_3.get() == "": # ни одно из полей не заполнено
                return None
        field_77 = []
        field_77.append(self.entry_1.get())
        field_77.append(self.entry_2.get())
        field_77.append(self.entry_3.get())
        return field_77

    def set_field(self, data):
        for index, value in enumerate(data):
            if index == 0:
                self.entry_1.insert(0, value)
            elif index == 1:
                self.entry_2.insert(0, value)
            elif index == 2:
                self.entry_3.insert(0, value)

    def clear_field(self):
        self.entry_1.delete(0, END)
        self.entry_2.delete(0, END)
        self.entry_3.delete(0, END)
        
           

    
    def show_country(self):
         current_entry = self.focus_get()
         if str(current_entry) == str(self.entry_1):
             create_country_window(self, current_entry)
         elif str(current_entry) == str(self.entry_2):
             create_country_window(self, current_entry)
         elif str(current_entry) == str(self.entry_3):
             create_country_window(self, current_entry)
         else:
             current_entry = self.entry_1
             create_country_window(self, current_entry)    
    
    def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master, padx=10, pady=10)
        self.frame = tk.Frame(master)
        style = Styles(self.frame)
        widget_var = tk.StringVar()
        vcmd_customer_entry = (self.register(check_entry),"%P","%i", "%d", 35)
        self.frame.pack(side=side, anchor=anchor)
        self.label_top = ttk.Label(self.frame, text=label_top_text,  style="Heading.TLabel")
        self.label = ttk.Label(self.frame, text=label_text, style="Heading.TLabel")
        self.entry_1 = ttk.Entry(self.frame, validate="key",
                                             name="entry_1",
                                 
                                             validatecommand=vcmd_customer_entry,
                                             **style.entry_amount_conf_big)
        self.entry_2 = ttk.Entry(self.frame, validate="key",
                                             name="entry_2",
                                             validatecommand=vcmd_customer_entry,
                                             **style.entry_amount_conf_big)
        self.entry_3 = ttk.Entry(self.frame, validate="key",
                                             name="entry_3",
                                             validatecommand=vcmd_customer_entry,
                                             **style.entry_amount_conf_big)

        self.bic_button = Button(self.frame, text="Код",width=5, height=2, command=self.show_country)
        self.label_top.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W+tk.S)
        self.label.grid(row=1, column=0, padx=5, sticky=tk.E)
        self.bic_button.grid(row=2, column=0, rowspan=2, padx=5, sticky=tk.E)
        self.entry_1.grid(row=1, column=2, padx=10, pady=5, sticky=tk.W)
        self.entry_2.grid(row=2, column=2, padx=10, pady=5, sticky=tk.W)
        self.entry_3.grid(row=3, column=2, padx=10, pady=5, sticky=tk.W)
        

class Field_79(tk.Frame):
    
    def __init__(self, master, label_top_text, label_text, side, anchor):
        super().__init__(master)
        self.frame = tk.Frame(master, padx=5, pady=5)
        self.frame.pack(side=side, anchor=anchor, padx=15)
        style = Styles(self.frame)
        # self.exchange_rate = tk.StringVar()
        # vcmd_exchange_rate = (self.register(check_entry_settled_amount),"%P","%i","%d",13)
        self.label_exchange_rate_top = ttk.Label(self.frame, text=label_top_text, style="Heading.TLabel")
        self.label_exchange_rate = ttk.Label(self.frame, text=label_text, style="Heading.TLabel")
        self.message_area = Text(self.frame, width=40, height=15, **style.text_conf)

        self.label_exchange_rate_top.grid(row=0, column=1, padx=5, ipady=5, sticky=tk.W+tk.N)
        self.label_exchange_rate.grid(row=1,column=0,padx=5, sticky=tk.W+tk.N)
        self.message_area.grid(row=1,column=1, padx=0, sticky=tk.W+tk.N)
        

    def get_field(self):
        сheck_text_area_field = self.message_area.get("1.0", "end-1c")
        if сheck_text_area_field != "":
            text_area_field = self.message_area.get("1.0", "end-1c").split("\n")
            return text_area_field
        

    def set_field(self,data):
        print(data)
        value = "\n".join(data)
        self.message_area.insert(1.0, value)


    def clear_field(self):
        self.message_area.delete(1.0, END)


#меню
class MainMenu(tk.Menu):
        def __init__(self,app):
                super().__init__(app)
                self.app = app
                # self.mt_103 = mt_103
                
                app.config(menu=self)
                self.filemenu = Menu(self, tearoff=0)
##                filemenu.add_command(label="
                self.filemenu.add_command(label="Сохранить...",command=test_save, state=DISABLED)
                self.filemenu.add_command(label="Загрузить данные...",command=download_data, state=DISABLED)
                self.filemenu.add_command(label="Очистить данные...",command=clear_fields, state=DISABLED)
                self.filemenu.add_command(label="Выход", command=close_main_window)
                self.add_cascade(label="Файл",
                     menu=self.filemenu)
                #Дополнительное меню
                externalmenu = Menu(self, tearoff=0)
                externalmenu.add_command(label="Настройки", command=show_settings)
                externalmenu.add_command(label="Форма МТ 103", command=self.show_mt_103)
                externalmenu.add_command(label="Форма МТ 202", command=self.show_mt_102)
                externalmenu.add_command(label="Форма МТ 199", command=self.show_mt_199)
                self.add_cascade(label="Дополнительно", menu=externalmenu)
        

        def show_mt_103(self):
            global tabs
            if not tabs is None:
                tabs.destroy()
            tabs = TabFrame
            index_1 = self.filemenu.index(0)
            index_2=self.filemenu.index(1)
            index_3=self.filemenu.index(2)
            self.filemenu.entryconfigure(index_1, state=NORMAL)
            self.filemenu.entryconfigure(index_2, state=NORMAL)
            self.filemenu.entryconfigure(index_3, state=NORMAL)
            if not isinstance(tabs, TabFrame):
                tabs = tabs(app)
        

        def show_mt_102(self):
            global tabs
            if not tabs is None:
                tabs.destroy()
            tabs = TabFrame102
            index_1 = self.filemenu.index(0)
            index_2=self.filemenu.index(1)
            index_3=self.filemenu.index(2)
            self.filemenu.entryconfigure(index_1, state=NORMAL, command = test_save_2)
            self.filemenu.entryconfigure(index_2, state=NORMAL)
            self.filemenu.entryconfigure(index_3, state=NORMAL)
            if not isinstance(tabs, TabFrame102):
                tabs = tabs(app)


        def show_mt_199(self):
            global tabs
            if not tabs is None:
                tabs.destroy()
            tabs = TabFrame199
            index_1 = self.filemenu.index(0)
            index_2=self.filemenu.index(1)
            index_3=self.filemenu.index(2)
            self.filemenu.entryconfigure(index_1, state=NORMAL, command = test_save_3)
            self.filemenu.entryconfigure(index_2, state=NORMAL)
            self.filemenu.entryconfigure(index_3, state=NORMAL)
            if not isinstance(tabs, TabFrame199):
                tabs = tabs(app)



#закладки
class TabFrame(ttk.Notebook):

    #получаем все созданные области с данными
    def get_fields(self):
            self.fields = {}
            self.fields["field_20"]   = self.field_20.get_field()
            self.fields["field_23B"]  = self.field_23B.get_field()
            self.fields["field_23E"]  = self.field_23E.get_field()
            self.fields["field_26T"]  = self.field_26T.get_field()
            self.fields["field_32A"]  = self.field_32A.get_field()
            self.fields["field_33B"]  = self.field_33B.get_field()
            self.fields["field_36"]   = self.field_36.get_field()
            self.fields["field_50"]   = self.field_50.get_field()
            self.fields["field_52"]   = self.field_52.get_field()
            self.fields["field_53"]   = self.field_53.get_field()
            self.fields["field_56"]   = self.field_56.get_field()
            self.fields["field_57"]   = self.field_57.get_field()
            self.fields["field_59"]   = self.field_59.get_field()
            self.fields["field_70"]   = self.field_70.get_field()
            self.fields["field_71A"]  = self.field_71A.get_field()
            self.fields["field_71F"]  = self.field_71F.get_field()
            self.fields["field_71G"]  = self.field_71G.get_field()
            self.fields["field_72"]   = self.field_72.get_field()
            self.fields["field_77B"]  = self.field_77B.get_field()
            return self.fields
    
        
    def set_fields(self, data):
        area_4 = data["4:"]
        #Заполнение поля 20
        field_20 = area_4.setdefault(":20:")
        if not field_20 is None:
            self.field_20.set_field(field_20)
        #Заполнение поля 23B
        field_23B = area_4.setdefault(":23B:")
        if not field_23B is None:
            self.field_23B.set_field(field_23B)
        #Заполнение поля 23E
        field_23E = area_4.setdefault(":23E:")
        if not field_23E is None:
            self.field_23E.set_field(field_23E)
        #Заполнение поля 26T
        field_26T = area_4.setdefault(":26T:")
        if not field_26T is None:
            self.field_26T.set_field(field_26T)
        #Заполнение поля 32А
        field_32A = area_4.setdefault(":32A:")
        if not field_32A is None:
            self.field_32A.set_field(field_32A)
        #Заполнение поля 33B
        field_33B = area_4.setdefault(":33B:")
        if not field_33B is None:
            self.field_33B.set_field(field_33B)
        #Заполнение поля 36
        field_36 = area_4.setdefault(":36:")
        if not field_36 is None:
            self.field_36.set_field(field_36)
        #Заполнение поля 50(F)
        field_50 = area_4.setdefault(":50F:")
        if not field_50 is None:
            self.field_50.set_field(field_50, "F")
        #Заполнение поля 50(K)
        field_50 = area_4.setdefault(":50K:")
        if not field_50 is None:
            self.field_50.set_field(field_50, "K")
        #Заполнение поля 52(A)
        field_52 = area_4.setdefault(":52A:")
        if not field_52 is None:
            self.field_52.set_field(field_52, "A")
        #Заполнение поля 52(D)
        field_52 = area_4.setdefault(":52D:")
        if not field_52 is None:
            self.field_52.set_field(field_52, "D")
        #Заполнение поля 53 
        field_53 = area_4.setdefault(":53B:")
        if not field_53 is None:
            self.field_53.set_field(field_53, "")
        #Заполнение поля 56(A)
        field_56 = area_4.setdefault(":56A:")
        if not field_56 is None:
            self.field_56.set_field(field_56, "A")
        #Заполнение поля 56(D)
        field_56 = area_4.setdefault(":56D:")
        if not field_56 is None:
            self.field_56.set_field(field_56, "D")
        #Заполнение поля 57(A)
        field_57 = area_4.setdefault(":57A:")
        if not field_57 is None:
            self.field_57.set_field(field_57, "A")
        #Заполнение поля 57(D)
        field_57 = area_4.setdefault(":57D:")
        if not field_57 is None:
            self.field_57.set_field(field_57, "D")
        #Заполнение поля 59 
        field_59 = area_4.setdefault(":59:")
        if not field_59 is None:
            self.field_59.set_field(field_59, "")
        #Заполнение поля 70
        field_70 = area_4.setdefault(":70:")
        if not field_70 is None:
            self.field_70.set_field(field_70)
        #Заполнение поля 71A
        field_71A = area_4.setdefault(":71A:")
        if not field_71A is None:
            self.field_71A.set_field(field_71A)
        #Заполнение поля 71F
        field_71F = area_4.setdefault(":71F:")
        if not field_71F is None:
            self.field_71F.set_field(field_71F)
        #Заполнение поля 71G
        field_71G = area_4.setdefault(":71G:")
        if not field_71G is None:
            self.field_71G.set_field(field_71G)
        #Заполнение поля 72
        field_72 = area_4.setdefault(":72:")
        if not field_72 is None:
            self.field_72.set_field(field_72)
        #Заполнение поля 71F
        field_77B = area_4.setdefault(":77B:")
        if not field_77B is None:
            self.field_77B.set_field(field_77B)

    def clear_fields(self):
        #Очистка поля 20
        self.field_20.clear_field()
        #Oчистка поля 23B
        self.field_23B.clear_field()
        #Oчистка поля 23E
        self.field_23E.clear_field()
        #Oчистка поля 26T
        self.field_26T.clear_field()
        #Oчистка поля 32А
        self.field_32A.clear_field()
        #Oчистка поля 33B
        self.field_33B.clear_field()
        #Oчистка поля 36
        self.field_36.clear_field()
        #Oчистка поля 50
        self.field_50.clear_field()
        #Oчистка поля 52
        self.field_52.clear_field()
        #Oчистка поля 53
        self.field_53.clear_field()
        #Oчистка поля 56
        self.field_56.clear_field()
        #Oчистка поля 57
        self.field_57.clear_field()
        #Oчистка поля 59
        self.field_59.clear_field()
        #Oчистка поля 70
        self.field_70.clear_field()
        #Oчистка поля 71A
        self.field_71A.clear_field()
        #Oчистка поля 71F
        self.field_71F.clear_field()
        #Oчистка поля 71G
        self.field_71G.clear_field()
        #Oчистка поля 72
        self.field_72.clear_field()
        #Oчистка поля 77B
        self.field_77B.clear_field()
   
   
    #oсновной фрейм где у нас расположены табы
    def __init__(self,app):
        super().__init__(app)

        tab1 = ttk.Frame(self)
        tab2 = ttk.Frame(self)
        tab3 = ttk.Frame(self)
        tab4 = ttk.Frame(self)

        self.add(tab1, text="Основная")
        self.add(tab2, text="Реквизиты перевода")
        self.add(tab3, text="Дополнительная информация")
        self.pack(expand=1,fill="both")


        self.label_frame = tk.LabelFrame(tab1)
        self.field_20 = Field_20(self.label_frame,"Референс отправителя","*:20:", LEFT, tk.N)
        self.field_32A = Field_32A(self.label_frame,"Дата","*:32А:", LEFT, tk.N)
        self.label_frame.pack(side=TOP,fill=X, anchor=tk.N)

        self.left_frame = tk.Frame(tab1)
        self.field_23B = Field_23B(self.left_frame,"Код банковской операции","*:23B:", TOP, tk.W)
        self.field_23E = Field_23E(self.left_frame,"Код для инструкций:", "23E:", TOP, tk.W+tk.N)
        self.field_26T = Field_26T(self.left_frame,"Код типа сделки", "26T:", LEFT, tk.W)
        self.left_frame.pack(side=LEFT,anchor=tk.N)

        
        self.right_frame = tk.Frame(tab1)
        self.field_33B = Field_33B(self.right_frame,"Валюта платежа(первоначальная)",":33B", TOP, tk.N)
        self.field_36 = Field_36(self.right_frame,"Курс",":36", LEFT, tk.N)
        self.right_frame.place(relx=.52, rely=.12)
        


        self.left_frame = tk.Frame(tab2)
        self.field_50 = Field_50(self.left_frame,"Клиент-плательщик",":50", TOP, tk.N)
        self.field_53 = Field_53(self.left_frame,"Счет списания",":53", TOP, tk.N)
        self.field_59 = Field_59(self.left_frame,"Бенефициар",":59", TOP, tk.N)
        self.left_frame.pack(side=LEFT,fill=X, anchor=tk.N)

        self.right_frame = tk.Frame(tab2)
        self.field_52 = Field_52(self.right_frame,"Банк клиента плательщика",":52", TOP, tk.N)
        self.field_56 = Field_56(self.right_frame,"Банк посредник",":56", TOP, tk.N)
        self.field_57 = Field_57(self.right_frame,"Банк бенефициара",":57", TOP, tk.N) 
        self.right_frame.pack(side=RIGHT, fill=X, anchor=tk.N)                    

        self.left_frame = tk.Frame(tab3)
        self.field_70 = Field_70(self.left_frame,"Назначение платежа",":70", TOP, tk.W)
        self.field_72 = Field_72(self.left_frame,"Информация для получателя сообщения",":72", TOP, tk.W)
        self.field_77B = Field_77B(self.left_frame, "Гражданство клиента", ":77B", TOP, tk.W)
        self.left_frame.pack(side=LEFT,fill=X, anchor=tk.N)

        self.right_frame = tk.Frame(tab3)
        self.field_71G = Field_71G(self.right_frame,"Комиссия получателя сообщения",":71G", TOP, tk.N)
        self.field_71A = Field_71A(self.right_frame,"Детали комиссий",":71A", TOP, tk.N)
        self.field_71F = Field_71F(self.right_frame,"Комиссия отправителя сообщения",":71F", TOP, tk.N)
        self.right_frame.pack(side=RIGHT, fill=X, anchor=tk.N)


#закладки
class TabFrame102(ttk.Notebook):

    #получаем все созданные области с данными
    def get_fields(self):
            self.fields = {}
            self.fields["field_20"]   = self.field_20.get_field()
            self.fields["field_21"]   = self.field_21.get_field()
            self.fields["field_32A"]  = self.field_32A.get_field()
            self.fields["field_52"]   = self.field_52.get_field()
            self.fields["field_53"]   = self.field_53.get_field()
            self.fields["field_56"]   = self.field_56.get_field()
            self.fields["field_57"]   = self.field_57.get_field()
            self.fields["field_58"]   = self.field_58.get_field()
            self.fields["field_72"]   = self.field_72.get_field()
            return self.fields
        
    def set_fields(self, data):
        area_4 = data["4:"]
        #Заполнение поля 20
        field_20 = area_4.setdefault(":20:")
        if not field_20 is None:
            self.field_20.set_field(field_20)
        #Заполнение поля 21
        field_21 = area_4.setdefault(":21:")
        if not field_21 is None:
            self.field_21.set_field(field_21)
        # #Заполнение поля 32А
        field_32A = area_4.setdefault(":32A:")
        if not field_32A is None:
            self.field_32A.set_field(field_32A)
        #Заполнение поля 52(A)
        field_52 = area_4.setdefault(":52A:")
        if not field_52 is None:
            self.field_52.set_field(field_52, "A")
        #Заполнение поля 52(D)
        field_52 = area_4.setdefault(":52D:")
        if not field_52 is None:
            self.field_52.set_field(field_52, "D")
        #Заполнение поля 53 
        field_53 = area_4.setdefault(":53B:")
        if not field_53 is None:
            self.field_53.set_field(field_53, "")
        #Заполнение поля 56(A)
        field_56 = area_4.setdefault(":56A:")
        if not field_56 is None:
            self.field_56.set_field(field_56, "A")
        #Заполнение поля 56(D)
        field_56 = area_4.setdefault(":56D:")
        if not field_56 is None:
            self.field_56.set_field(field_56, "D")
        #Заполнение поля 57(A)
        field_57 = area_4.setdefault(":57A:")
        if not field_57 is None:
            self.field_57.set_field(field_57, "A")
        #Заполнение поля 57(D)
        field_57 = area_4.setdefault(":57D:")
        if not field_57 is None:
            self.field_57.set_field(field_57, "D")
        #Заполнение поля 58(A)
        field_58 = area_4.setdefault(":58A:")
        if not field_58 is None:
            self.field_58.set_field(field_58, "A")
        #Заполнение поля 58(D)
        field_58 = area_4.setdefault(":58D:")
        if not field_58 is None:
            self.field_58.set_field(field_58, "D")
        
        #Заполнение поля 72
        field_72 = area_4.setdefault(":72:")
        if not field_72 is None:
            self.field_72.set_field(field_72)
        
    def clear_fields(self):
        #Очистка поля 20
        self.field_20.clear_field()
        #Oчистка поля 32А
        self.field_32A.clear_field()
        #Oчистка поля 52
        self.field_52.clear_field()
        #Oчистка поля 53
        self.field_53.clear_field()
        #Oчистка поля 56
        self.field_56.clear_field()
        #Oчистка поля 57
        self.field_57.clear_field()
        #Oчистка поля 58
        self.field_57.clear_field()
        #Oчистка поля 72
        self.field_72.clear_field()
   
   
    #oсновной фрейм где у нас расположены табы
    def __init__(self,app):
        super().__init__(app)

        tab1 = ttk.Frame(self)
        tab2 = ttk.Frame(self)
        tab3 = ttk.Frame(self)

        self.add(tab1, text="Основная")
        self.add(tab2, text="Реквизиты перевода")
        self.pack(expand=1,fill="both")


        self.label_frame = tk.LabelFrame(tab1)
        self.field_20 = Field_20(self.label_frame,"Референс отправителя","*:20:", LEFT, tk.N)
        self.field_32A = Field_32A(self.label_frame,"Дата","*:32А:", LEFT, tk.N)
        self.label_frame.pack(side=TOP,fill=X, anchor=tk.N)

        self.left_frame = tk.Frame(tab1)
        self.field_21 = Field_21(self.left_frame,"Связанный референс","*:21:", TOP, tk.W)
        self.left_frame.pack(side=LEFT,anchor=tk.N)

        
        self.right_frame = tk.Frame(tab1)
        self.field_52 = Field_52(self.right_frame,"Банк клиента плательщика",":52", TOP, tk.N)
        self.field_53 = Field_53(self.left_frame,"Счет списания",":53", TOP, tk.N)
        self.right_frame.place(relx=.52, rely=.12)
  
        self.left_frame = tk.Frame(tab2)
        self.field_56 = Field_56(self.left_frame,"Банк посредник",":56", TOP, tk.N)
        self.field_72 = Field_72(self.left_frame,"Информация для получателя сообщения",":72", TOP, tk.W)
        self.left_frame.pack(side=LEFT,fill=X, anchor=tk.N)

        self.right_frame = tk.Frame(tab2)
        self.field_57 = Field_57(self.right_frame,"Банк бенефициара",":57", TOP, tk.N)
        self.field_58 = Field_58(self.right_frame,"Банк бенефициар",":58", TOP, tk.N)
        self.right_frame.pack(side=RIGHT, fill=X, anchor=tk.N)                    


#закладки
class TabFrame199(ttk.Notebook):

    #получаем все созданные области с данными
    def get_fields(self):
            self.fields = {}
            self.fields["field_20"]   = self.field_20.get_field()
            self.fields["field_21"]   = self.field_21.get_field()
            self.fields["field_79"]   = self.field_79.get_field()
            return self.fields


    def set_fields(self, data):
        area_4 = data["4:"]
        #Заполнение поля 20
        field_20 = area_4.setdefault(":20:")
        if not field_20 is None:
            self.field_20.set_field(field_20)
        #Заполнение поля 21
        field_21 = area_4.setdefault(":21:")
        if not field_21 is None:
            self.field_21.set_field(field_21)
        #Заполнение поля 79
        field_79 = area_4.setdefault(":79:")
        if not field_79 is None:
            self.field_79.set_field(field_79)
        
   
        
    def clear_fields(self):
        #Очистка поля 20
        self.field_20.clear_field()
        #Oчистка поля 21
        self.field_21.clear_field()
        #Oчистка поля 79
        self.field_79.clear_field()
      
       
   
   
    #oсновной фрейм где у нас расположены табы
    def __init__(self,app):
        super().__init__(app)

        tab1 = ttk.Frame(self)
      

        self.add(tab1, text="Основная")
        self.pack(expand=1,fill="both")


        self.label_frame = tk.LabelFrame(tab1)
        self.field_20 = Field_20(self.label_frame,"Референс отправителя","*:20:", LEFT, tk.N)
        self.field_21 = Field_21(self.label_frame,"Связанный референс","*:21:", TOP, tk.W)
        self.label_frame.pack(side=TOP,fill=X, anchor=tk.N)


        self.left_frame = tk.Frame(tab1)
        self.field_79 = Field_79(self.left_frame,"Сообщение получателю",":79:", TOP, tk.W)
        self.left_frame.pack(side=LEFT,anchor=tk.N)
  

#кэш справочников
class CacheSPFS():
    def __init__(self, path_to_bic_spfs):
        self.path_to_bic = path_to_bic_spfs
        self.data = GetSpfsBic().get_fields_from_txt(self.path_to_bic)
    
    def get_data(self):
        return self.data

class CacheBicSwift():
    def __init__(self, path_to_bic):
        self.path_to_bic = path_to_bic
        self.data = Bic(path_to_bic).bic_list
    
    def get_data(self):
        return self.data

        

#настройки главного окна
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Форма набора swift сообщений")
        self.geometry("1110x600+400+100")
        self.resizable(0,0)
        

if __name__ == "__main__":
    app = App()
    spfs_data = CacheSPFS(path_to_bic_spfs).get_data()
    swift_data = CacheBicSwift(path_to_bic).get_data()
    MainMenu(app)
    app.mainloop()
