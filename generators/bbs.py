from utils.prime import generate_coprime_random_integer


class BBS:

    @staticmethod
    def new(seq_len: int) -> str:
        with open("numbers/blum.integer") as f:
            blum_int = int(f.read())
        random_natural_coprime_to_blum_int = generate_coprime_random_integer(blum_int)

        n, a, r = blum_int, random_natural_coprime_to_blum_int, seq_len

        sequence = ""
        x_0 = a ** 2 % n
        x_i_previous = x_0
        for i in range(1, r + 1):
            x_i = x_i_previous ** 2 % n
            sequence += str(0 if x_i % 2 == 0 else 1)
            x_i_previous = x_i

        return sequence
