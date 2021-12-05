import json
from random import randint

from rich import print_json
from rich.console import Console
from rich.table import Table

from utils.base import decimal_to_base, base_to_decimal
from utils.prime import generate_prime_number, generate_coprime_random_integer

console = Console()


class RSASimple:

    def __init__(self):
        self.preset = None

    def run_encryption(self, msg: bytes):
        if not self.preset:
            console.log("Generating new preset")
            self.preset = self.generate_preset()
        else:
            console.log("Using existing preset")
        print_json(json.dumps(self.preset))

        encrypted = self.encrypt(msg, "e")
        decrypted = self.decrypt(encrypted, "d")

        console.print(f"""
[bold]Input:[/bold]
[blue]{str(msg).lstrip('b')}[/blue]
[bold]Encrypted:[/bold]
[red]{encrypted}[/red]
[bold]Decrypted:[/bold]
[green]{str(decrypted).lstrip('b')}[/green]
""")

    def run_signing(self, msg: bytes):
        preset_a = self.generate_preset()
        preset_b = self.generate_preset()

        console.line(1)
        console.print("[bold]GENERATED PRESETS:[/bold]")
        print_json(json.dumps({"A": preset_a, "B": preset_b}))

        encrypted_a = self.encrypt(msg, "d", preset=preset_a)
        encrypted_b = self.encrypt(msg, "d", preset=preset_b)

        # correct decryption
        results = [
            ["A", preset_a["d"], self.decrypt(encrypted_a, "e", preset=preset_a), "A", preset_a["e"]],
            ["B", preset_b["d"], self.decrypt(encrypted_b, "e", preset=preset_b), "B", preset_b["e"]],
            ["A", preset_a["d"], self.decrypt(encrypted_a, "e", preset=preset_b), "B", preset_b["e"]],
            ["B", preset_b["d"], self.decrypt(encrypted_b, "e", preset=preset_a), "A", preset_a["e"]],
        ]

        table = Table(title="Signing results")

        table.add_column("Signed with", justify="center", style="cyan")
        table.add_column("Private key", justify="left", style="cyan")
        table.add_column("Result", style="magenta")
        table.add_column("Decrypted with", justify="center", style="green")
        table.add_column("Public key", justify="left", style="green")

        for result in results:
            for i in [0, 3]:
                result[i] = f"[bold]{result[i]}[/bold]"
            for i in [1, 2, 4]:
                result[i] = str(result[i]).lstrip("b").strip("'")
            table.add_row(*result)

        console.line(1)
        console.print(table)

    def encrypt(self, msg: bytes, key: str, preset: dict = None) -> list[int]:
        if preset is None:
            preset = self.preset

        encrypted = []
        for m in decimal_to_base(int.from_bytes(msg, "big"), preset["n"]):
            c = pow(m, preset[key], preset["n"])
            encrypted.append(c)
        return encrypted

    def decrypt(self, enc: list[int], key: str, preset: dict = None) -> bytes:
        if preset is None:
            preset = self.preset

        decrypted: list[int] = []
        for c in enc:
            m = pow(c, preset[key], preset["n"])
            decrypted.append(m)

        msg_int = base_to_decimal(decrypted, preset["n"])
        return msg_int.to_bytes((msg_int.bit_length() + 7) // 8, "big")

    def with_preset(self, data: str):
        self.preset = json.loads(data)

    def generate_preset(self) -> dict:
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

        return {"p": p, "q": q, "n": n, "phi": phi_n, "e": e, "d": d}

    @staticmethod
    def _rnd_int() -> int:
        return randint(10, 11)
