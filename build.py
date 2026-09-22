from pathlib import Path
import json
import subprocess
import sys

def main():
    config_path = Path("build.json")
    if not config_path.exists():
        print("'build.json' not found!")
        return 1 

    with open(config_path, "r", encoding="utf-8") as file:
        config = json.load(file)
    
    compiler = config.get("compiler", "")
    sources = config.get("source", [])
    target = config.get("target", "")
    command = config.get("command", [])

    if isinstance(sources, str):
        sources = [sources]
    if isinstance(command, str):
        command = [command]

    cmd = []

    if compiler in ("gcc", "clang", "g++", "c++"):
        cmd = [compiler] + sources
        if target:
            cmd += ["-o", target]
        cmd += command
    elif compiler in ("python", "python3"):
        cmd = [compiler] + command + sources
    elif compiler in ("bash", "sh"):
        cmd = [compiler] + sources
    else:
        print(f"Unknown compiler or runner '{compiler}'!")
        return 1
    
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd)
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())