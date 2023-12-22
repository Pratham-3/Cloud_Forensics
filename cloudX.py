import datetime
import os
import mimetypes
from mega import Mega
import sqlite3
import time
import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET
import json
import webbrowser
import subprocess
import re

db_file = 'C:/Users/Pratham Sharma/ownCloud - admin@localhost/.sync_journal.db'

BASE_URL = 'http://localhost:8080'
USERNAME_OC = 'admin'
PASSWORD_OC = 'admin'

def login_owncloud(username, password):
    auth_url = f'{BASE_URL}/ocs/v2.php/cloud/user?format=json'
    response = requests.get(auth_url, auth=HTTPBasicAuth(username, password))

    if response.status_code == 200:
        print('Authentication successful')
        return True
    else:
        print('Authentication failed. Check your credentials or server URL.')
        exit()


def retrieve_server_info(username, password):
    server_info_url = f'{BASE_URL}/status.php'
    server_info_response = requests.get(server_info_url, auth=(username, password))
    
    if server_info_response.status_code == 200:
        server_info = server_info_response.json()
        print("Server Information:")
        formatted_server_info = json.dumps(server_info, indent=4)
        print(formatted_server_info)
        print()
    else:
        print(f"Failed to fetch server information. Status code: {server_info_response.status_code}")


def shared_item_info(username, password):
    auth_url = f'{BASE_URL}/ocs/v2.php/cloud/user?format=json'
    response = requests.get(auth_url, auth=HTTPBasicAuth(username, password))

    share_url = f'{BASE_URL}/ocs/v2.php/apps/files_sharing/api/v1/shares'
    share_response = requests.get(share_url, cookies=response.cookies)
    
    print("Shared Items Informations:")
    try:
        share_data = ET.fromstring(share_response.content)
        for element in share_data.findall('.//element'):
            print('Shared Item ID:', element.find('id').text)
            print('Owner:', element.find('uid_owner').text)
            print('Sharing Type:', element.find('share_type').text)
            if element.find('share_type').text == '0':
                print('Shared With:', element.find('share_with').text)
                print('Item Type:', element.find('mimetype').text)
                print('Item Name:', element.find('file_target').text)
                print('Permissions:', element.find('permissions').text)
                # ... (other fields)
                print()
            elif element.find('share_type').text == '3':
                print('Public link:', element.find('url').text)
                print('Item Type:', element.find('mimetype').text)
                print('Item Name:', element.find('file_target').text)
                print('Permissions:', element.find('permissions').text)
                # ... (other fields)
                print()
    except ET.ParseError:
        print('Failed to parse response as XML. Response content:')
        print(share_response.text)


def retrieve_server_logs(username, password):
 print("downloading server logs...")
 url = "http://localhost:8080/settings/admin/log/download"  

 webbrowser.open(url)
 print("server logs downloaded successfully")


def extract_info_from_mega():
    
    mega = Mega()

    # email = input("Enter Email:")
    # password = input("Enter Password:")

    email = 'sharma.pratham2001@gmail.com'
    password = 'pratham@1'

    m = mega.login(email, password)
    
    file_link = 'https://mega.nz/file/fcwnWaCJ'
    file_key = 'yGPYU4bDjQF6YAwCQOZ5C_tKqolrTbKaV4zQacOPv3s'

    user_info = m.get_user()
    username = user_info.get('name')

    files = m.get_files()
    # print(files)

    quota = m.get_quota()
    space = m.get_storage_space(giga=True)

    print("Account disk quota:", quota, "MB")
    print("Account used storage space:", space['used'], "MB")
    print("Account remaining storage space:", quota - space['used'], "MB")
    print("\n")


    for item_id, item_data in files.items():
        item_type = item_data['t']
        item_name = item_data['a']['n']
        item_size = item_data['s'] if 's' in item_data else None
        item_timestamp = item_data['ts'] if 'ts' in item_data else None
        unique_identifier = item_data['h'] 
        initialization_vector = item_data['iv'] if 'iv' in item_data else None 
        user_identifier = username + ", " + item_data['u']
        content_key = item_data['a']['c'] if 'a' in item_data and 'c' in item_data['a'] else None
        keys = item_data['key'] if 'key' in item_data else None
        mac = item_data['meta_mac'] if 'meta_mac' in item_data else None


        date_time = datetime.datetime.fromtimestamp(item_timestamp)
        formatted_date_time = date_time.strftime('%Y-%m-%d %H:%M:%S')

        print("Item Name:", item_name)
        print("Unique Identifier:", unique_identifier)
        print("User Identifier:", user_identifier)
        print("Type:", "File" if item_type == 0 else "Folder")
        if item_type == 0:  
            print("Size:", item_size, "bytes")
        print("Timestamp:", formatted_date_time)
        if content_key:
            print("Content Key:", content_key)

        if keys:
            print("encryption and decryption Keys:", keys)
        
        if initialization_vector:
            print("initialization vector:", initialization_vector)

        if mac:
            print("Message authentication code:", mac)
        
        print()



    # print(files)

    # Get the file metadata
    # file = m.get_public_file_info(file_link, file_key)

    # # Print the metadata
    # print("File Name:", file.name)
    # print("File Size:", file.size)
    # print("File ID:", file.id)
    # print("File Node ID:", file.node_id)


def find_owncloud_directory():
    common_paths = [
        os.path.expanduser("~\ownCloud - admin@localhost"), 
        "\mnt\data\ownCloud", 
    ]

    for path in common_paths:
        if os.path.exists(path):
            return path 

    return None



# Define a function to check the shared status
# def is_shared(file_path):
#     remote_path = file_path.replace('\\', '/').replace('C:/Users/Pratham Sharma/', '')
#     response = client.info(remote_path)
#     return response.get('shared', False)

