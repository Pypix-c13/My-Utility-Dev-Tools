import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
import tomllib

CONFIGURATION = Path(__file__).resolve().parent / "configuration.toml"


@dataclass
class HelperCommand:
    command: str
    description: str


HELP_COMMANDS = [
    HelperCommand("--set-home", "Setup host and server"),
    HelperCommand("--set-sender", "Setup sender"),
    HelperCommand("--home-exit", "Exit host server and kill sender"),
    HelperCommand("--sender-exit", "Exit sender without kill host server"),
    HelperCommand("--transfer-file <file>", "Transfer 1 file into host server"),
    HelperCommand(
        "--transfer-many-file <file_text>",
        "Transfer 2 or many file into host server",
    ),
    HelperCommand("--help", "show help message"),
    HelperCommand("--version", "show newest version"),
]


def setup():
    operating_system = platform.system()

    if operating_system == "Android" or hasattr(sys, "getandroidapilevel"):
        print("Setup server for Android...")
        subprocess.run(["pkg", "update", "-y"], check=True)
        subprocess.run(["pkg", "upgrade", "-y"], check=True)
        subprocess.run(["pkg", "install", "openssh"], check=True)
        subprocess.run(["termux-setup-storage"], check=True)
        subprocess.run(["passwd"], check=True)

        print("Server has been taken information...")
        print("Server start to listening...")
        subprocess.run(["sshd"], check=True)

        print("Server has been listening...")
        print("Server take information...")

        port_android = input("Port [8022]: ").strip() or "8022"
        remote_android = (
            input("Remote storage [~/storage/downloads]: ").strip()
            or "~/storage/downloads"
        )

        username_android = subprocess.run(
            ["whoami"], capture_output=True, text=True, check=True
        ).stdout.strip()

        ifconfig = subprocess.run(
            ["ifconfig", "wlan0"], capture_output=True, text=True, check=True
        ).stdout

        ip = ""
        for line in ifconfig.splitlines():
            line = line.strip()
            if line.startswith("inet "):
                ip = line.split()[1]
                break

        if not ip:
            print("Error: IPv4 address not found.")
            return 1

        print("\nInformation:")
        print(f"Username: {username_android}")
        print(f"IP: {ip}")
        print(f"Port: {port_android}")
        print(f"Remote storage: {remote_android}\n")
        print("Server has been setup!")

    elif operating_system == "Linux":
        print("Setup server for Linux...")
        subprocess.run(
            ["sudo", "apt", "install", "-y", "openssh-server"], check=True
        )
        subprocess.run(["sudo", "systemctl", "enable", "--now", "ssh"], check=True)

        print("Server has been listening...")

        username = subprocess.run(
            ["whoami"], capture_output=True, text=True, check=True
        ).stdout.strip()

        ipv4 = (
            subprocess.run(
                ["hostname", "-I"], capture_output=True, text=True, check=True
            )
            .stdout.strip()
            .split()[0]
        )

        port = input("Port [22]: ").strip() or "22"
        remote = input("Remote storage [~/Downloads]: ").strip() or "~/Downloads"

        print("\nInformation:")
        print(f"Username: {username}")
        print(f"IP: {ipv4}")
        print(f"Port: {port}")
        print(f"Remote storage: {remote}\n")
        print("Host server has been setup...")

    else:
        print(f"Unsupported operating system: {operating_system}")
        return 1

    return 0


def set_sender():
    print("Setup sender...")

    host = input("Host IP: ").strip()
    username = input("Username: ").strip()
    port = input("Port [22]: ").strip() or "22"
    remote = input("Remote storage [~/Downloads]: ").strip() or "~/Downloads"

    print("\nInformation:")
    print(f"Host: {host}")
    print(f"Username: {username}")
    print(f"Port: {port}")
    print(f"Remote storage: {remote}")

    print("\nTesting SSH connection...")
    result = subprocess.run(["ssh", "-p", port, f"{username}@{host}", "exit"])

    if result.returncode != 0:
        print("Failed to connect to host.")
        return 1

    with open(CONFIGURATION, "w") as file:
        file.write(
            f'username = "{username}"\n'
            f"port = {port}\n"
            f'ip = "{host}"\n'
            f'remote = "{remote}"\n'
        )

    print("Successfully connected to host.")
    print("Sender has been setup!")
    return 0


