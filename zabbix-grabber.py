import argparse
import re
import json
import requests
import sys
import os
from bs4 import BeautifulSoup
from datetime import datetime

version = ""
store_file = False
plain_structure = False

# Print banner
def print_banner():
    banner_lines = [
        "\033[35m  ______     _     _     _         _____           _     _               ",
        " |___  /    | |   | |   (_)       / ____|         | |   | |              ",
        "    / / __ _| |__ | |__  ___  __ | |  __ _ __ __ _| |__ | |__   ___ _ __ ",
        "   / / / _` | '_ \\| '_ \\| \\ \\/ / | | |_ | '__/ _` | '_ \\| '_ \\ / _ \\ '__|",
        "  / /_| (_| | |_) | |_) | |>  <  | |__| | | | (_| | |_) | |_) |  __/ |   ",
        " /_____\\__,_|_.__/|_.__/|_/_/\\_\\  \\_____|_|  \\__,_|_.__/|_.__/ \\___|_|  \033[0m",
    ]

    for line in banner_lines:
        print(line)
    print("\n\033[33mBy: rM3ofM3\033[0m")

# Logon and create session to Zabbix
def login_to_zabbix(base_url, username, password):
    # Global variables declaration
    global version

    login_url = f"{base_url}/index.php"

    session = requests.Session()

    payload = {
        "name": username,
        "password": password,
        "autologin": "1", 
        "enter": "Sign in"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"
    }

    # POST request to logon form

    print(f"Connecting to {base_url} using {username}:{password}.")
    try:
        response = session.post(login_url, data=payload, headers=headers)
        if "Dashboard" in response.text:
            # Search version
            match = re.search(r'https://www\.zabbix\.com/documentation/(\d+\.\d+)/', response.text)
            if match:
               version = match.group(1)
            print(f"\033[32m[Successful logon to Zabbix version {version}.]\033[0m\n")
            if version not in {"6.4","7.0"}:
               print("\033[33m[Zabbix version not supported.]\33[0m\n")
               return None
            else:
               return session
        else:
            print("\033[31m[Zabbix logon session error. Check your credentials or URL.]\033[0m\n")
            return None
    except:
        print("\033[31m[Connection timeout.]\033[0m\n")


# List Zabbix registered hosts
def list_hosts(session, base_url, only_up=False):
  global version
  lastpage = False
  page = 1
  print("Zabbix agents list:")
  hosts = []

  # Loop to fund multiple pages
  while not lastpage:
    hosts_url = f"{base_url}/zabbix.php?action=host.list&page={page}&filter_host=&filter_dns=&filter_ip=&filter_port=&filter_status=-1&filter_monitored_by=0&filter_evaltype=0&filter_tags%5B0%5D%5Btag%5D=&filter_tags%5B0%5D%5Boperator%5D=0&filter_tags%5B0%5D%5Bvalue%5D=&filter_set=1"
    # Request
    response = session.get(hosts_url)
    if response.status_code != 200:
        print(f"Error accessing to hosts page. HTTP error code: {response.status_code}")
        return

    # Analyze HTML code
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", {"class": "list-table"})
    if not table:
        print("Unable to find hosts list in the page.")
        return

    # Extract and show hosts
    for row in table.find_all("tr")[1:]: # Discard header
        cols = row.find_all("td")
        if len(cols) > 6:  # Check we have enogh columns
            # Obtain host ID
            checkbox = cols[0].find("input", {"type": "checkbox"})
            host_id = checkbox["value"] if checkbox else "N/A"

            # If the host_id already exists into the array, it means that the previous page was the last one
            if any(hosts_items["host_id"] == host_id for hosts_items in hosts):
              lastpage = True
            else:
              # Obtain hostname
              link = cols[1].find("a")
              host_name = link.get_text(strip=True) if link else "N/A"

              address = cols[7].text
              match = re.search(r':(\d+)$', address)
              port = match.group(1)

              status_content = cols[11].find("span", {"class": "status-green"})
              status = "\033[32mUp\033[0m" if status_content else "\033[31mDown\033[0m"

              hosts.append({"host_id": host_id})

              # Display only hosts using Zabbix Agent
              if port == "10050":
                 if not (only_up and status == "\033[31mDown\033[0m"):
                   print(f"- Host-ID: \033[33m{host_id}\033[0m, Host-name: {host_name}, Status: {status}")
    page = page + 1
    # If the first page contains no agents, it finishes the loop
    if len(hosts) == 0:
       lastpage = True
  return hosts

