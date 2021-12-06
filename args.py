import json
import os
import time
from abc import abstractmethod, ABCMeta
from pathlib import Path
from pydoc import locate
from argparse import ArgumentParser

import pandas as pd
from bitarray import bitarray
from pandas import DataFrame

from cipher.asynchronous import RSASimple
from cipher.block import BBSCipher, CBCMode, CTRMode
from generators.bbs import BBS
from tests.bench import BenchBlockCipher
from tests.test import bbs_run_tests
from utils.blum import generate_blum_integer


def get_subcommands() -> dict[str:"Subcommand"]:
    return {
        "test": SubcommandTest(),
        "generate-blum-int": SubcommandGenerateBlumInt(),
        "bbs": SubcommandBBS(),
        "bench": SubcommandBench(),
        "modes": SubcommandModes(),
        "rsa": SubcommandRSA(),
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
            with open(args.file_path, "r") as f:
                bbs = f.read()
            bbs_run_tests(bbs)
        if args.bbs_cipher:
            if len(unknown_args) == 0:
                raise AttributeError("provide a message or a path to a file containing message")
            msg = " ".join(unknown_args)
            if os.path.exists(unknown_args[0]):
                with open(unknown_args[0], "r") as f:
                    msg = f.read()
            cipher = BBSCipher(args.file_path)
            cipher.run(msg)

            bits = bitarray()
            bits.frombytes(cipher.encrypted)

            bbs_run_tests(bits.to01())


class SubcommandBench(Subcommand):
    test_files_path = "resources/test_files"

    def run(self, args, unknown_args):
        results: list[DataFrame] = []
        for path, data in self._read_files(args).items():
            results.append(BenchBlockCipher(path, data).run())

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
            f.write(str(generate_blum_integer(p_len=args.p_len, q_len=args.q_len)))


class SubcommandBBS(Subcommand):
    def run(self, args, unknown_args):
        if args.generate:
            seq = BBS.new(args.seq_len)
            if seq:
                seq_path = Path('./sequence')
                if not seq_path.exists():
                    seq_path.mkdir(parents=True, exist_ok=True)
                with open(seq_path.joinpath(f"{time.time_ns()}.{args.seq_len}.bbs"), "w") as f:
                    f.write(seq)
        if args.cipher:
            if len(unknown_args) == 0:
                raise AttributeError("provide a message or a path to a file containing message")
            msg = " ".join(unknown_args)
            if os.path.exists(unknown_args[0]):
                with open(unknown_args[0], "r") as f:
                    msg = f.read()
            BBSCipher(args.file_path).run(msg)


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


class SubcommandRSA(Subcommand):

    def run(self, args, unknown_args):
        with open(args.file_path, "r") as f:
            data = f.read().encode(encoding="utf-8")
        if args.simple:
            simple_rsa = RSASimple()

            if args.preset_file:
                with open(args.preset_file, "r") as f:
                    simple_rsa.with_preset(f.read())

            if args.encrypt:
                simple_rsa.run_encryption(data)
            if args.sign:
                simple_rsa.run_signing(data)
