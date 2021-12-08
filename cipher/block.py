import os
from abc import ABCMeta, abstractmethod

from bitarray import bitarray
from cryptography.hazmat.primitives.ciphers import modes, algorithms, Cipher
from rich.console import Console
from rich.markdown import Markdown

from cipher.booboo import BooBoo

console = Console()


class BBSCipher:
    encoding = "utf-8"

    encrypted = b""

    def __init__(self, bbs_file_path: str):
        if not bbs_file_path:
            raise ValueError("provide file path to BBS sequence with -f")
        with open(bbs_file_path, "r") as f:
            self._key = bitarray(f.read())

    def run(self, msg: str):
        console.print(f"IN:  {msg}", style="blue")

        encrypted = self.encrypt(msg)
        pretty_enc = str(encrypted).lstrip('b').strip("'")
        console.print(f"ENC: {pretty_enc}", style="red")

        self.encrypted = encrypted

        decrypted = self.decrypt(encrypted)
        console.print(f"DEC: {decrypted.decode('utf-8')}", style="yellow")

    def encrypt(self, msg: str) -> bytes:
        msg_bits = bitarray()
        msg_bits.frombytes(msg.encode(self.encoding))
        return self._xor_both(msg_bits)

    def decrypt(self, ciphered: bytes) -> bytes:
        ciphered_bits = bitarray()
        ciphered_bits.frombytes(ciphered)
        return self._xor_both(ciphered_bits)

    def _xor_both(self, msg_bits: bitarray) -> bytes:
        if len(self._key) < len(msg_bits):
            raise AttributeError(f"BBS sequence should be at least as long as the bit form of the message"
                                 f", was: {len(msg_bits)} vs. key: {len(self._key)}")

        key_bits = self._key
        if len(self._key) > len(msg_bits):
            key_bits = self._key[:len(msg_bits)]

        return (msg_bits ^ key_bits).tobytes()


class BlockCipher:
    enc_data: str = ""
    dec_data: str = ""

    def __init__(self, algorithm: algorithms.CipherAlgorithm, mode: modes.Mode, data: bytes):
        self.tag = None
        self.data = data
        self.cipher = Cipher(algorithm, mode)

    def encrypt(self):
        encryptor = self.cipher.encryptor()
        self.enc_data = encryptor.update(self.data) + encryptor.finalize()
        if isinstance(self.cipher.mode, modes.ModeWithAuthenticationTag):
            self.tag = encryptor.tag

    def decrypt(self):
        decryptor = self.cipher.decryptor()
        if isinstance(self.cipher.mode, modes.ModeWithAuthenticationTag):
            self.dec_data = decryptor.update(self.enc_data) + decryptor.finalize_with_tag(self.tag)
        else:
            self.dec_data = decryptor.update(self.enc_data) + decryptor.finalize()


class CustomMode(metaclass=ABCMeta):
    block_size = 16

    def __init__(self):
        self.black_box = self.BlackBox()

    class BlackBox:
        def __init__(self):
            self._cipher = Cipher(algorithms.AES(os.urandom(CBCMode.block_size)), modes.ECB())

        def encrypt(self, data: bytes) -> bytes:
            encryptor = self._cipher.encryptor()
            return encryptor.update(data) + encryptor.finalize()

        def decrypt(self, data: bytes) -> bytes:
            encryptor = self._cipher.decryptor()
            return encryptor.update(data) + encryptor.finalize()

    def run(self, data: bytes, boo_boo: str):
        encrypted_blocks = self._encrypt(data)
        encrypted_blocks = BooBoo(encrypted_blocks).from_args(boo_boo)
        decrypted_blocks = self._decrypt(b"".join(encrypted_blocks))

        input_blocks = self._split(data)

        # adjust the length of all lists to fit into zip()
        if len(decrypted_blocks) > len(input_blocks):
            input_blocks.extend((len(decrypted_blocks) - len(input_blocks)) * [b""])
        if len(decrypted_blocks) < len(input_blocks):
            diff = len(input_blocks) - len(decrypted_blocks)
            encrypted_blocks.extend(diff * [b""])
            decrypted_blocks.extend(diff * [b""])

        block_n = 0
        for i, enc, dec in zip(input_blocks, encrypted_blocks, decrypted_blocks):
            try:
                decoded_str = dec.decode('utf-8')
            except UnicodeDecodeError:
                decoded_str = dec
            block_n += 1
            console.print(f"""BLOCK {block_n} 
• IN:  [bold blue]'{i.decode('utf-8')}'[/bold blue]
• ENC: [bold red]{enc.__str__().lstrip("b")}[/bold red]
• DEC: [bold yellow]'{decoded_str}'[/bold yellow]
            """, style="bold green")

        console.print(Markdown(f"""## SUMMARY:
### Mode: {self.name}
### BooBoo: {boo_boo}
"""))

    @abstractmethod
    def _encrypt(self, data: bytes) -> list[bytes]:
        raise NotImplementedError("CustomMode must implement _encrypt method")

    @abstractmethod
    def _decrypt(self, data: bytes) -> list[bytes]:
        raise NotImplementedError("CustomMode must implement _decrypt method")

    @property
    @abstractmethod
    def name(self):
        raise NotImplementedError("CustomMode must implement name property")

    @staticmethod
    def _xor(first: bytes, second: bytes) -> bytes:
        if len(first) != len(second):
            raise ValueError("to perform xor both bytes should be equal")
        return bytes(b1 ^ b2 for b1, b2 in zip(first, second))

    def _split(self, s: bytes) -> list[bytes]:
        return [s[k:k + self.block_size] for k in range(0, len(s), self.block_size)]


