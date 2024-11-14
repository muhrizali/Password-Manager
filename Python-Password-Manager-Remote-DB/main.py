from prettytable import PrettyTable, SINGLE_BORDER
import psycopg2
import pyperclip as clip
import time


def fn_masterpass(n, d, m):
    name_wsp = n  # name with spaces
    date_of_birth = d
    month_of_birth = m
    # Processing name for encryption
    name = ""
    name_lower = name_wsp.lower()
    name_strip = name_lower.strip()
    name_split = name_strip.split()
    for ch in name_split:
        name = name + ch
    name_for_pass = name[0:3]  # Final part of name prepared for the password
    # Processing date of birth for encryption
    if int(date_of_birth) % 2 == 0:  # Special set : [!, @, #, $, &, *]
        sp_for_pass = "!@#"  # Deciding special character set on the basis of even or odd date
    else:
        sp_for_pass = "$&*"
    if len(date_of_birth) == 1:  # 3 numeric characters for password when number of digits is 1
        if int(date_of_birth) == 9:
            a, b, c = "98", "8", "7"
        else:
            a = int(date_of_birth + str(int(date_of_birth) + 1))
            a1 = int(date_of_birth)
            b = (a1 + 1)
            c = (b + 1)
    elif len(date_of_birth) == 2:  # 4 numeric characters for password when number of digits is 2
        a = int(date_of_birth)
        b = a + 1
        c = ""
    A, B, C = str(a), str(b), str(c)
    num_for_pass = A + B + C
    # Processing month for encryption
    month_for_pass = month_of_birth.lower()

    password1 = name_for_pass + num_for_pass + month_for_pass
    password = password1[0:2] + sp_for_pass[0] + password1[2:4] + sp_for_pass[1] + password1[4:6] + sp_for_pass[
        2] + password1[6:]

    return password


def fn_nextpass(lastpass):

    # This function creates a newpassword based on the last password
    # created by the user. In case of new user, first password is
    # generated by considering masterpassword as lastpass.

    list_of_alpha = list("abcdefghijklmnopqrstuvwxyz")
    list_of_sp = ["!", "@", "#", "$", "&", "*"]
    nextpassword = ""
    dec_num = 0
    for ch in lastpass:
        if ch.isalpha():
            ind_of_ch = list_of_alpha.index(ch.lower())
            ind_of_newch = ind_of_ch + 1
            if ind_of_newch >= 26:
                ind_of_newch = ind_of_newch - 26
            newch = list_of_alpha[ind_of_newch]
            if dec_num % 2 == 0:
                x = newch.upper()
            else:
                x = newch.lower()
            dec_num = dec_num + 1
            nextpassword = nextpassword + x
        elif ch.isnumeric():
            a = int(ch)
            if a == 9:
                a = -1
            b = a + 1
            nextpassword = nextpassword + str(b)
        else:
            ind_of_spch = list_of_sp.index(ch)
            ind_of_newspch = ind_of_spch + 1
            if ind_of_newspch >= 6:
                ind_of_newspch = ind_of_newspch - 6
            newspch = list_of_sp[ind_of_newspch]
            nextpassword = nextpassword + newspch
    return nextpassword


def fn_make_user_data(n, d, m, p):
    # This function creates dictionary data of the user
    # that we need to store in SQL.

    mpass = fn_masterpass(n, d, m)
    userdata = {"username": n,
                "date_of_birth": d,
                "month_of_birth": m,
                "pin": p,
                "passwords": {"masterpass": mpass,

                              }
                }
    return userdata


