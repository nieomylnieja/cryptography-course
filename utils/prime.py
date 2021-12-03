from math import gcd
from random import randrange, getrandbits


def _is_prime(n, k=128) -> bool:
    """ Test if a number is prime
        Args:
            n -- int -- the number to test
            k -- int -- the number of tests to do
        return True if n is prime
    """
    if n == 2 or n == 3:
        return True
    if n <= 1 or n % 2 == 0:
        return False
    s = 0
    r = n - 1
    while r & 1 == 0:
        s += 1
        r //= 2
    for _ in range(k):
        a = randrange(2, n - 1)
        x = pow(a, r, n)
        if x != 1 and x != n - 1:
            j = 1
            while j < s and x != n - 1:
                x = pow(x, 2, n)
                if x == 1:
                    return False
                j += 1
            if x != n - 1:
                return False
    return True


def generate_prime_number(length=1024) -> int:
    p = 0
    while not _is_prime(p, 128):
        # apply a mask to set MSB and LSB to 1
        p = getrandbits(length) | (1 << length - 1) | 1
    return p


def generate_coprime_random_integer(p: int, length=512) -> int:
    a = abs(getrandbits(length))
    while gcd(p, a) != 1:
        a = abs(getrandbits(length))
    return a
