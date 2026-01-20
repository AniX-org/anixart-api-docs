import os, sys
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

TYPES = {}
BASE_FILE = "./base.yaml"
GEN_FILE = "openapi.yaml"
SRC_DIR = "./AnixartJS-typeconv"
DST_DIR = "./public"


def load_yml_file(file_path):
    with open(file_path, "r") as f:
        return load(f, Loader=Loader)


def write_yml_file(data, file_path):
    with open(file_path, "w") as f:
        dump(data, f, Dumper=Dumper, sort_keys=False)


def load_types():
    for root, dirs, files in os.walk(SRC_DIR):
        for file in files:
            if file.endswith(".yaml"):
                file_path = os.path.join(root, file)
                data = load_yml_file(file_path)
                for x in data["components"]["schemas"]:
                    TYPES[x] = data["components"]["schemas"][x]


def main():
    # Loading types from SRC_DIR, that was converted from AnixartJS ts types via typeconv
    load_types()
    # Loading base file with description and paths
    base = load_yml_file(BASE_FILE)
    # Adding schemas to base file
    for x in TYPES:
        base["components"]["schemas"][x] = TYPES[x]
    # Saving new openapi.yaml file
    os.makedirs(DST_DIR, exist_ok=True)
    write_yml_file(
        {
            "openapi": base["openapi"],
            "info": base["info"],
            "paths": base["paths"],
            "servers": base["servers"],
            "tags": base["tags"],
            "components": base["components"],
        },
        f"{DST_DIR}/{GEN_FILE}",
    )
    print(f"Generated `{DST_DIR}/{GEN_FILE}`")


if __name__ == "__main__":
    main()
    if ("-w" or "--watch") in sys.argv:
        from watchfiles import watch
        try:
            print(f"Watching for changes in file `{BASE_FILE}`")
            for _ in watch(BASE_FILE):
                main()
        except KeyboardInterrupt:
            print(f"Stopped watching for changes in file `{BASE_FILE}`")