# Extract CSRF token, IP address and interface ID. The patterns work for all versions
def extract_csrf_token(html):
    soup = BeautifulSoup(html, "html.parser")
    # Search for CSRF token value
    csrf_input = soup.find("input", {"name": lambda name: name and "_csrf_token" in name})
    if csrf_input and 'value' in csrf_input.attrs:
        # Delete additional characters
        token = csrf_input['value'].replace('\\"', '')
    else:
        return None, None, None

    # Search for DNS name or IP address
    ip_pattern = r'"label":"Agent","options":\[{"value":"\d+","label":"([0-9a-zA-Z\.-_]+):\d+"'
    ip_match = re.search(ip_pattern, str(soup))
    ip_address = ip_match.group(1) if ip_match else None 

    # Search for interface ID
    intid_pattern = r'"label":"Agent","options":\[{"value":"(\d+)","label":"[0-9a-zA-Z\.-_]+:\d+"'
    intid_match = re.search(intid_pattern, str(soup))
    interface_id = intid_match.group(1) if intid_match else None
    #print (f"CSRF:{token}, address:{ip_address}, ID:{interface_id}") 

    if token!=None and ip_address!=None and interface_id !=None:
        return token, ip_address, interface_id

    print("Unable to find CSRF token, IP address or interface ID.")
    return None, None, None

# STEP 1: Request to "item.edit" to obtain CSRF token, agent IP address and interface ID
def get_csrf_token_for_item_creation(session, base_url, host_id):
    global version
    # We have different URL depending on version
    if version == "7.0":
        url = f"{base_url}/zabbix.php?action=item.edit"
    else:
       url = f"{base_url}/items.php?form=create&hostid={host_id}&context=host"
    payload = {
        "hostid": host_id,
        "context": "host"
    }

    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36",
        "Referer": f"{base_url}/zabbix.php?action=item.list&context=host&filter_set=1&filter_hostids%5B0%5D={host_id}"
    }

    # POST request
    response = session.post(url, data=payload, headers=headers)

    if response.status_code == 200:
        csrf_token, ip_address, interface_id = extract_csrf_token(response.text)
        if csrf_token:
            return csrf_token, ip_address, interface_id
        else:
            print("Could not find CSRF token, IP address or Interface ID. Check if host ID is valid.")
            return None, None, None
    else:
        print(f"item.edit request error. HTTP code: {response.status_code}")
        return None, None, None


# Extract CSRF token from 'popup.itemtest.edit'
def extract_csrf_token_from_popup(response_text):
    global version

    # Regular expression to find CSRF token depending on the Zabbix version
    if version == "7.0":
        csrf_pattern = r'url\.setArgument\(CSRF_TOKEN_NAME,\s*\\"([a-fA-F0-9]{64})\\"\)'
    else:
        csrf_pattern = r'url\.setArgument\(\'_csrf_token\',\s*\\"([a-fA-F0-9]{64})\\"\)'
    csrf_match = re.search(csrf_pattern, response_text)


    csrf_token = csrf_match.group(1) if csrf_match else None

    #print(f"Second token:{csrf_token}")
    if csrf_token:
        return csrf_token
    else:
        print("Fatal error obtaining popup CSRF token.")
        return None