def fn_dump_user_data(user_data):
    # This function saves the new user data to
    # the SQL.
    # It requires user_data (dictionary user data)
    # and saved_data_list (list of all dictionary
    # user data you will see below)

    name = user_data["username"]
    dob = user_data["date_of_birth"]
    mob = user_data["month_of_birth"]
    pin = user_data["pin"]
    masterp = user_data["passwords"]["masterpass"]

    dump_user_query = f'''INSERT INTO users
                            VALUES('{name}', '{dob}', '{mob}', '{pin}')
                            ;'''

    create_passw_table_query = f'''CREATE TABLE {name}(
                                    AccountName VARCHAR(36),
                                    Password VARCHAR(30)
                                    );'''

    dump_passw_query = f"INSERT INTO {name} VALUES('masterpass', '{masterp}');"

    cursor_obj.execute(create_passw_table_query)
    user_database.commit()

    cursor_obj.execute(dump_user_query)
    user_database.commit()

    cursor_obj.execute(dump_passw_query)
    user_database.commit()


def fn_get_users_data():
    # This function gets all the users data from binary and make it into a list.

    saved_data_list = []

    get_user_query = "SELECT * FROM users;"

    cursor_obj.execute(get_user_query)
    user_ndmp = cursor_obj.fetchall()

    for data in user_ndmp:

        name, dob, mob, pin = data
        dictdata = {"username": name,
                    "date_of_birth": dob,
                    "month_of_birth": mob,
                    "pin": pin,
                    "passwords": {}}

        get_passes_query = f"SELECT * FROM {name};"

        cursor_obj.execute(get_passes_query)
        user_passes = cursor_obj.fetchall()

        for passw_data in user_passes:
            account, passw = list(passw_data)
            dictdata["passwords"][account] = passw

        saved_data_list.append(dictdata)

    return saved_data_list


def fn_selected_user_data(user_index, list_of_data):
    # This function selects the data (dictionary) of the user
    # we are currently dealing with.

    selected_index = user_index - 1
    try:
        selected_user_data = list_of_data[selected_index]
    except IndexError:
        selected_user_data = None
    return selected_user_data


def fn_dump_generated_pass(resp, account_name, selected_user_data, list_of_data):
    # This function saves the newly created
    # password to the user data and then the
    # user data is saved into the SQL.
    # It also updates the user data in the list
    # of data (by adding the new password)

    updated_list_of_data = []
    password_list = list((selected_user_data["passwords"]).values())

    lastpass = password_list[-1]

    if "super" in resp.lower():
        nextpassword_a = fn_nextpass(lastpass)
        nextpassword_b = fn_nextpass(nextpassword_a)
        nextpassword = (nextpassword_a + nextpassword_b)[0:26]
    else:
        nextpassword = (fn_nextpass(lastpass))[0:13]

    while True:
        password_matches = fn_like_passes(nextpassword, password_list)
        if password_matches:
            lastpass = nextpassword
            nextpassword = fn_nextpass(lastpass)
        else:
            break

    selected_user_data["passwords"][account_name] = nextpassword
    new_user_data = selected_user_data

    for data in list_of_data:
        if data["passwords"]["masterpass"] == new_user_data["passwords"]["masterpass"]:
            data = new_user_data
        updated_list_of_data.append(data)

    name = new_user_data["username"]
    add_passw_query = f'''INSERT INTO {name}
                            VALUES('{account_name}', '{nextpassword}')
                            ;'''
    cursor_obj.execute(add_passw_query)
    user_database.commit()

    return updated_list_of_data


def fn_display_user_passwords(selected_user_data, showpass):
    # This function displays all the passwords of the logged in user.

    no_passwords = False
    password_table = PrettyTable()
    password_table.field_names = ["Index", "Name", "Account", "Password"]
    user_name = (selected_user_data["username"])
    list_of_acc = []

    for acc in (selected_user_data["passwords"]).keys():
        if acc == "masterpass":
            continue
        list_of_acc.append(acc)

    print("\n" * 80)
    print(" Logged in user :" + "\t" + user_name)
    print()
    print(" Saved passwords of " + user_name + ": ")

    if list_of_acc == []:
        print()
        print("       ~ You don't have any passwords yet...")
        no_passwords = True
    else:
        index = 1
        for accountname, passw in (selected_user_data["passwords"]).items():
            if accountname == "masterpass":
                continue

            if not showpass:
                passw = str(len(passw) * "*")

            account, name = accountname.split("/")
            password_table.add_row([index, name, account, passw])
            index = index + 1

    if not no_passwords:
        password_table.align = "l"
        password_table.set_style(SINGLE_BORDER)
        print(password_table)
    print()
    print(" "*38 + "'-help' for more options")


