import json
import os
from pathlib import PurePath
from project_utils import Installer

from pubmed.installer import PubMedInstaller
from lipidmaps.installer import LipidMapsInstaller
from kegg.installer import KeggInstaller
from hmdb.installer import HMDBInstaller

# Make sure the server name [key] matches the directory name
SERVERS2INSTALL = {
    "pubmed": PubMedInstaller(),
    "hmdb": HMDBInstaller(),
    "lipidmaps": LipidMapsInstaller(),
    "kegg": KeggInstaller(),
}


# Check if macOS
if os.name != 'posix' or not os.uname().sysname == 'Darwin':
    raise EnvironmentError("This script is intended to run on macOS only. Contact the developer if you see this message.")

config_path = PurePath(os.path.expanduser("~/Library/Application Support/Claude/claude_desktop_config.json"))
root_path = PurePath(__file__).parent

if not os.path.exists(config_path):
    print("Creating configuration file at:", config_path)
    os.makedirs(config_path.parent, exist_ok=True)

    # Create the config file with default values
    with open(config_path, "w") as f:
        json.dump({"mcpServers": {}}, f)


# Load existing config
with open(config_path, "r") as f:
    config = json.load(f)
if "mcpServers" not in config:
    config["mcpServers"] = {}

server_installed = []
server_errors = []
installer: Installer
for server_name, installer in SERVERS2INSTALL.items():
    if server_name not in config["mcpServers"]:
        server_cfg = {
            "command": "uv",
            "args": [
                "--directory",
                f"/Users/anthonylavertu/mac_docs/pycharmProjects/metabo-mcp/{server_name}",
                "run",
                "server.py",
                *[arg for arg in installer.args]
            ]
        }
        # Run the installer callback
        try:
            error = installer()
        except Exception as e:
            error = str(e)

        if error:
            print(f"Error installing {server_name}:\n{error}")
            server_errors.append(server_name)
            continue

        config["mcpServers"][server_name] = server_cfg
        server_installed.append(server_name)


# Now, write a summary of installed servers and those that failed to install
for server_name in server_installed:
    print(f"✅ {server_name} installed successfully.")

for server_name in server_errors:
    print(f"❌ {server_name} failed to install.")

# If the installer did something, we should ask the user if they want to save the configuration
if server_installed or server_errors:
    install_confirm = input("Do you want to save the configuration? (y/n): ").strip().lower()
    if install_confirm in ("y", "yes"):
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
        print("Configuration saved successfully 🎉")
    else:
        print("Configuration not saved. Exiting without changes.")