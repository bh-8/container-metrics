"""
static_utils.py

general utility functions
"""

# IMPORTS

import logging
import magic
import mimetypes
from pathlib import Path
import pymongo
from pymongo.errors import DocumentTooLarge
log = logging.getLogger(__name__)

# UTILS

class MIMEDetector:
    @staticmethod
    def from_path_by_filename(path: Path) -> str | None:
        mt = mimetypes.guess_type(path, False)[0]
        if mt is None:
            log.warning(f"could not determine mime-type by filename of file '{path}'")
        return mt

    @staticmethod
    def from_path_by_magic(path: Path) -> str | None:
        mt = magic.from_file(path, mime=True)
        if mt is None:
            log.warning(f"could not determine mime-type by libmagic of file '{path}'")
        return mt

    @staticmethod
    def from_bytes_by_magic(data: bytes) -> str | None:
        mt = magic.from_buffer(data, mime=True)
        if mt is None:
            log.warning(f"could not determine mime-type by libmagic of binary data")
        return mt

static_mongo: pymongo.MongoClient = None
class MongoInterface: # singleton
    @staticmethod
    def set_connection(mongo_connection_string: str) -> None:
        global static_mongo
        if static_mongo is None:
            static_mongo = pymongo.MongoClient(mongo_connection_string)

    @staticmethod
    def get_connection() -> pymongo.MongoClient:
        global static_mongo
        if static_mongo is None:
            raise TypeError("singleton instance uninitialized")
        return static_mongo

@staticmethod
def flatten_paths(path_list: list[Path], recursive: bool = False) -> list[Path]:
    flattened_list = []
    for p in path_list:
        if not p.exists():
            log.critical(f"could not find path '{p}'")
            continue

        if p.is_file():
            flattened_list.append(p)

        elif p.is_dir():
            t1 = len(flattened_list)

            if recursive:
                flattened_list.extend([
                    q for q in p.rglob("*") if q.is_file()
                ])
            else:
                flattened_list.extend([
                    q for q in p.glob("*") if q.is_file()
                ])

            t2 = len(flattened_list)
            if t2 - t1 == 0:
                log.critical(f"could not find files in directory '{p}'")

    if len(flattened_list) == 0:
        raise FileNotFoundError(f"could not find any file at given position(s)")

    return list(dict.fromkeys(flattened_list))

@staticmethod
def to_camel_case(string_with_underscores: str) -> str:
    return "".join([s.capitalize() for s in string_with_underscores.split("_")])

@staticmethod
def try_utf8_conv(raw: bytes) -> str | bytes:
    try:
        return str(raw, "utf-8")
    except:
        return raw

@staticmethod
def try_utf16_conv(raw: bytes) -> str | bytes:
    try:
        return str(raw, "utf-16")
    except:
        return raw

@staticmethod
def convert_unicode_str(byteString: bytes) -> str: #convert unicode string
    return byteString.split(b"\xff\xfe")[-1].replace(b"\x00", b"").decode(errors = "ignore")
