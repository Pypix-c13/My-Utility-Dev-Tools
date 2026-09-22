import os, shutil
import subprocess, sys

def push():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  push <file>")
        print("  push --configuration <config>")
        return 1
    
    if shutil.which("git") is None:
        print("'Git' not found!\n")
        return 1

    if not os.path.isdir(".git"):
        subprocess.run(["git", "init"], check=True)

    if sys.argv[1] == "--configuration":
        config = sys.argv[2]

        with open(config, "r") as file:
            for line in file:
                file_path = line.strip()
                if not file_path or file_path.startswith("#"):
                    continue
                subprocess.run(["git", "add", file_path], check=True)
    else:
        subprocess.run(["git", "add", sys.argv[1]], check=True)

    subprocess.run(["git", "commit", "-m", "Update"], check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], check=True)

if __name__ == "__main__":
    push()