# Paso 2: Requests to "popup.itemtest.edit" using first CSRF token and interface_id
def get_csrf_token_for_popup_itemtest(session, base_url, csrf_token, host_id, interface_id):
    url = f"{base_url}/zabbix.php?action=popup.itemtest.edit"
    payload = {
        "_csrf_token": csrf_token,
        "key": "vfs.dir.get["+base_url+",,,,,1,,,,,]",
        "timeout": "3s",
        "delay": "1m",
        "value_type": "4",
        "item_type": "0",
        "itemid": "0",
        "interfaceid": interface_id,
        "hostid": host_id,
        "test_type": "0",
        "step_obj": "-2",
        "show_final_result": "1",
        "get_value": "1"
    }

    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36",
        "Referer": f"{base_url}/zabbix.php?action=item.list&context=host&filter_set=1&filter_hostids%5B0%5D={host_id}"
    }

    # Post request to get second CSRF token
    response = session.post(url, data=payload, headers=headers)
    if response.status_code == 200:
        csrf_token_popup = extract_csrf_token_from_popup(response.text)
        if csrf_token_popup:
            return csrf_token_popup
        else:
            print("Unable to find CSRF token in the second step .")
            return None
    else:
        print(f"popup.itemtest.edit request error. HTTP code: {response.status_code}")
        return None

# List folder content
def list_folder_contents(session, base_url, csrf_token, host_id, ip_address, interface_id, base_path, recurse=0, regex="", dump=False):
    try:
        re.compile(regex)
    except re.error:
        print("Error: Invalid regular expression.")
        return False

    url = f"{base_url}/zabbix.php?action=popup.itemtest.send&_csrf_token={csrf_token}"
    payload = {
        "key": "vfs.dir.get["+base_path+","+regex+",,,,"+str(recurse)+",,,,,]",
        "timeout": "30s",
        "delay": "",
        "value_type": "4",
        "item_type": "0",
        "itemid": "0",
        "interfaceid": interface_id,
        "get_value": "1",
        "interface[address]": ip_address,
        "interface[port]": "10050",
        "test_with": "0",
        "show_final_result": "1",
        "test_type": "0",
        "hostid": host_id,
        "valuemapid": "0",
        "value": "",
        "runtime_error": ""
    }

    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36",
        "Referer": f"{base_url}/zabbix.php?action=item.list&context=host&filter_set=1&filter_hostids%5B0%5D={host_id}"
    }

    # Perform POST request
    response = session.post(url, data=payload, headers=headers)
    if response.status_code == 200:
        try:
            result = response.json()
            if "value" in result:
                # Don't show information if you're going to dump files
                if not dump:
                    print(f"Contents in '{base_path}' using {recurse} levels of recursivity:\n")
                    print(f"Regular expression filter: '{regex}'\n")
                contents = json.loads(result["value"])
                if recurse == 0:
                    sorted_contents = sorted(contents, key=lambda entry: (entry.get("type", "N/A") != "dir", entry.get("basename", "").lower()))
                else:
                    sorted_contents = contents
                for entry in sorted_contents:
                    basename = entry.get("basename", "N/A")
                    pathname = entry.get("pathname", "N/A")
                    dirname = entry.get("dirname", "N/A")
                    type_ = entry.get("type", "N/A")
                    user = entry.get("user", "N/A")
                    raw_change_date = entry.get("time", {}).get("change", "") 
                    if raw_change_date != None:
                        # Convert to desired format
                        try:
                            change_date = datetime.strptime(raw_change_date[:19], "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M")
                        except ValueError:
                            change_date = raw_change_date  # Fall back to raw value if parsing fails
                    else:
                        change_date = "                "
                    size = human_readable_size(entry.get("size", "N/A"))
                    if type_!="dir":
                        if dump:
                           get_file_content(session, base_url, csrf_token, host_id, ip_address, interface_id, dirname, basename, True, plain_structure)
                        else:
                           if recurse == 0:
                              print(f"{change_date}         {basename}  ({size})")
                           else:
                              print(f"{change_date}  {pathname}  ({size})")
                    elif recurse == 0:
                    	print(f"{change_date}   <DIR> {basename}")
            else:
                print("Error finding folder content or timeout.")
        except json.JSONDecodeError:
            print("Error processing server reply message. Invalid JSON formet.")
            print("Server response:", response.text)
    else:
        print(f"Request error. HTTP error code: {response.status_code}")

