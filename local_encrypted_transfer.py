# Copyright (c) Local Encrypted Transfer by Loxy0devlp
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.

from flask import Flask, request, render_template_string, send_from_directory, send_file
import os, socket, colorama, sys, ctypes, json

credits = {
    "tool_name"    : "Local Encrypted Transfer",
    "tool_version" : "1.0",
    "tool_license" : "MIT License",
    "tool_github"  : "github.com/loxy0devlp/Local-Encrypted-Transfer",
    "developer"    : "loxy0devlp",
    "gunslol"      : "guns.lol/loxy0dev"
}

colorama.init()
color  = colorama.Fore
white  = color.WHITE
reset  = color.RESET
green  = color.GREEN
blue   = color.BLUE
red    = color.RED

ERROR = f"{red}[{white}x{red}]"
INPUT = f"{blue}[{white}>{blue}]"
INFO  = f"{blue}[{white}!{blue}]"
ADD   = f"{blue}[{white}+{blue}]"

try:     os_name = "Windows" if sys.platform.startswith("win") else "Linux" if sys.platform.startswith("linux") else "Unknown"
except:  os_name = "Unknown"

banner = rf"""
             .____                        .__    ___________                              _____             
             |    |    ____   ____ _____  |  |   \__    ___/___________    ____   _______/ ____\___________ 
             |    |   /  _ \_/ ___\\__  \ |  |     |    |  \_  __ \__  \  /    \ /  ___/\   __\/ __ \_  __ \
             |    |__(  <_> )  \___ / __ \|  |__   |    |   |  | \// __ \|   |  \\___ \  |  | \  ___/|  | \/
             |________\____/ \_____>______/____/   |____|   |__|  (______/___|__/______> |__|  \_____>__|   
             
                                     {white + credits["tool_github"]}
"""

path_tool             = os.path.dirname(os.path.abspath(__file__))
path_folder_storage   = os.path.join(path_tool, "Storage")
path_folder_structure = os.path.join(path_tool, "Structure")
path_folder_config    = os.path.join(path_tool, "Config")
path_file_config      = os.path.join(path_folder_config, "Config.json")  
path_file_logs        = os.path.join(path_folder_config, "Logs.json")  
path_file_css         = os.path.join(path_folder_structure, "Css.css")
path_file_javascript  = os.path.join(path_folder_structure, "Javascript.js")
path_file_html        = os.path.join(path_folder_structure, "Html.html")

with open(path_file_config,     "r", encoding="utf-8") as file: data_config        = json.load(file)
with open(path_file_css,        "r", encoding="utf-8") as file: content_css        = file.read()
with open(path_file_javascript, "r", encoding="utf-8") as file: content_javascript = file.read()
with open(path_file_html,       "r", encoding="utf-8") as file: content_html       = file.read().replace("/*%CSS%*/", content_css).replace("/*%JAVASCRIPT%*/", content_javascript).replace("/*%TITLE1%*/", f"{credits["tool_name"]} v{credits["tool_version"]} (by {credits["developer"]})").replace("/*%TITLE2%*/", credits["tool_name"]).replace(r"/*%GITHUB%*/", credits["tool_github"]).replace(r"/*%DEVELOPER%*/", credits["developer"])

HOST = data_config["host"]
PORT = data_config["port"]

def Title():
    if os_name == "Windows": ctypes.windll.kernel32.SetConsoleTitleW(f"{credits["tool_name"]} v{credits["tool_version"]} (by {credits["developer"]})")
    elif os_name == "Linux": sys.stdout.write(f"\x1b]2;{credits["tool_name"]} v{credits["tool_version"]} (by {credits["developer"]})\x07")

def CreateFolderAndFile():
    os.makedirs(path_folder_storage, exist_ok=True)
    if not os.path.exists(path_file_logs):
        with open(path_file_logs, "w", encoding="utf-8") as file: json.dump({}, file)

def GetLocalIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except: ip = "127.0.0.1"
    finally: s.close()
    return ip

def LoadFilesJson():
    if os.path.exists(path_file_logs):
        try:
            with open(path_file_logs, "r", encoding="utf-8") as file:
                data = json.load(file)
                if isinstance(data, dict): return data
        except json.JSONDecodeError: pass
    return {}

def SaveFilesJson(data):
    with open(path_file_logs, "w", encoding="utf-8") as file: json.dump(data, file, indent=2)

def Start():
    Title()
    CreateFolderAndFile()
    app = Flask(__name__)

    @app.route("/", methods=["GET", "POST"])
    def Index():
        os.makedirs(path_folder_storage, exist_ok=True)
        files_data = LoadFilesJson()
        if request.method == "POST":
            uploaded_file = request.files.get("file")
            if uploaded_file and uploaded_file.filename:
                path = os.path.join(path_folder_storage, uploaded_file.filename)
                uploaded_file.save(path)
                print(f"{ADD} File received (encrypted): {white}{uploaded_file.filename}{reset}")
                if uploaded_file.filename not in files_data:
                    next_number = max(files_data.values(), default=0) + 1
                    files_data[uploaded_file.filename] = next_number
                    SaveFilesJson(files_data)
            else:
                print(f"{ERROR} No file received in POST.{reset}")
        sorted_files = sorted(files_data.items(), key=lambda x: x[1])
        return render_template_string(content_html, files=sorted_files)

    @app.route("/download/<filename>")
    def Download(filename):
        path = os.path.join(path_folder_storage, filename)
        if not os.path.exists(path): return f"{ERROR} File not found", 404
        return send_file(path, as_attachment=True)

    @app.route("/delete/<filename>", methods=["POST"])
    def DeleteFile(filename):
        path = os.path.join(path_folder_storage, filename)
        if os.path.exists(path):
            try:
                size = os.path.getsize(path)
                with open(path, "r+b") as file: file.write(b"\x00" * size)
                os.remove(path)
                files_data = LoadFilesJson()
                if filename in files_data:
                    del files_data[filename]
                    SaveFilesJson(files_data)
                print(f"{ADD} File downloaded and successfully deleted: {white}{filename}{reset}")
                return "OK", 200
            except Exception as e: 
                print(f"{ERROR} Failed to delete {filename}: {white}{e}{reset}")
                return "Error", 500
        return "File not found", 404

    @app.route("/favicon.ico")
    def Favicon():
        return send_from_directory(path_folder_structure, "Icone.ico", mimetype="image/vnd.microsoft.icon")

    IP = GetLocalIp()

    print(f"""{blue + banner + reset}
{blue}Access:{reset}
 * Local   : https://localhost:{PORT}
 * Network : https://{IP}:{PORT}
{blue}Logs:{reset}""")

    app.run(host=HOST, port=PORT, ssl_context="adhoc")

try: Start()
except Exception as e: 
    print(f"{ERROR} Error: {white}{e}")
    input(f"{INPUT} Press enter -> {reset}")