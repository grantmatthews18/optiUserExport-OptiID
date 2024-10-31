import requests
import sys
import csv
import os
import json

# globals
# organizationID = o_input("Organization ID: ")
organizationID = ""
# authorization = o_input("Authorization: ")
authorization = ""

def o_input(message):
    userInput = input(message)
    if(userInput == "exit"):
        exit()
    return userInput

def print_help(type = ""):
    
    help_text = """
    Opti ID User Management CLI Help:

    Commands:
    help                - Show this help message
    ls users [fields]   - List users with optional fields (default: Email). Type 'help fields' for valid fields.
    ls groups [fields]  - List groups with optional fields (default: Name). Type 'help fields' for valid fields.
    save users <path>   - Save users to a CSV file at the specified path
    save groups <path>  - Save groups to a CSV file at the specified path
    add user            - Add a single user interactively
    add users <path>    - Add multiple users using a CSV file at the specified path
    rm user             - Remove a single user interactively
    rm users <path>     - Remove multiple users using a CSV file at the specified path
    exit                - Exit the CLI
    """

    fields_help_text = """
    Opti ID User Management Fields Help:

    Commands:
    help fields       - Show this help message
    ls users [fields]   - List users with optional fields (default: Email). Type Help --fields for valid fields.
    ls groups [fields]  - List groups with optional fields (default: Name). Type Help --fields for valid fields.
    
    Note:
    - User Fields for 'ls users' can be any of the following:
        - * (All fields)
        - ExternalStatus
        - Id
        - ExternalUserId
        - Email
        - FirstName
        - LastName
        - HomeOrganizationId
        - UserGroupIds
        - LastLoggedIn
        - Created
        - Modified
        - Properties
        - links
    - Group Fields for 'ls groups' can be any of the following:
        - * (All fields)
        - Id
        - Name
        - Description
        - OrganizationId
        - GroupOwner
        - UserCount
        - GroupType
        - Properties
        - InstancePermissions
        - Created
        - Modified
        - Links
    - Fields are specified individually. For example: 'ls users Email FirstName LastName'
    """

    if type == "":
        print(help_text)
    elif type == "fields":
        print(fields_help_text)

def api_users(headers = {}, queryParams = []):
    try:

        url = 'https://usermgmt-api.optimizely.com/api/users'

        if len(queryParams) > 0:
            url += '?'
            url += '&'.join(queryParams)

        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def api_groups(headers = {}, queryParams = []):
    try:

        url = 'https://usermgmt-api.optimizely.com/api/usergroups'

        if len(queryParams) > 0:
            url += '?'
            url += '&'.join(queryParams)

        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def ls_users(fields = ['Email']):
    queryParams = [
        f'organizationId={organizationID}',
        'includeExternalStatus=true',
        'matchAnyUserGroups=true',
        'size=50'
    ]

    headers = {
        'Authorization': 'bearer ' + authorization,
        "Content-Type": "application/json",
        "cache-control": "no-cache"
    }
    firstResponse = api_users(headers, queryParams + ['offset=0'])
    
    users = firstResponse['items']

    totalUserCount = firstResponse['totalItemCount']

    if(totalUserCount > 50):
        for i in range(50, totalUserCount, 50):
            response = api_users(headers, queryParams + [f'offset={i}'])
            users += response['items']


    if users:
        if(fields == ['*']):
            return users
        elif(len(fields) == 1):
            return [user[fields[0]] for user in users]
        else:
            missing_fields = [field for field in fields if field not in users[0]]
            if missing_fields:
                print(f"Error: The following fields are missing in the user data: {', '.join(missing_fields)}")
                return
            if 'Id' not in fields:
                fields.append('Id')
                filtered_users = [{field: user[field] for field in fields if field in user} for user in users]
                return filtered_users
    else:
        print("No users found.")
        return

def ls_groups(fields = ['Name']):
    queryParams = [
        f'organizationId={organizationID}',
        'size=50'
    ]

    headers = {
        'Authorization': 'bearer ' + authorization,
        "Content-Type": "application/json",
        "cache-control": "no-cache"
    }
    firstResponse = api_groups(headers, queryParams + ['offset=0'])
    
    groups = firstResponse['items']

    totalGroupCount = firstResponse['totalItemCount']

    if(totalGroupCount > 50):
        for i in range(50, totalGroupCount, 50):
            response = api_groups(headers, queryParams + [f'offset={i}'])
            groups += response['items']

    if groups:
        if(fields == ['*']):
            return groups
        elif(len(fields) == 1):
            return [group[fields[0]] for group in groups]
        else:
            missing_fields = [field for field in fields if field not in groups[0]]
            if missing_fields:
                print(f"Error: The following fields are missing in the user data: {', '.join(missing_fields)}")
                return
            if 'Id' not in fields:
                fields.append('Id')
                filtered_groups = [{field: group[field] for field in fields if field in group} for group in groups]
                return filtered_groups
    else:
        print("No groups found.")
        return