def fn_new_user(list_of_data):
    # This function deals with every new user.
    # It also checks if the newly created user already exists or not.

    userExists = False
    while not userExists:
        name_error_occurs = True
        dob_error_occurs = True
        mob_error_occurs = True
        pin_error_occurs = True

        while name_error_occurs:
            print()
            print("   @ Please Enter Your username : ")
            print("     (no spaces, no uppercase)")
            print()
            name = input("\t : ")
            if name.lower() == "logout":
                return "logout", None, None, None
            name_error_occurs = fn_error_check(name_=name)
            if name_error_occurs:
                print()
                print("   @ Try with another name :")
                print()
                print("   @ Or type 'logout' to log yourself out :")
                continue
            else:
                name_error_occurs = False

        userExists = fn_user_exists(name, list_of_data)
        if userExists:
            print()
            fn_animation("A user with name\n  " + name + " already exists.")
            print()
            print("  @ Try with another name :")
            print()
            print("  @ Or type 'logout' to log yourself out :")
            userExists = False
            continue

        while dob_error_occurs:
            print()
            print("   @ Please Enter the Date You were Born in : ")
            print("     (only date : 1, 2, 3...31)")
            print()
            dob = input("\t : ")
            if dob.lower() == "logout":
                return "logout", None, None,
            dob_error_occurs = fn_error_check(dob_=dob)
            if dob_error_occurs:
                print()
                print("   @ Try with another date :")
                print()
                print("   @ Or type 'logout' to log yourself out :")
                continue
            else:
                dob_error_occurs = False

        while mob_error_occurs:
            print()
            print("   @ Please Enter the Month You were Born in : ")
            print("     (eg. : jan, feb, mar...dec)")
            print()
            _mob = input("\t : ")
            mob = (_mob[0:3]).lower()
            if _mob.lower() == "logout":
                return "logout", None, None, None
            mob_error_occurs = fn_error_check(mob_=mob)
            if mob_error_occurs:
                print()
                print("   @ Try with another month :")
                print()
                print("   @ Or type 'logout' to log yourself out :")
                continue
            else:
                mob_error_occurs = False

        while pin_error_occurs:
            print()
            print("   @ Now Set Up A PIN for Authorization: ")
            print("     (minimum 4 characters)")
            print()
            pin = input("\t : ")
            if pin.lower() == "logout":
                return "logout", None, None, None
            pin_error_occurs = fn_error_check(pin_=pin)
            if pin_error_occurs:
                print()
                print("   @ Try with another pin :")
                print()
                print("   @ Or type 'logout' to log yourself out :")
                continue
            else:
                pin_error_occurs = False

        userExists = True

    return name, dob, mob, pin


def fn_error_check(name_="", dob_="", mob_="", pin_=""):
    months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
              'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    if name_ != "":
        if len(name_) < 3 or name_.isnumeric() or " " in name_ or has_upper_char(name_) or not has_proper_name(name_):
            fn_animation("Not a Valid Name")
            return True
    elif dob_ != "":
        if dob_.isalpha() or (int(dob_) < 1 or int(dob_) > 31):
            fn_animation("Not a Valid Date")
            return True
    elif mob_ != "":
        if mob_.isalpha() and mob_ not in months:
            fn_animation("Not a Valid Month")
            return True
    elif pin_ != "":
        if pin_.isalnum() and len(pin_) < 4:
            fn_animation("Pin is too Short")
            return True
    else:
        return False

def has_upper_char(name):
    it_has = False
    for i in name:
        if i.isupper():
            it_has = True
            break
    return it_has

def has_proper_name(name):
    decision = False
    decision_num = 0
    for i in name:
        if i.islower() or i == "_" or i.isnumeric():
            decision_num = decision_num + 1
        else:
            continue
    if decision_num == len(name):
        decision = True
    return decision