class CBCMode(CustomMode):
    name = "CBC"

    def __init__(self):
        super().__init__()
        self.iv = os.urandom(self.block_size)

    def _encrypt(self, data: bytes) -> list[bytes]:
        blocks = self._split(data)

        encrypted: list[bytes] = []
        previous_result = self.iv

        for i, block in enumerate(blocks):
            try:
                block = CMS.add_padding(block, self.block_size)
                previous_result = self.black_box.encrypt(self._xor(previous_result, block))
                encrypted.append(previous_result)
            except ValueError as e:
                console.log(f"Skipping block NR {i} during encryption due to exception: {e}")
                encrypted.append(b"FAILED BLOCK")

        return encrypted

    def _decrypt(self, enc: bytes) -> list[bytes]:
        blocks = self._split(enc)

        decrypted: list[bytes] = []
        previous_block = self.iv

        for i, block in enumerate(blocks):
            try:
                dec_block = self._xor(previous_block, self.black_box.decrypt(block))
                dec_block = CMS.rm_padding(dec_block, self.block_size)
            except ValueError as e:
                console.log(f"Skipping block NR {i} during decryption due to exception: {e}")
                dec_block = b"FAILED BLOCK"
            decrypted.append(dec_block)
            previous_block = block

        return decrypted


class CTRMode(CustomMode):
    name = "CTR"

    def __init__(self):
        super().__init__()
        self.nonce = os.urandom(self.block_size)

    def _encrypt(self, data: bytes) -> list[bytes]:
        blocks = self._split(data)

        encrypted: list[bytes] = []
        nonce_int = int.from_bytes(self.nonce, "big")

        for i, block in enumerate(blocks):
            try:
                i_nonce = (nonce_int + i).to_bytes(len(self.nonce), "big")
                i_nonce = self.black_box.encrypt(i_nonce)
                block = CMS.add_padding(block, self.block_size)
                i_enc = self._xor(block, i_nonce)
            except ValueError as e:
                console.log(f"Skipping block NR {i} during encryption due to exception: {e}")
                i_enc = b"FAILED BLOCK"
            encrypted.append(i_enc)

        return encrypted

    def _decrypt(self, enc: bytes) -> list[bytes]:
        blocks = self._split(enc)

        decrypted: list[bytes] = []
        nonce_int = int.from_bytes(self.nonce, "big")

        for i, block in enumerate(blocks):
            try:
                i_nonce = (nonce_int + i).to_bytes(len(self.nonce), "big")
                i_nonce = self.black_box.encrypt(i_nonce)
                i_dec = self._xor(block, i_nonce)
                i_dec = CMS.rm_padding(i_dec, self.block_size)
            except ValueError as e:
                console.log(f"Skipping block NR {i} during decryption due to exception: {e}")
                i_dec = b"FAILED BLOCK"
            decrypted.append(i_dec)

        return decrypted


class CMS:

    @staticmethod
    def add_padding(block: bytes, block_size: int) -> bytes:
        if len(block) < block_size:
            diff = block_size - len(block)
            block = block + diff * bytes([diff])
        return block

    @staticmethod
    def rm_padding(block: bytes, block_size: int) -> bytes:
        last_byte = block[len(block) - 1]
        if last_byte <= block_size:
            ctr = 0
            for b in block[::-1]:
                if b != last_byte or ctr >= last_byte:
                    break
                ctr += 1
            if ctr == last_byte:
                block = block[:len(block) - last_byte]
        return block
