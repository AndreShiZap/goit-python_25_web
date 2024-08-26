# бот-асистент адресної книги:
# зберігає ім'я, номер телефону та дату народження у файлі addressbook.pkl",
# знаходить номер телефону за ім'ям, змінює записаний номер телефону,
# знаходить дату народження за ім'ям, змінює дату народження,
# виводить на консоль дати народження на наступні 7 днів
# виводить в консоль всі записи, які збереженні
from functools import wraps
from collections import UserDict
from datetime import datetime, date, timedelta
from abc import ABC, abstractmethod
import re
import pickle


FILE_STORE = "addressbook.pkl"


def input_error(func):
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            if inner.__name__ == "add_contact":
                if str(e).startswith("not enough"):
                    return f"Enter the argument for the command: name and phone."
                else:
                    return f"Enter the argument for the command: name and phone.\n{e}"
            elif inner.__name__ == "change_contact":
                if str(e).startswith("not enough"):
                    return f"Enter the argument for the command: name, old phone and new phone."
                else:
                    return f"Enter the argument for the command: name, old phone and new phone.\n{e}"
            elif inner.__name__ == "add_phone":
                return f"It's not a phone number.\n{e}"
            elif inner.__name__ == "add_birthday":
                return f"Enter the argument for the command: name and birthday (dd.mm.yyyy)"
            else:
                return e
        except KeyError:
            return "Contact not found"
        except IndexError:
            if inner.__name__ == "phone_show":
                return "Enter the argument for the command: name"
            elif inner.__name__ == "show_birthday":
                return "Enter the argument for the command: name"
            else:
                return "IndexError"

    return inner


def valid_name(name):
    if not (type(name) == str and len(name) > 1):
        raise ValueError("Name - required field, at least two letters")
    return name


def valid_phone(phone):
    regex = "^[0-9]{10}$"
    if not re.match(regex, phone):
        raise ValueError(
            "It's not a phone number. A phone number must contain 10 digits"
        )
    return phone


class Field(ABC):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    @abstractmethod
    def __getitem__(self):
        pass


class Name(Field):
    def __init__(self, value):
        super().__init__(value)
        self.value = valid_name(value)

    def __getitem__(self):
        return self.value


class Phone(Field):
    def __init__(self, value):
        super().__init__(value)
        self.value = valid_phone(value)

    def __getitem__(self):
        return self.value


class Birthday(Field):
    def __init__(self, value):
        super().__init__(value)
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
            self.value = self.value.strftime("%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    def __getitem__(self):
        return self.value


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def __str__(self):
        return f"Contact name: {self.name}, phones: {'; '.join(p.value for p in self.phones)}, birthday: {self.birthday}"

    def add_phone(self, phone):
        phone = Phone(phone)
        for i in range(len(self.phones)):
            if self.phones[i].value == phone.value:
                raise ValueError(f"Phone {phone} already exists")
        self.phones.append(phone)
        return self.phones

    def remove_phone(self, phone):
        phone = Phone(phone)
        for i in range(len(self.phones)):
            if self.phones[i].value == phone.value:
                self.phones.pop(i)
                return self.phones
            else:
                return None

    def edit_phone(self, old_phone, new_phone):
        old_phone = Phone(old_phone)
        new_phone = Phone(new_phone)
        for i in range(len(self.phones)):
            if self.phones[i].value == old_phone.value:
                self.phones.pop(i)
                self.phones.insert(i, new_phone)
                return self.phones
            else:
                raise ValueError(f"{old_phone} is not found")

    def find_phone(self, phone):
        self.phone = Phone(phone)
        for i in range(len(self.phones)):
            if self.phones[i].value == phone.value:
                return self.phone
        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)
        return self.birthday


class AddressBook(UserDict):
    def __init__(self):
        super().__init__()
        self.data = {}

    def __str__(self):
        str_book = ""
        for key in self.data:
            str_book += self.data[key].__str__() + "\n"
        return str_book

    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        name = Name(name)
        for key in self.data:
            if key == name.value:
                return self.data[key]
        else:
            return None

    def delete(self, name):
        name = Name(name)
        if name.value in self.data:
            del self.data[name.value]
        else:
            return ValueError(f"{name} is not found")
        return self.data

    def get_upcoming_birthdays(self, days=7):
        upcoming_birthdays = []
        today = date.today()
        for key in self.data:
            birthday_realy = datetime.strptime(
                self.data[key].birthday.value, "%d.%m.%Y"
            ).date()
            birthday_this_year = birthday_realy.replace(year=today.year)
            if birthday_this_year < today:
                birthday_this_year = birthday_realy.replace(year=today.year + 1)
            if 0 <= (birthday_this_year - today).days <= days:
                congratulation_date_str = date_to_string(
                    adjust_for_weekend(birthday_this_year)
                )
                upcoming_birthdays.append(
                    {
                        "name": self.data[key].name.value,
                        "congratulation_date": congratulation_date_str,
                    }
                )
        return upcoming_birthdays


