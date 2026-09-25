import os, sys, json
import zipfile, uuid, subprocess

COMMANDS = {
    "init": "create an empty template project",
    "pack": "add behavior pack or resource pack inside the project",
    "package": "compress project into .mcpack or .mcaddon",
}

SECTIONS = {
    "data", "script",
    "resources", "world",
}


def lookup():
    print("Options:")
    for command, description in COMMANDS.items():
        print(f"    {command:<10} {description}")
uuidgen = lambda: str(uuid.uuid4())

def create_manifest(name, section):
    if section == "data":
        return {
            "format_version": 2,
            "header": {
                "name": name,
                "description": f"{name} Behavior Pack",
                "uuid": f"{uuidgen()}",
                "version": [1, 0, 0],
                "min_engine_version": [26, 40, 0],
            },
            "modules": [
                {
                    "type": "data",
                    "uuid": f"{uuidgen()}",
                    "version": [1, 0, 0],
                }
            ],
        }

    if section == "script":
        return {
            "format_version": 2,
            "header": {
                "name": name,
                "description": f"{name} Script Pack",
                "uuid": f"{uuidgen()}",
                "version": [1, 0, 0],
                "min_engine_version": [26, 40, 0],
            },
            "modules": [
                {
                    "type": "script",
                    "language": "javascript",
                    "uuid": f"{uuidgen()}",
                    "version": [1, 0, 0],
                    "entry": "scripts/main.js",
                }
            ],
        }

    if section == "resources":
        return {
            "format_version": 2,
            "header": {
                "name": name,
                "description": f"{name} Resource Pack",
                "uuid": f"{uuidgen()}",
                "version": [1, 0, 0],
                "min_engine_version": [26, 40, 0],
            },
            "modules": [
                {
                    "type": "resources",
                    "uuid": f"{uuidgen()}",
                    "version": [1, 0, 0],
                }
            ],
        }

    if section == "world":
        return {
            "format_version": 2,
            "header": {
                "name": name,
                "description": f"{name} World",
                "uuid": f"{uuidgen()}",
                "version": [1, 0, 0],
            },
        }

    return None


def init_project(name, location, section):
    if section not in SECTIONS:
        print(f"Unknown section: {section}")
        print("Available sections: data, script, resources, world")
        return 1

    project = os.path.join(location, name)
    os.makedirs(project, exist_ok=True)
    subprocess.run(["git", "init", project])

    manifest = create_manifest(name, section)
    with open(os.path.join(project, "manifest.json"), "w", encoding="utf-8",) as file:
        json.dump(manifest, file, indent=4)

    if section == "data":
        os.makedirs(os.path.join(project, "functions"), exist_ok=True)
        open(os.path.join(project, "functions", "main.mcfunction"), "w", encoding="utf-8").close()

    elif section == "script":
        os.makedirs(os.path.join(project, "scripts"), exist_ok=True)
        open(os.path.join(project, "scripts", "main.js"), "w", encoding="utf-8").close()

    elif section == "resources":
        os.makedirs(os.path.join(project, "textures"), exist_ok=True)

    elif section == "world":
        os.makedirs(os.path.join(project, "db"), exist_ok=True)
        os.makedirs(os.path.join(project, "behavior_packs"), exist_ok=True)
        os.makedirs(os.path.join(project, "resource_packs"), exist_ok=True)

    print(f"Created project: {project}")
    return 0


def package_project(section, location):
    if section not in ("mcpack", "mcaddon"):
        print(f"Unknown package type: {section}")
        print("Available packages: mcpack, mcaddon")
        return 1

    location = os.path.abspath(location)

    if not os.path.isdir(location):
        print(f"Directory does not exist: {location}")
        return 1

    name = os.path.basename(location)
    output = os.path.join(os.path.dirname(location), f"{name}.{section}")

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for root, directories, files in os.walk(location):
            for filename in files:
                filepath = os.path.join(root, filename)
                archive_name = os.path.relpath(filepath, location)
                archive.write(filepath, archive_name)

    print(f"Created package: {output}")
    return 0

def pack_project(section, location):
    if section not in ("behavior", "resources"):
        print(f"Unknown pack type: {section}")
        print("Available packs: behavior, resources")
        return 1

    project = os.path.abspath(location)

    if not os.path.isdir(project):
        print(f"Directory does not exist: {project}")
        return 1

    if section == "behavior":
        pack = os.path.join(project, "behavior_pack")
        name = "Behavior Pack"

        manifest = {
            "format_version": 2,
            "header": {
                "name": f"{os.path.basename(project)} {name}",
                "description": f"{os.path.basename(project)} Behavior Pack",
                "uuid": uuidgen(),
                "version": [1, 0, 0],
                "min_engine_version": [26, 40, 0],
            },
            "modules": [
                {
                    "type": "data",
                    "uuid": uuidgen(),
                    "version": [1, 0, 0],
                }
            ],
        }
        os.makedirs(os.path.join(pack, "functions"), exist_ok=True)

    elif section == "resources":
        pack = os.path.join(project, "resource_pack")
        name = "Resource Pack"

        manifest = {
            "format_version": 2,
            "header": {
                "name": f"{os.path.basename(project)} {name}",
                "description": f"{os.path.basename(project)} Resource Pack",
                "uuid": uuidgen(),
                "version": [1, 0, 0],
                "min_engine_version": [26, 40, 0],
            },
            "modules": [
                {
                    "type": "resources",
                    "uuid": uuidgen(),
                    "version": [1, 0, 0],
                }
            ],
        }

        os.makedirs(os.path.join(pack, "textures"), exist_ok=True)
    os.makedirs(pack, exist_ok=True)

    with open(os.path.join(pack, "manifest.json"), "w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=4)

    print(f"Created {section} pack: {pack}")
    return 0

def main():
    if len(sys.argv) < 2:
        lookup()
        return 0

    command = sys.argv[1]

    if command == "init":
        if len(sys.argv) < 5:
            print(
                "usage: vpack init "
                "<name> <location> "
                "<data|script|resources|world>"
            )
            return 1

        name = sys.argv[2]
        location = sys.argv[3]

        section = sys.argv[4]
        return init_project(name, location, section)

    if command == "package":
        if len(sys.argv) < 4:
            print(
                "usage: vpack package "
                "<mcpack|mcaddon> <location>"
            )
            return 1

        section = sys.argv[2]
        location = sys.argv[3]

        return package_project(section, location)

    if command == "pack":
        if len(sys.argv) < 4:
            print(
                "usage: vpack pack "
                "<behavior|resources> <location>"
            )
            return 1

        section = sys.argv[2]
        location = sys.argv[3]

        return pack_project(section, location)

    print(f"Unknown command: {command}")
    lookup()
    return 1


if __name__ == "__main__":
    sys.exit(main())