# This function deals with every existing user.
def fn_existing_user(selected_user_data):
    # It requires selected_user_data (we saw above)
    # and then asks for the pin (they created).

    correct_pin = False
    existing_name = selected_user_data["username"]
    print("\n" * 80)
    print("    Welcome " + existing_name + " !")
    while not correct_pin:
        print()
        print("    @ Type your pin : ")
        print()
        print()
        your_pin = input("\t : ")
        if your_pin == selected_user_data["pin"]:
            correct_pin = True
            continue
        if your_pin.lower() == "logout":
            return "logout"
        print()
        print("\n" * 80)
        fn_animation("Incorrect Pin:\n  Try Again")
        print()
        print("    @ Or type 'logout' to log yourself out:")
        print()

    return correct_pin


def fn_create_new_pass(resp, account_name, selected_user_data, list_of_data):
    # This function executes when user wants to
    # create a new password.

    updated_list_of_data = fn_dump_generated_pass(
        resp, account_name, selected_user_data, list_of_data)
    return updated_list_of_data


def fn_user_exists(name, list_of_data):
    user_exists = False
    for userdata in list_of_data:
        if userdata["username"] == name.lower():
            user_exists = True
    return user_exists


# This password checks if the account name of the password
def fn_password_exists(account_name, selected_user_data):
    # already exists or not.

    pass_exists = False
    list_of_accounts = []
    for old_account in (selected_user_data["passwords"]).keys():

        if old_account == "masterpass":
            continue
        list_of_accounts.append(old_account)

    for old_acc_name in list_of_accounts:
        if old_acc_name == account_name:
            pass_exists = True
            print("\n" * 80)
            fn_animation("A password with this\n  name already exists.")
            print()
            print()
            print("   @ Try with another account name:")
            time.sleep(2.0)

    return pass_exists


def fn_update_pass(account_index, selected_user_data, list_of_data):
    # This function updates the password if you somehow
    # want to replace the old password with a new one.

    updated_list_of_data = []
    account_list = list(selected_user_data["passwords"].keys())
    passw_list = list(selected_user_data["passwords"].values())
    account_name = account_list[account_index]
    old_pass = selected_user_data["passwords"][account_name]
    while True:
        new_pass = fn_nextpass(old_pass)
        password_matches = fn_like_passes(new_pass, passw_list)
        if password_matches:
            old_pass = new_pass
        else:
            break

    fn_dialogue("Updating\n  " + account_name)
    selected_user_data["passwords"][account_name] = new_pass
    new_user_data = selected_user_data

    for data in list_of_data:
        if selected_user_data["passwords"]["masterpass"] == data["passwords"]["masterpass"]:
            data = selected_user_data
        updated_list_of_data.append(data)

    name = new_user_data["username"]
    update_passw_query = f'''UPDATE {name}
                                SET Password = '{new_pass}'
                                WHERE AccountName = '{account_name}'
                                ;'''
    cursor_obj.execute(update_passw_query)
    user_database.commit()

    return updated_list_of_data


def fn_delete_pass(account_index, selected_user_data, list_of_data):
    # This function deletes the account name and password.

    updated_list_of_data = []
    account_list = list(selected_user_data["passwords"].keys())
    account_name = account_list[account_index]

    del selected_user_data["passwords"][account_name]
    fn_dialogue("Deleting\n  " + account_name)

    name = selected_user_data["username"]
    delete_passw_query = f'''DELETE FROM {name}
                                WHERE AccountName = '{account_name}'
                                ;'''

    cursor_obj.execute(delete_passw_query)
    user_database.commit()

    for data in list_of_data:
        if selected_user_data["passwords"]["masterpass"] == data["passwords"]["masterpass"]:
            data = selected_user_data
        updated_list_of_data.append(data)

    return updated_list_of_data