def date_to_string(dat):
    return dat.strftime("%d.%m.%Y")


def find_next_weekday(start_date, weekday):
    days_ahead = weekday - start_date.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return start_date + timedelta(days=days_ahead)


def adjust_for_weekend(birthday):
    if birthday.weekday() >= 5:
        return find_next_weekday(birthday, 0)
    return birthday


def parse_input(user_input):
    if user_input:
        cmd, *args = user_input.split()
        cmd = cmd.strip().lower()
    else:
        cmd = "0"
        args = []
    return cmd, *args


@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record:
        record.edit_phone(old_phone, new_phone)
    else:
        return "Contact not found"
    return "Contact updated."


@input_error
def phone_show(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record:
        return f"{'; '.join(p.value for p in record.phones)}"
    else:
        return "Contact not found"


@input_error
def add_birthday(args, book: AddressBook):
    name, birthday, *_ = args
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        return "Contact updated."
    else:
        return "Contact not found"


@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record:
        return record.birthday
    else:
        return "Contact not found"


@input_error
def birthdays(book: AddressBook):
    str_birthdays = ""
    list_birthdays = book.get_upcoming_birthdays()
    if len(list_birthdays) == 0:
        return "No birthdays for 7 days"
    for elem in list_birthdays:
        str_birthdays += str(elem) + "\n"
    return str_birthdays


def save_data(book, filename=FILE_STORE):
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename=FILE_STORE):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


class Bot(ABC):

    @abstractmethod
    def output(self, book: AddressBook, command, args): ...

    @abstractmethod
    def output_text(self, value: str): ...

    @abstractmethod
    def output_command(self): ...


class BotAssistant(Bot):
    def __init__(self):
        self.book = AddressBook()

    def output(self, book: AddressBook, command, args):
        match command:
            case "add":
                print(add_contact(args, book))
            case "change":
                print(change_contact(args, book))
            case "phone":
                print(phone_show(args, book))
            case "all":
                print(book)
            case "add-birthday":
                print(add_birthday(args, book))
            case "show-birthday":
                print(show_birthday(args, book))
            case "birthdays":
                print(birthdays(book))

    def output_text(self, command):
        if command == "close" or command == "exit":
            print("Good bye!")
        elif command == "hello":
            print("How can I help you?")
        else:
            print(f"Invalid command.")

    def output_command(self):
        list_command = [
            "hello",
            "add",
            "change",
            "phone",
            "all",
            "add-birthday",
            "show-birthday",
            "birthdays",
            "close/exit",
        ]
        str_comm = f"Available commands: {list_command}\n"
        str_comm += "Format command:\n"
        str_comm += "add name phone - adds a contact and/or phone number\n"
        str_comm += (
            "change name old_phone new_phone - changes the contact's phone number\n"
        )
        str_comm += "phone name - shows contact phone numbers\n"
        str_comm += "all - shows all contents of the address book\n"
        str_comm += "add-birthday name birthday(dd.mm.yyyy) - adds/changes contact's date of birth\n"
        str_comm += "show-birthday name - shows the contact's date of birth\n"
        str_comm += "birthdays - shows birthdays in the next 7 days\n"
        str_comm += "close/exit - terminates the program\n"
        return list_command, str_comm


def main():
    print("Welcome to the assistant bot!")
    book = load_data()
    bot_assistant = BotAssistant()
    list_command, str_comm = bot_assistant.output_command()

    while True:
        user_input = input("Enter a command or Help: ")
        command, *args = parse_input(user_input)

        if command in list_command[1:-1]:
            bot_assistant.output(book, command, args)
        elif command == "close" or command == "exit":
            bot_assistant.output_text(command)
            break
        elif command == "hello":
            bot_assistant.output_text(command)
        elif command == "help":
            print(str_comm)
        else:
            bot_assistant.output_text(command)
    save_data(book)


if __name__ == "__main__":
    main()
