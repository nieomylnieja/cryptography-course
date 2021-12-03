from dataclasses import dataclass


@dataclass
class ConfigBBS:
    SERIES_LENGTH = 20000
    LONG_SERIES_LENGTH = 26
    SINGLE_BITS_LOWER_BOUND = 9725
    SINGLE_BITS_UPPER_BOUND = 10275
    POKER_X_LOWER_BOUND = 2.16
    POKER_X_UPPER_BOUND = 46.17
    SERIES_TEST_TABLE = {
        "1": [2315, 2685],
        "2": [1114, 1386],
        "3": [527, 723],
        "4": [240, 384],
        "5": [103, 209],
        "6+": [103, 209],
    }
