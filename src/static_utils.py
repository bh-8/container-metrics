import mimetypes
from typing import List
import magic
from pathlib import Path
import logging
import pymongo

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

class MIMETypeDetector:
    @staticmethod
    def by_filename(path: Path) -> str | None:
        return mimetypes.guess_type(path, False)[0]

    @staticmethod
    def by_content(path: Path) -> str | None:
        return magic.from_file(path, mime=True)

@staticmethod
def flatten_paths(path_list: List[Path], recursive: bool = False) -> List[Path]:
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
