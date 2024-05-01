import logging
import magic
import mimetypes
from pathlib import Path
import pymongo
from typing import Callable, List

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

class MIMEDetector:
    @staticmethod
    def from_path_by_filename(path: Path) -> str | None:
        mt = mimetypes.guess_type(path, False)[0]
        if mt is None:
            StaticLogger.get_logger().critical(f"could not determine mime-type by filename of file '{path}'")
        return mt

    @staticmethod
    def from_path_by_magic(path: Path) -> str | None:
        mt = magic.from_file(path, mime=True)
        if mt is None:
            StaticLogger.get_logger().critical(f"could not determine mime-type by libmagic of file '{path}'")
        return mt

    @staticmethod
    def from_bytes_by_magic(data: bytes) -> str | None:
        mt = magic.from_buffer(data, mime=True)
        if mt is None:
            StaticLogger.get_logger().critical(f"could not determine mime-type by libmagic of file '{path}'")
        return mt

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

@staticmethod
def filter_paths(path_list: List[Path], supported_mime_types: List[str], mime_type_filter: Callable[[str], str | None]) -> List[Path]:
    filtered_path_list = [
        f for f in path_list
            if (mime_type_filter(f) is not None)
                and (mime_type_filter(f) in supported_mime_types)
    ]

    if len(filtered_path_list) == 0:
        raise FileNotFoundError(f"none of the given files is supported")

    return filtered_path_list

@staticmethod
def to_camel_case(string_with_underscores: str) -> str:
    return "".join([s.capitalize() for s in string_with_underscores.split("_")])

class ContainerItem():
    def __init__(self, position: int, length: int) -> None:
        self.internal_dict: dict = {
            "pos": position,
            "len": length
        }
    def set_attribute(self, key: str, data) -> None:
        if data is None and key in self.internal_dict:
            del self.internal_dict[key]
        else:
            self.internal_dict[key] = data
    def get_dict(self) -> dict:
        return self.internal_dict

class Coverage():
    def __init__(self, coverage_list: list[dict], total_length: int) -> None:
        self.coverage_list: list[dict] = coverage_list
        self.total_length: int = total_length
    def uncovered_positions(self) -> list[dict]:
        covered_to: int = 0
        uncovered: list[dict] = []
        for i in self.coverage_list:
            position: int = i["pos"]
            length: int = i["len"]
            if covered_to == position:
                covered_to = covered_to + length
            else:
                uncovered.append({
                    "pos": covered_to,
                    "len": position - covered_to
                })
                covered_to = position + length
        if covered_to < self.total_length:
            uncovered.append({
                "pos": covered_to,
                "len": self.total_length - covered_to
            })
        return [i for i in uncovered if i["pos"] + i["len"] <= self.total_length]