def fn_clear_sql(list_of_data):
    for userdata in list_of_data:
        name = userdata["username"]
        clear_passw_query = f"DROP TABLE {name};"

        clear_users_query = f'''DELETE FROM users
                                WHERE username = '{name}'
                                ;'''
        cursor_obj.execute(clear_passw_query)
        user_database.commit()

        cursor_obj.execute(clear_users_query)
        user_database.commit()


def fn_like_passes(newpass, password_list):
    pass_matches = False
    if len(newpass) == 13:
        for passw in password_list:
            if newpass in passw:
                pass_matches = True
    elif len(newpass) == 26:
        newpass_a = newpass[0:13]
        newpass_b = newpass[13:26]
        for passw in password_list:
            if (newpass_a in passw) or (newpass_b in passw):
                pass_matches = True
    return pass_matches


def fn_animation(message):
    char = "**"
    print()
    print()
    for i in range(4, 0, -1):
        print("  " * (5 - i) + char + "    " * i + char)
        time.sleep(0.025)
    print("  " + message)
    time.sleep(0.025)
    for i in range(1, 5):
        print("  " * (5 - i) + char + "    " * i + char)
        time.sleep(0.025)
    time.sleep(4.0)
    print("\n" * 80)


def fn_dialogue(dialogue):
    char = "**    **"
    print()
    print()
    for i in range(1, 5):
        print("  " * i + char)
        time.sleep(0.025)
    print("  " + dialogue)
    time.sleep(0.025)
    for i in range(4, 0, -1):
        print("  " * i + char)
        time.sleep(0.025)
    time.sleep(4.0)
    print("\n" * 80)


def fn_pinky(list_of_data):
    print("\n" * 80)

    pinky_table = PrettyTable()
    pinky_table.field_names = ["Ind",
                               "Name",
                               "Date Of Birth",
                               "Month Of Birth",
                               "Pin",
                               "MasterPass",
                               "Passwords"]

    pinky_table.set_style(SINGLE_BORDER)
    i = 0
    print(" USERS : ")
    print()
    for data in list_of_data:
        i = i + 1
        print()
        name = data["username"]
        dob = data["date_of_birth"]
        mob = data["month_of_birth"]
        pin = data["pin"]
        masterp = data["passwords"]["masterpass"]
        passes = len(list(data["passwords"].keys())) - 1
        pinky_table.add_row([i, name, dob, mob, pin, masterp, passes])

    print(pinky_table)

    print()
    print("   You will be returned after 9 seconds.")
    time.sleep(9.0)


def fn_get_user_names(list_of_data):
    nameslist = []
    for data in list_of_data:
        name_of_user = data["username"]
        nameslist.append(name_of_user)
    return nameslist


def fn_savetext(selected_user_data):
    user_name = (selected_user_data["username"])
    filename = user_name + "_data" + ".txt"
    file_obj = open(filename, "w")
    list_of_passw = []
    index = 1
    file_obj.write(" USER :" + "\t" + user_name + "\n\n")
    file_obj.write(" Saved passwords of " + user_name + ": \n\n")
    for old_account, passw in (selected_user_data["passwords"]).items():
        if old_account == "masterpass":
            continue
        file_obj.write("      " + str(index) + " ~ " +
                       old_account + " : " + passw + "\n\n")
        index = index + 1
        list_of_passw.append(passw)
    if list_of_passw == []:
        file_obj.write()
        file_obj.write("       ~ You don't have any passwords yet...")
    file_obj.close()


def fn_copy_pass(copy_index, selected_user_data):
    account_list = list(selected_user_data["passwords"].keys())
    passw_list = list(selected_user_data["passwords"].values())
    account_name = account_list[copy_index]
    passw_to_copy = passw_list[copy_index]
    clip.copy(passw_to_copy)
    fn_dialogue(f"Password Copied\n  {account_name}")


