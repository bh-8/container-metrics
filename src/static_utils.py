import logging
from pathlib import Path
import pymongo
import logging
import magic
import mimetypes

static_logger: logging.Logger = None
class StaticLogger: # singleton
    @staticmethod
    def set_logger(logname: str, loglevel: str) -> None:
        global static_logger
        if static_logger is None:
            logging.basicConfig()
            logging_level = getattr(logging, loglevel, None)
            logging.root.setLevel(logging_level)
            logging.basicConfig(level=logging_level)
            static_logger = logging.getLogger(logname)
            static_logger.debug("logger initialized")

    @staticmethod
    def get_logger() -> logging.Logger:
        global static_logger
        if static_logger is None:
            raise TypeError("singleton instance uninitialized")
        return static_logger

class MIMEDetector:
    @staticmethod
    def from_path_by_filename(path: Path) -> str | None:
        mt = mimetypes.guess_type(path, False)[0]
        if mt is None:
            StaticLogger.get_logger().warning(f"could not determine mime-type by filename of file '{path}'")
        return mt

    @staticmethod
    def from_path_by_magic(path: Path) -> str | None:
        mt = magic.from_file(path, mime=True)
        if mt is None:
            StaticLogger.get_logger().warning(f"could not determine mime-type by libmagic of file '{path}'")
        return mt

    @staticmethod
    def from_bytes_by_magic(data: bytes) -> str | None:
        mt = magic.from_buffer(data, mime=True)
        if mt is None:
            StaticLogger.get_logger().warning(f"could not determine mime-type by libmagic of binary data")
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
    logger = StaticLogger.get_logger()
    flattened_list = []
    for p in path_list:
        if not p.exists():
            logger.critical(f"could not find path '{p}'")
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
                logger.critical(f"could not find files in directory '{p}'")

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
