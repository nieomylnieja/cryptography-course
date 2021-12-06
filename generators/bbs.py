from typing import Optional

from utils.prime import generate_coprime_random_integer

from rich.console import Console
from rich.markdown import Markdown

console = Console()


class BBS:

    @staticmethod
    def new(seq_len: int) -> Optional[str]:
        try:
            with open("numbers/blum.integer") as f:
                blum_int = int(f.read())
        except FileNotFoundError:
            console.print(f"[bold red]Generate the blum integer first![/bold red]")
            console.print(
                Markdown(f"Run this command first: `./run.py generate-blum-int -p <P_PRIME_LEN> -q <Q_PRIME_LEN>`"))
            return None

        random_natural_coprime_to_blum_int = generate_coprime_random_integer(blum_int)

        n, a, r = blum_int, random_natural_coprime_to_blum_int, seq_len

        sequence = ""
        x_0 = a ** 2 % n
        x_i_previous = x_0
        for i in range(1, r + 1):
            x_i = x_i_previous ** 2 % n
            sequence += str(0 if x_i % 2 == 0 else 1)
            x_i_previous = x_i

        console.print(f"[bold magenta]Generated sequence[/bold magenta]: {sequence}")

        return sequence