# Convert size to human readable format
def human_readable_size(size_in_bytes):
    if size_in_bytes == 0:
        return "0 B"
    sizes = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    while size_in_bytes >= 1024 and i < len(sizes) - 1:
        size_in_bytes /= 1024.0
        i += 1
    return f"{size_in_bytes:.2f} {sizes[i]}"

# Obtain separator character depending on operatin system notation
def get_separator(base_path):
    if base_path.endswith("/") or base_path.endswith("\\"):
        return ""
    elif "/" in base_path:
        return "/"
    elif "\\" in base_path:
        return "\\"
    return ""

# Obtain separator character depending on operating system notation
def get_separator(base_path):
    if base_path.endswith("/") or base_path.endswith("\\"):
        return ""
    elif "/" in base_path:
        return "/"
    elif "\\" in base_path:
        return "\\"
    return ""

# Ensure directory structure exists based on a given path
def ensure_directory_structure(base_dir, base_path):
    # Normalize path to use OS-specific separators
    if "\\" in base_path:
        path_parts = base_path.split("\\")
    else:
        path_parts = base_path.split("/")

    current_path = base_dir
    for part in path_parts:
        if part:  # Skip empty parts (e.g., leading or trailing slashes)
            current_path = os.path.join(current_path, part)
            if not os.path.exists(current_path):
                os.makedirs(current_path)
    return current_path

# List folder content
def get_file_content(session, base_url, csrf_token, host_id, ip_address, interface_id, base_path, file_name, store_file=False, plain_structure=False):

    url = f"{base_url}/zabbix.php?action=popup.itemtest.send&_csrf_token={csrf_token}"
    payload = {
        "key": "vfs.file.contents[" + base_path + get_separator(base_path) + file_name + ",]",
        "timeout": "30s",
        "delay": "",
        "value_type": "4",
        "item_type": "0",
        "itemid": "0",
        "interfaceid": interface_id,
        "get_value": "1",
        "interface[address]": ip_address,
        "interface[port]": "10050",
        "test_with": "0",
        "show_final_result": "1",
        "test_type": "0",
        "hostid": host_id,
        "valuemapid": "0",
        "value": "",
        "runtime_error": ""
    }

    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36",
        "Referer": f"{base_url}/zabbix.php?action=item.list&context=host&filter_set=1&filter_hostids%5B0%5D={host_id}"
    }

    # Perform POST request
    response = session.post(url, data=payload, headers=headers)

    if response.status_code == 200:
        try:
            result = response.json()
            if "value" in result:
                if store_file:
                    if plain_structure:
                       file_path = os.path.join(os.getcwd(),file_name)
                    else:
	               # Define base directory
                       base_dir = os.path.join(os.getcwd(), "ZGFiles", str(host_id))
	               # Ensure directory structure exists
                       final_directory = ensure_directory_structure(base_dir, base_path)
	               # Full file path
                       file_path = os.path.join(final_directory, file_name)
	            # Save the file
                    print(f"File '{base_path}{get_separator(base_path)}{file_name}' downloaded into '{file_path}'.")
                    with open(file_path, "w", encoding="utf-8") as file:
                        file.write(result["value"])
                else:
                    print(f"Content for file '{base_path + get_separator(base_path) + file_name}':\n")
                    print(result["value"])
            else:
                print(result.text)
        except Exception as e:
            print("Error processing server reply message.")
            print("Server response:", response.text)
            print("Exception:", e)
    else:
        print(f"Request error. HTTP error code: {response.status_code}")