def transfer_file():
    if len(sys.argv) < 3:
        print("Usage: tf --transfer-file <file>")
        return 1

    if not CONFIGURATION.exists():
        print("Configuration file not found!")
        print("Run --set-sender first.")
        return 1

    with open(CONFIGURATION, "rb") as file:
        config = tomllib.load(file)

    username = config["username"]
    host = config["ip"]
    port = str(config["port"])
    remote = config["remote"]

    source = Path(sys.argv[2])

    if not source.exists():
        print(f"File '{source}' not found!")
        return 1

    if not source.is_file():
        print(f"'{source}' is not a file!")
        return 1

    target = f"{username}@{host}:{remote}"
    print(f"Sending {source}...")
    result = subprocess.run(["scp", "-P", port, str(source), target])

    if result.returncode != 0:
        print("Failed to transfer file.")
        return 1

    print("File transferred successfully!")
    return 0


def transfer_many_file():
    if len(sys.argv) < 3:
        print("Usage: tf --transfer-many-file <file_text>")
        return 1

    if not CONFIGURATION.exists():
        print("Configuration file not found!")
        print("Run --set-sender first.")
        return 1

    with open(CONFIGURATION, "rb") as file:
        config = tomllib.load(file)

    username = config["username"]
    host = config["ip"]
    port = str(config["port"])
    remote = config["remote"]

    list_file = Path(sys.argv[2])

    if not list_file.exists():
        print(f"File '{list_file}' not found!")
        return 1

    if not list_file.is_file():
        print(f"'{list_file}' is not a file!")
        return 1

    with open(list_file, "r") as file:
        sources = [
            Path(line.strip()) for line in file if line.strip()
        ]

    if not sources:
        print("No files found in list!")
        return 1

    for source in sources:
        if not source.exists():
            print(f"File '{source}' not found!")
            return 1

        if not source.is_file():
            print(f"'{source}' is not a file!")
            return 1

    target = f"{username}@{host}:{remote}"
    print(f"Sending {len(sources)} files...")

    command_args = ["scp", "-P", port, *[str(source) for source in sources], target]
    result = subprocess.run(command_args)

    if result.returncode != 0:
        print("Failed to transfer files.")
        return 1

    print("Files transferred successfully!")
    return 0


def home_exit():
    if hasattr(sys, "getandroidapilevel"):
        result = subprocess.run(["pkill", "sshd"])
    elif platform.system() == "Linux":
        result = subprocess.run(["sudo", "systemctl", "stop", "ssh", "ssh.socket"])
    else:
        print("Unsupported operating system.")
        return 1

    if result.returncode != 0:
        print("Failed to stop host server.")
        return 1

    print("Host server has been stopped.")
    return 0


def sender_exit():
    if not CONFIGURATION.exists():
        print("Configuration file not found.")
        return 1

    CONFIGURATION.unlink()
    print("Sender has been exited.")
    return 0


def help_message():
    print("Options:")
    for cmd in HELP_COMMANDS:
        print(f"    {cmd.command} - {cmd.description}")
    return 0


def version():
    print("OnTF v1.0")
    return 0


def command():
    if len(sys.argv) < 2:
        print("usage: tf [options] ..")
        print("try --help for more information!")
        return 1

    cmd = sys.argv[1]

    match cmd:
        case "--help":
            return help_message()
        case "--version":
            return version()
        case "--set-home":
            return setup()
        case "--set-sender":
            return set_sender()
        case "--home-exit":
            return home_exit()
        case "--sender-exit":
            return sender_exit()
        case "--transfer-file":
            return transfer_file()
        case "--transfer-many-file":
            return transfer_many_file()
        case _:
            print(f"Unknown option: {cmd}")
            print("try --help for more information!")
            return 1

if __name__ == "__main__":
    sys.exit(command())