def fn_starting():
    displaylist = ['                                                          __',
                   '    ____   ____ _ _____ _____ _      __ ____   _____ ____/ /',
                   '   / __ \\ / __ `// ___// ___/| | /| / // __ \\ / ___// __  / ',
                   '  / /_/ // /_/ /(__  )(__  ) | |/ |/ // /_/ // /   / /_/ /  ',
                   ' / .___/ \\__,_//____//____/  |__/|__/ \\____//_/    \\__,_/   ',
                   '/_/____ ___   ____ _ ____   ____ _ ____ _ ___   _____       ',
                   '  / __ `__ \\ / __ `// __ \\ / __ `// __ `// _ \\ / ___/       ',
                   ' / / / / / // /_/ // / / // /_/ // /_/ //  __// /           ',
                   '/_/ /_/ /_/ \\__,_//_/ /_/ \\__,_/ \\__, / \\___//_/            ',
                   '                                /____/',
                   '                                         ',
                   '                                         '
                   ]
    for line in displaylist:
        print("    " + line)
        time.sleep(0.025)
    time.sleep(2.0)


def fn_progress_animation(message):
    for j in range(6):
        for i in range(6):
            print("\n" * 80)
            print(message + ("." * i))
            time.sleep(0.095)
    print("\n" * 80)


display_text = '''
                                                              __
        ____   ____ _ _____ _____ _      __ ____   _____ ____/ /
       / __ \ / __ `// ___// ___/| | /| / // __ \ / ___// __  /
      / /_/ // /_/ /(__  )(__  ) | |/ |/ // /_/ // /   / /_/ /
     / .___/ \__,_//____//____/  |__/|__/ \____//_/    \__,_/
    /_/____ ___   ____ _ ____   ____ _ ____ _ ___   _____
      / __ `__ \ / __ `// __ \ / __ `// __ `// _ \ / ___/
     / / / / / // /_/ // / / // /_/ // /_/ //  __// /
    /_/ /_/ /_/ \__,_//_/ /_/ \__,_/ \__, / \___//_/
                                    /____/

'''

try:
    user_database = psycopg2.connect(
        host="ec2-3-227-195-74.compute-1.amazonaws.com",
        user="kjadlvhespbcml",
        database="dbmin7uner1mlc",
        password="87bc0337fe5e930f062f219afc0f8822bf49ae94fd3518e87bbc152205c118dc",
    )
except:
    fn_animation("Can't Connect to Database")
    time.sleep(2.0)
    sql_connected = False


create_tb_query = '''CREATE TABLE IF NOT EXISTS users(
                        name VARCHAR(20),
                        date_of_birth VARCHAR(3),
                        month_of_birth VARCHAR(4),
                        pin VARCHAR(30));'''
cursor_obj = user_database.cursor()
cursor_obj.execute(create_tb_query)
user_database.commit()

sql_connected = True
fn_progress_animation("Connecting to database")

fn_starting()

