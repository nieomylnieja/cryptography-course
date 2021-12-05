import json
from random import randint

from rich import print_json
from rich.console import Console

from utils.base import decimal_to_base, base_to_decimal
from utils.prime import generate_prime_number, generate_coprime_random_integer

console = Console()


class RSASimple:

    def __init__(self):
        self.preset = None

    def run(self, msg: bytes):
        if not self.preset:
            console.log("Generating new preset")
            self.generate_preset()
        else:
            console.log("Using existing preset")
        print_json(json.dumps(self.preset))

        encrypted = self.encrypt(msg)
        decrypted = self.decrypt(encrypted)

        console.print(f"""
[bold]Input:[/bold]
[blue]{str(msg).lstrip('b')}[/blue]
[bold]Encrypted:[/bold]
[red]{encrypted}[/red]
[bold]Decrypted:[/bold]
[green]{str(decrypted).lstrip('b')}[/green]
""")

    def encrypt(self, msg: bytes) -> list[int]:
        encrypted = []
        for m in decimal_to_base(int.from_bytes(msg, "big"), self.preset["n"]):
            c = pow(m, self.preset["e"], self.preset["n"])
            encrypted.append(c)
        return encrypted

    def decrypt(self, enc: list[int]) -> bytes:
        decrypted: list[int] = []
        for c in enc:
            m = pow(c, self.preset["d"], self.preset["n"])
            decrypted.append(m)

        msg_int = base_to_decimal(decrypted, self.preset["n"])
        return msg_int.to_bytes((msg_int.bit_length() + 7) // 8, "big")

    def with_preset(self, data: str):
        self.preset = json.loads(data)

    def generate_preset(self):
        # choose two random 4-digit primes
        p = generate_prime_number(self._rnd_int())
        q = generate_prime_number(self._rnd_int())
        while p == q:
            q = generate_prime_number(self._rnd_int())
        # calculate n by multiplying them both
        n = p * q
        # calculate φ(n) = (p – 1)(q – 1)
        phi_n = (p - 1) * (q - 1)
        # generate e, as a coprime to φ(n)
        e = generate_coprime_random_integer(phi_n, self._rnd_int())
        # generate d, so that e·d is congruent to modulo of φ(n)
        d = 0
        while d == 0:
            proposed_d = randint(1, phi_n)
            if (e * proposed_d - 1) % phi_n == 0:
                d = proposed_d

        self.preset = {"p": p, "q": q, "n": n, "phi": phi_n, "e": e, "d": d}

    @staticmethod
    def _rnd_int() -> int:
        return randint(10, 11)
