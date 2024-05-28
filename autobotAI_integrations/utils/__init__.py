import asyncio
from datetime import datetime
import importlib.machinery
import importlib.util
import traceback
import uuid
from pathlib import Path
import json


def fromisoformat(strdate):
    try:
        return datetime.strptime(strdate, "%Y-%m-%dT%H:%M:%S.%f")
    except:
        return datetime.strptime(strdate, "%Y-%m-%dT%H:%M:%S")


def load_mod_from_string(code_string):
    try:
        Path("/tmp/mods/").mkdir(parents=True, exist_ok=True)
        file_path = '/tmp/mods/' + str(uuid.uuid4()) + '.py'
        f = open(file_path, "w")
        f.write(code_string)
        f.close()
        loader = importlib.machinery.SourceFileLoader('fetcher', file_path)
        spec = importlib.util.spec_from_loader(loader.name, loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        return mod
    except:
        traceback.print_exc()
        raise Exception("Unable to load function.")

def run_mod_func(fn, **kwargs):
    if not asyncio.iscoroutinefunction(fn):
        return fn(**kwargs)
    else:
        return asyncio.run(fn(**kwargs))

def list_of_unique_elements(list_to_verify: list) -> list:
    my_set = set()
    unique_list = list()

    for item in list_to_verify:
        my_set.add(json.dumps(item, sort_keys=True))

    for string_json in my_set:
        unique_list.append(json.loads(string_json))

    return unique_list