while sql_connected:
    print("\n"*80)
    print(display_text)
    listOfData = fn_get_users_data()
    listOfNames = fn_get_user_names(listOfData)
    newUser = False
    LoggedIn = False
    saved_users = "    @ Saved Users : " + str(len(listOfNames))
    print(saved_users)
    print()
    print("    @ Enter username to login    //    'newuser' to create a new account :\n\n")
    print()
    resp = input("    : ")

    if resp.lower() == "newuser":
        fn_dialogue("Creating New User")
        print("\n" * 80)
        name, dob, mob, pin = fn_new_user(listOfData)
        if name == "logout":
            continue
        if name is None:
            continue
        userDictData = fn_make_user_data(name, dob, mob, pin)
        selectedUserData = userDictData
        fn_dump_user_data(selectedUserData)
        LoggedIn = True

    elif resp in listOfNames:
        userIndex = listOfNames.index(resp) + 1
        selectedUserData = fn_selected_user_data(userIndex, listOfData)
        if selectedUserData is None:
            fn_animation("User does\n  not exist.")
            continue
        LoggedIn = fn_existing_user(selectedUserData)

    elif resp.lower() == "--clear":
        fn_dialogue("Clearing All\n  Users Data")
        fn_clear_sql(listOfData)
        continue

    elif resp.lower() == "--pinky":
        fn_dialogue("Getting All\n  Users Data")
        fn_pinky(listOfData)
        continue

    else:
        fn_animation("Invalid Response:\n  No User Saved")

    if LoggedIn == "logout":
        continue

    first_run = True
    show_pass = False
    help_user = False
    while LoggedIn:

        if first_run:
            fn_dialogue("       Logging in\n         As " + selectedUserData["username"])
            first_run = False

        fn_display_user_passwords(selectedUserData, show_pass)
        show_pass = False
        print("_" * 96)
        print()
        user_text = '''
       @ 'newpass' creates secure key              //    'update <index>' to update the password

       @ 'supernewpass' creates super-secure key   //    'delete <index>' to delete the password

       @ 'logout' to log yourself out              //    'save' to save all passwords as txt file

       @ 'show' to show all the passwords          //    'copy <index>' to copy the password
    '''
        if help_user:
            print(user_text)
            help_user = False
        sec_resp = input("\t: ")

        if "newpass" in sec_resp.lower():
            fn_dialogue("Creating New Password")
            run = True
            while run:
                account_valid = False
                username_valid = False
                while not account_valid:
                    print()
                    print(
                        "   @ Type the account for the password : (Google, Netflix, Amazon, Instagram...)")
                    print()
                    account = input("\t : ")
                    if account == "" or account.isspace():
                        fn_animation("Invalid Account")
                        continue
                    account_valid = True

                while not username_valid:
                    print()
                    print(
                        "   @ Type the username for the account : (Muhriz Ali, Julie_M , poonam236, PrinceKS...)")
                    print()
                    username = input("\t : ")
                    print()
                    if username == "" or username.isspace():
                        fn_animation("Invalid Username")
                        continue
                    username_valid = True
                accountName = account.upper() + "/" + username
                accountExists = fn_password_exists(accountName, 
                                                   selectedUserData)
                if not accountExists:
                    listOfData = fn_create_new_pass(
                        sec_resp, accountName, selectedUserData, listOfData)
                    run = False

        elif "update" in sec_resp.lower():
            update_options = sec_resp.split()
            try:
                updateAccountIndex = int(update_options[1])
            except ValueError:
                fn_animation("Invalid Response")
                continue
            accountList = list(selectedUserData["passwords"].keys())
            if updateAccountIndex >= len(accountList) or updateAccountIndex <= 0:
                fn_animation("Account does\n  not exist.")
                continue
            listOfData = fn_update_pass(updateAccountIndex, 
                                        selectedUserData, 
                                        listOfData)

        elif "delete" in sec_resp.lower():
            delete_options = sec_resp.split()
            try:
                deleteAccountIndex = int(delete_options[1])
            except ValueError:
                fn_animation("Invalid Response")
                continue
            accountList = list(selectedUserData["passwords"].keys())
            if deleteAccountIndex >= len(accountList) or deleteAccountIndex <= 0:
                fn_animation("Account does\n  not exist.")
                continue
            listOfData = fn_delete_pass(
                deleteAccountIndex, selectedUserData, listOfData)

        elif "copy" in sec_resp.lower():
            copy_options = sec_resp.split()
            try:
                copyAccountIndex = int(copy_options[1])
            except ValueError:
                fn_animation("Invalid Response")
                continue
            accountList = list(selectedUserData["passwords"].keys())
            if copyAccountIndex >= len(accountList) or copyAccountIndex <= 0:
                fn_animation("Account does\nnot exist.")
                continue
            fn_copy_pass(copyAccountIndex, selectedUserData)

        elif sec_resp.lower() == "save":
            fn_dialogue("Saving Passwords\n  as Text file.")
            fn_savetext(selectedUserData)
            continue

        elif sec_resp.lower() == "show":
            if sec_resp.lower() == "show":
                show_pass = True
            else:
                continue
        elif sec_resp.lower() == "logout":
            fn_dialogue("      Logging Out")
            LoggedIn = False

        elif sec_resp.lower() == "-help":
            help_user = True
        else:
            fn_animation("Invalid Response")