def try_execute_query(query, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            conn.close()
            return results
        except sqlite3.OperationalError as e:
            print(f"Error: {e}. Retrying...")
            retries += 1
            time.sleep(1)  # Wait for a short period before retrying
    print("Max retries reached. Unable to execute the query.")
    return []


def extract_info_from_owncloud(path):
    

    contents = os.listdir(path)

    # for item in contents:
    #     item_path = os.path.join(path, item)
    #     is_directory = os.path.isdir(item_path)
    #     item_size = os.path.getsize(item_path) if not is_directory else 0
    #     item_modified = os.path.getmtime(item_path)
    #     item_owner = os.stat(item_path).st_uid
    #     item_permissions = oct(os.stat(item_path).st_mode & 0o777)
    #     item_group = os.stat(item_path).st_gid
    #     # file_type = "Directory" if is_directory else determine_file_type(item_path)
    #     # shared = is_shared(item_path)
    #     if not is_directory:
    #         # Determine the file type using mimetypes
    #         mime_type, _ = mimetypes.guess_type(item_path)
    #         file_type = mime_type if mime_type else "Unknown"
    #     else:
    #         file_type = "Directory"

    

        # print(f"Item Name: {item}")
        # print(f"Is a directory: {is_directory}")
        # print(f"Size: {item_size} bytes")
        # print(f"Last Modified: {item_modified_formatted}")
        # print(f"Owner: {item_owner}")
        # print(f"Permissions: {item_permissions}")
        # print(f"Group: {item_group}")
        # print(f"File Type: {file_type}")
        # # print(f"Shared: {shared}")
        # print("\n")

    tables = try_execute_query("SELECT name FROM sqlite_master WHERE type='table';")
    # for table in tables:
    #      print(table[0])

        # Retrieve and print information from the "metadata" table
    metadata_results = try_execute_query('SELECT * FROM metadata')
    for row in metadata_results:
            phash, pathlen, path, inode, uid, gid, mode, modtime, item_type, md5, fileid, remote_perm, filesize, ignored_children_remote, content_checksum, content_checksum_type_id, has_dirty_placeholder = row
            
            date_time = datetime.datetime.fromtimestamp(modtime)
            item_modified_formatted = date_time.strftime('%Y-%m-%d %H:%M:%S')
            # Include additional information in the printout
            print("phash:", phash)
            print("pathlen:", pathlen)
            print("path:", path)
            print("inode:", inode)
            print("uid:", uid)
            print("gid:", gid)
            print("mode:", mode)
            print("modtime:", item_modified_formatted)
            print("item_type:", item_type)
            print("md5:", md5)
            print("fileid:", fileid)
            print("remote_perm:", remote_perm)
            print("filesize:", filesize)
            print("ignored_children_remote:", ignored_children_remote)
            print("content_checksum:", content_checksum)
            print("content_checksum_type_id:", content_checksum_type_id)
            print("has_dirty_placeholder:", has_dirty_placeholder)
            print("Full Row:", row)
            print()
        

    # if is_directory:
    #     extract_info_from_owncloud(item_path)


def get_and_save_container_logs(container_name_or_id, output_file):
    try:
        # Run the docker logs command
        logs_command = f"docker logs {container_name_or_id}"
        logs_process = subprocess.Popen(logs_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logs_output, logs_error = logs_process.communicate()

        # Check if there was an error
        if logs_process.returncode != 0:
            raise Exception(f"Error retrieving logs: {logs_error.decode('utf-8')}")

        # Save the logs to a file
        with open(output_file, 'w') as file:
            file.write(logs_output.decode('utf-8'))

        print(f"Logs saved to {output_file}")

    except Exception as e:
        print(f"Error: {e}")


def finding_deleted_files(log_file_path):
    log_pattern = re.compile(r'.*DELETE\s+([^\s]+)\s+HTTP.*')

    # Open the log file and extract deleted file names
    deleted_files = []
    with open(log_file_path, 'r') as log_file:
        for line in log_file:
            match = log_pattern.match(line)
            if match:
                deleted_file = match.group(1)
                file = deleted_file.split('/')
                file.reverse()
                # You might want to decode URL-encoded characters in the file name
                deleted_files.append(file[0])

    # Print the list of deleted file names
    print("Deleted files:")
    for file_name in deleted_files:
        print(file_name)


def main():
    print("Choose a platform:")
    print("1. Mega")
    print("2. OwnCloud")
    choice = input("Enter the platform number: ")

    if choice == '1':
        extract_info_from_mega()
    elif choice == '2':
        print("1. Client side information")
        print("2. Server side information")
        print("3. Extract deleted files")
        choice = input("Enter the information type number: ")

        if choice == '1':
            directory_path = find_owncloud_directory()
            if directory_path:
             print(f"OwnCloud directory found at: {directory_path}")
             extract_info_from_owncloud(directory_path)
            else:
                print("ownCloud directory not found")
        elif choice == '2':
            if login_owncloud(USERNAME_OC, PASSWORD_OC):
             retrieve_server_info(USERNAME_OC, PASSWORD_OC)
             shared_item_info(USERNAME_OC, PASSWORD_OC)
             retrieve_server_logs(USERNAME_OC, PASSWORD_OC)
        elif choice == '3':
             container_name_or_id = "10e3fed681ff8f99e0d6f5ece34eabc4fcaea4005457e9e865e41730aa0ff1f7"
             output_file = "C:/Users/Pratham Sharma/Desktop/logs.txt"

             get_and_save_container_logs(container_name_or_id, output_file)
             finding_deleted_files(output_file)     
        else:
         print("Invalid choice. Please enter 1 for client side information or 2 for server side information.")

    else:
        print("Invalid choice. Please enter 1 for Mega or 2 for OwnCloud.")

if __name__ == '__main__':
    main()