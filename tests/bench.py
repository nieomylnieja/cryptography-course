import os
import timeit
from abc import ABCMeta, abstractmethod
from collections import namedtuple
from pathlib import Path
from typing import Callable

from cryptography.hazmat.primitives.ciphers import algorithms, modes
from pandas import DataFrame
import pandas as pd

from cipher.cipher import BlockCipher


class Benchmark(metaclass=ABCMeta):
    benchmarks: list["bench_result"] = []

    bench_result = namedtuple("BenchResult", ["details", "result"])

    def __init__(self, path: Path, num_iter: int = 100000):
        self.num_iter = num_iter
        self.filename = path.name

    def timeit(self, details: dict, f: Callable):
        duration = timeit.Timer(f).timeit(number=self.num_iter)
        self.benchmarks.append(self.bench_result(
            details=details,
            result=(duration / self.num_iter) * 1000))

    def summarize(self) -> DataFrame:
        frames: list[DataFrame] = []
        for b in self.benchmarks:
            frames.append(DataFrame.from_dict({k: [v] for k, v in b.details.items()} |
                                              {"time": [b.result], "file": [self.filename]}))
        return pd.concat(frames)

    @abstractmethod
    def run(self) -> DataFrame:
        raise NotImplementedError("benchmark must implement run() method")


class BenchBlockCypher(Benchmark):
    BLOCK_SIZE_BYTES = 16

    _m = [
        {
            "algorithm": algorithms.AES(os.urandom(32)),
            "modes": [
                modes.ECB(),
                modes.CBC(initialization_vector=os.urandom(16)),
                modes.CFB(initialization_vector=os.urandom(16)),
                modes.OFB(initialization_vector=os.urandom(16)),
                modes.CFB8(initialization_vector=os.urandom(16)),
                modes.CTR(nonce=os.urandom(16)),
                modes.GCM(initialization_vector=os.urandom(16), tag=os.urandom(16)),
                modes.XTS(tweak=os.urandom(16)),
            ],
        },
        {
            "algorithm": algorithms.Camellia(os.urandom(32)),
            "modes": [
                modes.ECB(),
                modes.CBC(initialization_vector=os.urandom(16)),
                modes.CFB(initialization_vector=os.urandom(16)),
                modes.OFB(initialization_vector=os.urandom(16)),
                modes.CFB8(initialization_vector=os.urandom(16)),
                modes.CTR(nonce=os.urandom(16)),
                modes.GCM(initialization_vector=os.urandom(16), tag=os.urandom(16)),
                modes.XTS(tweak=os.urandom(16)),
            ],
        },
        {
            "algorithm": algorithms.TripleDES(os.urandom(16)),
            "modes": [
                modes.ECB(),
                modes.CBC(initialization_vector=os.urandom(8)),
                modes.CFB(initialization_vector=os.urandom(8)),
                modes.OFB(initialization_vector=os.urandom(8)),
                modes.CFB8(initialization_vector=os.urandom(8)),
                modes.CTR(nonce=os.urandom(8)),
            ],
        }
    ]

    def __init__(self, path: Path, data: bytes, num_iter: int = 100000):
        super().__init__(path, num_iter)
        self.data = data + b" " * (self.BLOCK_SIZE_BYTES - len(data) % self.BLOCK_SIZE_BYTES)

    def run(self) -> DataFrame:
        for a in self._m:
            for mode in a["modes"]:
                bc = BlockCipher(a["algorithm"], mode, self.data)
                self.timeit(bc.details | {"op": "encryption"}, lambda: bc.encrypt)
                self.timeit(bc.details | {"op": "decryption"}, lambda: bc.decrypt)

        return self.summarize()