def ls(command_args = []):
    
    if(len(command_args) == 0):
        print("No arguments provided. Type 'help' for a list of arguments")
    elif(command_args[0] == 'users'):
        if(len(command_args) > 1):
            items = ls_users(command_args[1:])
        else:
            items = ls_users()
    elif(command_args[0] == 'groups'):
        if(len(command_args) > 1):
            items = ls_groups(command_args[1:])
        else:
            items = ls_groups()
    
    for item in items:
        if isinstance(item, dict):
            print('Id: ' + item['Id'])
            for key in item:
                if(key != 'Id'):
                    print(f"|-{key}: {item[key]}")
        else:
            print(item)


def save_groups(path, forCLI = False):
    
    groups = ls_groups(['*'])
    
    if not groups:
        return
    
    keys = groups[0].keys()
    with open(path, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(users)

def save_users(path, forCLI = False):
    
    users = ls_users(['*'])

    if not users:
        return

    keys = users[0].keys()
    with open(path, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(users)

def save(command_args = []):
    if(len(command_args) == 0):
        print("No arguments provided. Type 'help' for a list of arguments")
    elif(command_args[0] == 'users'):
        if(len(command_args) == 2):
            save_users(command_args[1])
        elif(len(command_args) == 1):
            print("No path provided. Type 'help' for a list of arguments")
        else:
            print("Too many arguments provided. Type 'help' for a list of arguments")
    elif(command_args[0] == 'groups'):
        if(len(command_args) == 2):
            save_groups(command_args[1])
        elif(len(command_args) == 1):
            print("No path provided. Type 'help' for a list of arguments")
        else:
            print("Too many arguments provided. Type 'help' for a list of arguments")
    else:
        print(f"Command '{command_args[0]}' not found. Type 'help' for a list of arguments")


def api_invations(headers = {}, queryParams = [], body = {}):
    try:

        url = 'https://usermgmt-api.optimizely.com/api/invitations'

        if len(queryParams) > 0:
            url += '?'
            url += '&'.join(queryParams)

        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()  # Raise an error for bad status codes
        return response
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None    

def add_users(path):

    if not os.path.exists(path):
        print(f"File {path} does not exist.")
        return

    users = []
    with open(path, mode='r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) < 4:
                print(f"Invalid row: {row}. Each row must have at least 4 columns.")
                continue
            else:
                userInfo = {}
                userInfo["email"] = row[0]
                userInfo["firstName"] = row[1]
                userInfo["lastName"] = row[2]

                requireAcceptance = row[3].strip().lower() == 'true'

                groups = row[4:]

                users.append({
                    "userInfo": userInfo,
                    "groups": groups,
                    "requireAcceptance": requireAcceptance
                })

    for user in users:
        success = add_single_user(user["userInfo"], user["groups"], user["requireAcceptance"])
        if not success:
            print(f"Failed to add user: {user['userInfo']['email']}")
            return
        else:
            print(f"User {user['userInfo']['email']} added successfully.")
    
def add_single_user(userInfo = {}, groups = [], requireAcceptance = True):
    queryParams = [
    ]

    headers = {
        'Authorization': 'bearer ' + authorization,
        "Content-Type": "application/json",
        "cache-control": "no-cache"
    }

    body = {
        "createdBy": "",
        "email": userInfo["email"],
        "firstName": userInfo["firstName"],
        "lastName": userInfo["lastName"],
        "organizationId": organizationID,
        "requireAcceptance": requireAcceptance,
        "sentDates": [],
        "userGroupIds": groups
    }

    response = api_invations(headers, queryParams, body)

    if response.status_code >= 200 & response.status_code < 300:
        return True
    else:
        return False

def helper_input_loop(type, message):
    if type == "email":
        while True:
            email = o_input(message)
            if '@' in email and '.' in email:
                return email
            else:
                print("Invalid email address. Please try again.")
    else:
        while True:
            value = o_input(message)
            if value != "":
                return value
            else:
                print("Nothing Inputed. Please try again.")

def helper_group_input_loop():
    groups = []
    while True:
        group = o_input("Group ID: ")
        if group == "":
            break
        groups.append(group)
    
    if len(groups) == 0:
            confirm = o_input("No groups added. Ok? (y/n): ")
            if confirm == "n":
                groups = helper_group_input_loop()
    
    return groups

def add(command_args = []):
    
    if(len(command_args) == 0):
        print("No arguments provided. Type 'help' for a list of arguments")
    elif(command_args[0] == 'user'):
        userInfo = {}
        userInfo["email"] = helper_input_loop("email", "Email: ")
        userInfo["firstName"] = helper_input_loop("text", "First Name: ")
        userInfo["lastName"] = helper_input_loop("text", "Last Name: ")

        groups= helper_group_input_loop()

        requireAcceptance = helper_input_loop("text", "Require Acceptance? (y/n): ")

        if requireAcceptance == "n":
            requireAcceptance = False
        else:
            requireAcceptance = True
   
        success = add_single_user(userInfo, groups, requireAcceptance)
        
        if success:
            print(f"User {userInfo['email']} added successfully.")
        else:
            print("Failed to add user.")

    elif(command_args[0] == 'users'):
        if(len(command_args) == 2):
            add_users(command_args[1])
        elif(len(command_args) == 1):
            print("No path provided. Type 'help' for a list of arguments")
        else:
            print("Too many arguments provided. Type 'help' for a list of arguments")
    else:
        print(f"Command '{command_args[0]}' not found. Type 'help' for a list of arguments")
    

def api_users_delete(headers = {}, queryParams = [], email = ""):
    try:

        url = f'https://usermgmt-api.optimizely.com/api/users/{email}'

        if len(queryParams) > 0:
            url += '?'
            url += '&'.join(queryParams)

        response = requests.delete(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        return response
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def rm_users(path):
    if not os.path.exists(path):
        print(f"File {path} does not exist.")
        return

    users = []
    with open(path, mode='r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) == 1:
                print(f"Invalid row: {row}. Each row must have 1 column (email).")
                continue
            else:
                users.append(row[0].strip().lower())

    for user in users:
        success = rm_single_user(user)
        if not success:
            print(f"Failed to remove user: {user}")
            return
        else:
            print(f"User {user} removed successfully.")

def rm_single_user(email):
    queryParams = [
    ]

    headers = {
        'Authorization': 'bearer ' + authorization,
        "Content-Type": "application/json",
        "cache-control": "no-cache"
    }

    response = api_users_delete(headers, queryParams, email)

    if response.status_code >= 200 & response.status_code < 300:
        return True
    else:
        return False

def rm(command_args = []):

    if(len(command_args) == 0):
        print("No arguments provided. Type 'help' for a list of arguments")
    elif(command_args[0] == 'user'):
        email = helper_input_loop("email", "Email: ")
        success = rm_single_user(email)
        if success:
            print(f"User {email} removed successfully.")
        else:
            print("Failed to remove user.")
    elif(command_args[0] == 'users'):
        if(len(command_args) == 2):
            rm_users(command_args[1])
        elif(len(command_args) == 1):
            print("No path provided. Type 'help' for a list of arguments")
        else:
            print("Too many arguments provided. Type 'help' for a list of arguments")
    else:
        print(f"Command '{command_args[0]}' not found. Type 'help' for a list of arguments")
    

def extract_credentials(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File {path} does not exist.")

    with open(path, 'r') as file:
        credentials = json.load(file)

    if 'organizationID' not in credentials or 'authorization' not in credentials:
        print("The provided file does not contain the required credentials.")
        exit()

    global organizationID, authorization
    organizationID = credentials['organizationID']
    authorization = credentials['authorization']
    return True

if __name__ == "__main__":

    print("Opti ID User Management CLI")
    print("Type 'help' for a list of actions")

    if(len(sys.argv) <= 1):
        print("No Credentials provided.")
        print("Please provide the Organization ID and Authorization Token.")
        print("For More information, see the GitHub Repository: https://github.com/grantmatthews18/optiUserExport-OptiID")
        exit()
    else:
        success = extract_credentials(sys.argv[1])
        if success:
            print("Credentials successfully extracted. Starting CLI...")

    while True:
        
        userInput = o_input("$ ")

        if userInput == "":
            continue
        else:
            inputTokens = userInput.split(' ')

            flags = []
            command = None
            command_args = []

            for token in inputTokens:
                if token.startswith('-'):
                    flags.append(token)
                elif command is None:
                    command = token
                else:
                    command_args.append(token)

            if(command == 'help'):
                print(command_args)
                print_help(command_args[0] if len(command_args) > 0 else "")
            elif(command == 'ls'):
                ls(command_args)
            elif(command == 'save'):
                save(command_args)
            elif(command == 'add'):
                add(command_args)
            elif(command == 'rm'):
                rm(command_args)
            elif(command == 'exit'):
                exit()
            else:
                print(f"Command '{command}' not found. Type 'help' for a list of actions")
