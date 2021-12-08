import os
import time
from abc import ABCMeta, abstractmethod
from collections import namedtuple
from pathlib import Path
from statistics import mean

from cryptography.hazmat.primitives.ciphers import algorithms, modes
from pandas import DataFrame
import pandas as pd

from cipher.block import BlockCipher


class Benchmark(metaclass=ABCMeta):
    benchmarks: list["bench_result"] = []

    bench_result = namedtuple("BenchResult", ["details", "result"])

    def __init__(self, path: Path, num_iter: int):
        self.num_iter = num_iter
        self.filename = path.name

    def timeit(self, details: dict, duration: float):
        self.benchmarks.append(self.bench_result(
            details=details,
            result=duration))

    def summarize(self) -> DataFrame:
        frames: list[DataFrame] = []
        for b in self.benchmarks:
            frames.append(DataFrame.from_dict({k: [v] for k, v in b.details.items()} |
                                              {"time": [b.result], "file": [self.filename]}))
        return pd.concat(frames)

    @abstractmethod
    def run(self) -> DataFrame:
        raise NotImplementedError("benchmark must implement run() method")


class BenchBlockCipher(Benchmark):
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
                modes.GCM(initialization_vector=os.urandom(16)),
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
                modes.CTR(nonce=os.urandom(16)),
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
            ],
        }
    ]

    def __init__(self, path: Path, data: bytes, num_iter: int = 10):
        super().__init__(path, num_iter)
        self.data = data + b" " * (self.BLOCK_SIZE_BYTES - len(data) % self.BLOCK_SIZE_BYTES)

    def run(self) -> DataFrame:
        for a in self._m:
            for mode in a["modes"]:
                enc_results, dec_results = [], []
                for i in range(self.num_iter):
                    bc = BlockCipher(a["algorithm"], mode, self.data)

                    start_enc = time.perf_counter()
                    bc.encrypt()
                    end_enc = time.perf_counter()

                    start_dec = time.perf_counter()
                    bc.decrypt()
                    end_dec = time.perf_counter()

                    enc_results.append(end_enc - start_enc)
                    dec_results.append(end_dec - start_dec)

                details = {
                    "algo": a["algorithm"].name,
                    "mode": mode.name,
                }
                self.timeit(details | {"op": "encryption"}, mean(enc_results))
                self.timeit(details | {"op": "decryption"}, mean(dec_results))

        return self.summarize()
