def decimal_to_base(n: int, b: int) -> list[int]:
    if n == 0:
        return [0]

    digits = []

    while n:
        digits.append(int(n % b))
        n //= b

    return digits[::-1]


def base_to_decimal(n: list[int], b: int) -> int:
    r = range(0, len(n))
    i = 0

    for n_idx, b_idx in zip(r, reversed(r)):
        i += n[n_idx] * pow(b, b_idx)

    return i
