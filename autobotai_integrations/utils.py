import json


def list_of_unique_elements(list_to_verify: list) -> list:
    my_set = set()
    unique_list = list()

    for item in list_to_verify:
        my_set.add(json.dumps(item, sort_keys=True))

    for string_json in my_set:
        unique_list.append(json.loads(string_json))

    return unique_list
