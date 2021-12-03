from utils.prime import generate_prime_number


def generate_blum_integer(p_len=512, q_len=512) -> int:
    p = _generate_prime_congruent_to_3_mod_4(p_len)
    q = _generate_prime_congruent_to_3_mod_4(q_len)
    return p * q


def _generate_prime_congruent_to_3_mod_4(length: int) -> int:
    p = 0
    while p % 4 != 3:
        p = generate_prime_number(length)
    return p