# MAIN FUNCTION
def main():
    global plain_structure
    script_path = __file__
    print_banner()
    print("\n")
    # Command line arguments configuration
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Grab information from file system of Zabbix agents connected to a Zabbix server.",
        epilog="""
Examples of usage:

  1. List hosts from Zabbix server:
     python3 zabbix-grabber.py -U username -P password -A http://server/zabbix 

  2. List folder contents (by default it doesn't use recursivity):
     python3 zabbix-grabber.py -U username -P password -A http://server/zabbix -H HOST_ID -F folder_path

  3. Display file content (it must be plain text file):
     python3 zabbix-grabber.py -U username -P password -A http://server/zabbix -H HOST_ID -F folder_path -D file_name
"""
    )
    parser.add_argument("-A", "--base-url", required=True, help="Zabbix base URL (don't use /index.php).")
    parser.add_argument("-U", "--user", default="Admin", help="Username to connect to Zabbix.")
    parser.add_argument("-P", "--password", default="zabbix", help="Password to connect to Zabbix.")
    parser.add_argument("-H", "--host-id", help="Host ID used to list folder contents.")
    parser.add_argument("-F", "--base-path", help="Base folder from which we're goin to read contents.")
    parser.add_argument("-D", "--dump-file", help="File name to be dumped. This requires -F option.")
    parser.add_argument("-G", "--store-file", action="store_true", help="Store file localy into ZGFiles structure.")
    parser.add_argument("-L", "--recursive-levels", default="0", help="Levels of recursivity (default=0, max=5).")
    parser.add_argument("-R", "--regex", default="", help="Regular expression to find files into folders.")
    parser.add_argument("--only-up", action="store_true", help="Display only online and available agents.")
    parser.add_argument("--plain-structure", action="store_true", help="Used to download files in current folder. The scrip will not try to create ZGFiles/{HOST_ID} folder structure.")
    args = parser.parse_args()

    store_file = args.store_file
    if args.plain_structure:
        plain_structure = True

    if args.host_id and not args.base_path:
        parser.error("-F is required if you use -H.")
    elif args.base_path and not args.host_id:
        parser.error("-H is required if you use -F.")

    try:
        levels = int(args.recursive_levels)
    except ValueError:
        levels = 0

    if levels <0 or levels>5:
       print("\033[33mWarning: recursivity must be defined betwen 0 and 5. Now it has been estalished to 0.\033[0m")
       levels = 0

    # Logon request
    session = login_to_zabbix(args.base_url, args.user, args.password)
    if not session:
        return

    if args.host_id:
         # Obtaining CSRF token, address and interface ID
         csrf_token_item, ip_address, interface_id = get_csrf_token_for_item_creation(session, args.base_url, args.host_id)
         if csrf_token_item:
             # Obteining second CSRF token
             csrf_token_popup = get_csrf_token_for_popup_itemtest(session, args.base_url, csrf_token_item, args.host_id, interface_id)
             if csrf_token_popup and ip_address:
                  # Enviar el test y obtener las unidades
                 if args.dump_file:
                   get_file_content(session, args.base_url, csrf_token_popup, args.host_id, ip_address, interface_id, args.base_path, args.dump_file, args.store_file, plain_structure)
                 else:
                   list_folder_contents(session, args.base_url, csrf_token_popup, args.host_id, ip_address, interface_id, args.base_path,levels,args.regex,False)
                   if store_file:
                      answer = ""
                      print("\n")
                      while answer not in ("Y","N"):  # Keep asking until a valid input is provided
                          answer = input("\r\033[33mAre you sure you want to download all those files (Y/N): \33[0m").strip().upper()
                      if answer == "Y":
                          list_folder_contents(session, args.base_url, csrf_token_popup, args.host_id, ip_address, interface_id, args.base_path,levels,args.regex, True)
             else:
                 print("No se pudo obtener el CSRF token o la dirección IP del agente desde popup.itemtest.edit.")
    else:
        # Obtain host list
        list_hosts(session, args.base_url, args.only_up)

if __name__ == "__main__":
    main()
