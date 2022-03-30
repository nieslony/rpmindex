"""
Some usefull hepler functions
"""

import collections
import flask

def dict_merge(dct, merge_dct):
    """
    Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts
    nested to an arbitrary depth, updating keys. The ``merge_dct`` is
    merged into ``dct``.

    :param dct: dict onto which the merge is executed
    :param merge_dct: dct merged into dct
    :return: None
    """

    for key in merge_dct.keys():
        if (key in dct and isinstance(dct[key], dict)
            and
            isinstance(merge_dct[key], collections.abc.Mapping)):
            dict_merge(dct[key], merge_dct[key])
        else:
            dct[key] = merge_dct[key]

def is_prefix_of(path1, path2):
    """
    Test if path1 is a prefix of path2
    """
    app = flask.current_app
    while path1.startswith("/"):
        path1 = path1[1:]
    while path2.startswith("/"):
        path2 = path2[1:]
    while path1.endswith("/"):
        path1 = path2[:-1]
    while path2.endswith("/"):
        path2 = path2[:-1]
    path1_list = path1.split("/")
    path2_list = path2.split("/")

    if len(path1_list) > len(path2_list):
        return False

    app.logger.debug(f"Comparing {str(path1_list)} <-> {str(path2_list)}")
    for i in range(len(path1_list)):
        if path1_list[i] != path2_list[i]:
            return False
    return True
