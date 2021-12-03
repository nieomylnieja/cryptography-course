import json
import logging
import os
import time
from abc import abstractmethod, ABCMeta
from pathlib import Path
from pydoc import locate
from argparse import ArgumentParser

import pandas as pd
from pandas import DataFrame

from cipher.cipher import BBSCipher, CBCMode, CTRMode
from generators.bbs import BBS
from tests.bench import BenchBlockCypher
from tests.test import bbs_run_tests
from utils.blum import generate_blum_integer


def get_subcommands() -> dict[str:"Subcommand"]:
    return {
        "test": SubcommandTest(),
        "generate-blum-int": SubcommandGenerateBlumInt(),
        "bbs": SubcommandBBS(),
        "bench": SubcommandBench(),
        "modes": SubcommandModes(),
    }


class Parser:

    def __init__(self, sub_c: dict[str:"Subcommand"]):
        self.parser = ArgumentParser(description="Script for cryptography course")
        subparsers = self.parser.add_subparsers(help="sub-command help")

        with open("args.json", "r") as f:
            args = json.load(f)

        for sub_c_name, s in args.items():
            sub_parser = subparsers.add_parser(
                sub_c_name,
                **{k: v for (k, v) in s.items() if k != "flags"})

            flags = s.get("flags")
            if not flags:
                continue
            for flag in flags:
                kwargs: dict = {k: locate(v) if k == "type" else v
                                for (k, v) in flag["kwargs"].items()}
                sub_parser.add_argument(*flag["args"], **kwargs)

            sub_parser.set_defaults(func=sub_c[sub_c_name].run)

    def parse(self):
        return self.parser.parse_known_args()


class Subcommand(metaclass=ABCMeta):
    @abstractmethod
    def run(self, args, unknown_args):
        raise NotImplementedError("run command must be implemented by all subcommands")


class SubcommandTest(Subcommand):
    def run(self, args, unknown_args):
        if args.bbs:
            path = Path(args.file_path)
            with open(path, "r") as f:
                bits = f.read()
            bbs_run_tests(bits)


class SubcommandBench(Subcommand):
    test_files_path = "resources/test_files"

    def run(self, args, unknown_args):
        results: list[DataFrame] = []
        for path, data in self._read_files(args).items():
            results.append(BenchBlockCypher(path, data).run())

        df = pd.concat(results, ignore_index=True)
        if args.output == "excel":
            df.to_excel('results.xlsx', sheet_name='results', index=False)
        elif args.output == "json":
            print(df.to_json(orient="records"))
        elif args.output == "csv":
            print(df.to_csv(index=False))
        else:
            print(df)

    def _read_files(self, args) -> dict[Path:bytes]:
        files: dict[Path:bytes] = {}
        if args.file_paths:
            for path in args.file_paths.split(","):
                file = Path(path)
                if not file.is_file():
                    raise ValueError(f"{file} is not a file")
                files[file] = file.read_bytes()
        else:
            dir_str = self.test_files_path
            if args.dir_path:
                dir_str = args.dir_path
            directory = Path(dir_str)
            if not directory.is_dir():
                raise ValueError(f"{directory} is not a directory")
            for file in filter(lambda f: f.is_file(), directory.iterdir()):
                files[file] = file.read_bytes()

        return files


class SubcommandGenerateBlumInt(Subcommand):
    def run(self, args, unknown_args):
        with open("numbers/blum.integer", "w") as f:
            f.write(str(generate_blum_integer()))


class SubcommandBBS(Subcommand):
    def run(self, args, unknown_args):
        if args.generate:
            seq = BBS.new(args.seq_len)
            with open(f"sequence/{time.time_ns()}.{args.seq_len}.bbs", "w") as f:
                f.write(seq)
        if args.cypher:
            if len(unknown_args) == 0:
                raise AttributeError("provide a message or a path to a file containing message")
            msg = " ".join(unknown_args)
            if os.path.exists(unknown_args[0]):
                with open(unknown_args[0], "r") as f:
                    msg = f.read()
            cypher = BBSCipher(args.file_path)

            encrypted = cypher.encrypt(msg)
            logging.info(f"Encrypted message: {encrypted}")

            decrypted = cypher.decrypt(encrypted)
            logging.info(f"Decrypted message: {decrypted.decode('utf-8')}")


class SubcommandModes(Subcommand):

    def run(self, args, unknown_args):
        with open(args.file_path, "r") as f:
            data = f.read().encode(encoding="utf-8")

        mode = None
        if args.cbc:
            mode = CBCMode()
        if args.ctr:
            mode = CTRMode()
        if mode is None:
            raise ValueError("unknown mode provided")

        mode.run(data, args.boo_boo)
