from abc import ABCMeta, abstractmethod
import itertools
from typing import Callable

from tests.config import ConfigBBS


def bbs_run_tests(bits: str):
    if len(bits) > ConfigBBS.SERIES_LENGTH:
        print(f"Sequence is too long, expecting {ConfigBBS.SERIES_LENGTH} length.\n"
              f"Do you want to cut it or select a subset?")
        choice = input("Type: [c/s]: ")
        if choice.lower() == "c":
            bits = bits[:ConfigBBS.SERIES_LENGTH]
            print(f"Cutting the sequence to {ConfigBBS.SERIES_LENGTH} length.")
        elif choice.lower() == "s":
            lower_index = int(input("Provide lower subset index: "))
            upper_index = int(input("Provide upper subset index: "))
            bits = bits[lower_index:upper_index]
            print(f"Cutting the sequence to {lower_index}:{upper_index} subset.")
        else:
            raise ValueError("invalid argument provided, expected either 'c' or 's'")

    Tests.register(
        TestSeriesLength(bits),
        TestSingleBits(bits),
        TestSeries(bits),
        TestLongSeries(bits),
        TestPoker(bits))
    Tests.run()


class Tests:
    tests: list["TestInterface"] = []

    @staticmethod
    def register(*tests: "TestInterface"):
        [Tests.tests.append(test) for test in tests]

    @staticmethod
    def run():
        all_tests_passed = True
        for test in Tests.tests:
            test.run()
            if not test.passed:
                all_tests_passed = False
        if all_tests_passed:
            print("[SUCCESS] All tests have passed!")
        else:
            print("[FAILURE] Some of the tests have failed!")


class TestInterface(metaclass=ABCMeta):
    passed: bool = True
    name: str = "none"
    expected: any = "none"

    def __init__(self, bits: str):
        if self.name in ["none", ""]:
            raise NotImplementedError("'name' must be set to a description of the test to be run")
        if self.expected in ["none", ""]:
            raise NotImplementedError("'expected' must be set to a description of the expected result of the test")
        self.bits = bits

    def assert_true(self, predicate: Callable[[], bool], result: any):
        self._passing(result) if predicate() else self._failing(result)

    def _failing(self, result: any):
        self.passed = False
        self._print("FAIL", result)

    def _passing(self, result: any):
        self._print("PASS", result)

    def _print(self, outcome: str, result: any):
        print(f"[{outcome}] Test: {self.name}, Result: {result}, Expected: {self.expected}")

    @abstractmethod
    def run(self):
        raise NotImplementedError


class TestSeriesLength(TestInterface):
    name = "series length"
    expected = ConfigBBS.SERIES_LENGTH

    def run(self):
        length = len(self.bits)
        self.assert_true(
            predicate=lambda: length == ConfigBBS.SERIES_LENGTH,
            result=length)


class TestSeries(TestInterface):
    name = "series"
    expected = f"{ConfigBBS.SERIES_TEST_TABLE.items()}"

    def run(self):
        series_occurrences = {bit: {k: 0 for k in ConfigBBS.SERIES_TEST_TABLE.keys()} for bit in ["0", "1"]}
        previous_bit, series_ctr = "0", 0
        for bit in self.bits:
            series_ctr += 1
            if previous_bit != bit:
                series_key = str(series_ctr) if series_ctr < 6 else "6+"
                series_occurrences[previous_bit][series_key] += 1
                series_ctr = 0
            previous_bit = bit

        self.assert_true(
            predicate=lambda: self._compare_series(series_occurrences),
            result=series_occurrences)

    @staticmethod
    def _compare_series(series_occurrences: dict) -> bool:
        for bit, series in series_occurrences.items():
            for s, occurrences in series.items():
                v = ConfigBBS.SERIES_TEST_TABLE[s]
                if not v[0] < occurrences < v[1]:
                    return False
        return True


class TestSingleBits(TestInterface):
    name = "single bits"
    expected = f"{ConfigBBS.SINGLE_BITS_LOWER_BOUND} < n < {ConfigBBS.SINGLE_BITS_UPPER_BOUND}"

    def run(self):
        ones_num = len(list(filter(lambda x: x == "1", self.bits)))
        self.assert_true(
            predicate=lambda: ConfigBBS.SINGLE_BITS_LOWER_BOUND < ones_num < ConfigBBS.SINGLE_BITS_UPPER_BOUND,
            result=f"n = {ones_num}")


class TestLongSeries(TestInterface):
    name = "long series"
    expected = "s < 26"

    def run(self):
        current_bit = ""
        ctr, longest_sequence = 0, 0
        for bit in self.bits:
            if bit != current_bit:
                if ctr > longest_sequence:
                    longest_sequence = ctr
                ctr = 0
                current_bit = bit
            ctr += 1
        # IF we ended with the longest sequence
        if ctr > longest_sequence:
            longest_sequence = ctr

        self.assert_true(
            predicate=lambda: longest_sequence < ConfigBBS.LONG_SERIES_LENGTH,
            result=f"s = {longest_sequence}")


class TestPoker(TestInterface):
    name = "poker"
    expected = f"{ConfigBBS.POKER_X_LOWER_BOUND} < x < {ConfigBBS.POKER_X_UPPER_BOUND}"

    def run(self):
        four_bit_occurrences = {"".join(seq): 0 for seq in itertools.product("01", repeat=4)}
        four_bit_sequences = map(lambda x: "".join(x), zip(*(self.bits[i::4] for i in range(4))))
        for seq in four_bit_sequences:
            four_bit_occurrences[seq] += 1

        x = (16 / 5000) * sum(map(lambda y: y ** 2, four_bit_occurrences.values())) - 5000

        self.assert_true(
            predicate=lambda: ConfigBBS.POKER_X_LOWER_BOUND < x < ConfigBBS.POKER_X_UPPER_BOUND,
            result=f"x = {x}")
