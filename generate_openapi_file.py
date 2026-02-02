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

_CLEANUP = False
_DEBUG = False


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


def save_openapi(content):
    # Saving new openapi.yaml file
    os.makedirs(DST_DIR, exist_ok=True)
    write_yml_file(
        {
            "openapi": content["openapi"],
            "info": content["info"],
            "paths": content["paths"],
            "servers": content["servers"],
            "tags": content["tags"],
            "components": content["components"],
        },
        f"{DST_DIR}/{GEN_FILE}",
    )
    print(f"Generated `{DST_DIR}/{GEN_FILE}`")


def concat_files():
    # Loading types from SRC_DIR, that was converted from AnixartJS ts types via typeconv
    load_types()
    # Loading base file with description and paths
    content = load_yml_file(BASE_FILE)
    # Adding schemas to base file
    for x in TYPES:
        content["components"]["schemas"][x] = TYPES[x]
    return content


def find_all_references(string, content):
    return sum(string in line for line in content)


def find_unused(content):
    content_string = dump(content, None, Dumper=Dumper, sort_keys=False)
    content_array = content_string.split("\n")

    _foundRefs = {}

    for request in content["components"]["requests"]:
        # /components/requests/{request}
        _foundRefs[f"#/components/requests/{request}"] = find_all_references(
            f"#/components/requests/{request}", content_array
        )
    for response in content["components"]["responses"]:
        # /components/responses/{response}
        _foundRefs[f"#/components/responses/{response}"] = find_all_references(
            f"#/components/responses/{response}", content_array
        )
    for schema in content["components"]["schemas"]:
        # /components/schemas/{schema}
        _foundRefs[f"#/components/schemas/{schema}"] = find_all_references(
            f"#/components/schemas/{schema}", content_array
        )
    for parameter in content["components"]["parameters"]:
        # /components/parameters/{parameter}
        _foundRefs[f"#/components/parameters/{parameter}"] = find_all_references(
            f"#/components/parameters/{parameter}", content_array
        )

    _unusedRefs = {}
    for x in _foundRefs:
        if _foundRefs[x] == 0:
            _unusedRefs[x] = _foundRefs[x]
    return _unusedRefs


def print_unused_warn(unused):
    for x in unused:
        print(f"WARN:UNUSED:{x}")


def cleanup_unused(content, unused):
    for ref in unused:
        _array = ref.split("/")
        _hash = _array[0]
        _components = _array[1]
        path = _array[2]
        name = _array[3]
        content["components"][path].pop(name)
    return content


def main():
    content = concat_files()
    if _CLEANUP:
        unused = find_unused(content)
        if _DEBUG:
            print_unused_warn(unused)
        content = cleanup_unused(content, unused)
        print("Removed unused references")
    save_openapi(content)


if __name__ == "__main__":
    if ("-d" or "--debug") in sys.argv:
        _DEBUG = True
        print("DEBUG MODE ON")
    if ("-c" or "--cleanup") in sys.argv:
        _CLEANUP = True
    main()
    if ("-w" or "--watch") in sys.argv:
        from watchfiles import watch
        try:
            print(f"Watching for changes in file `{BASE_FILE}`")
            for _ in watch(BASE_FILE):
                main()
        except KeyboardInterrupt:
            print(f"Stopped watching for changes in file `{BASE_FILE}`")
