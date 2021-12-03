import os
from abc import ABCMeta, abstractmethod

from bitarray import bitarray
from cryptography.hazmat.primitives.ciphers import modes, algorithms, Cipher
from rich.console import Console

console = Console()


class BBSCipher:
    encoding = "utf-8"

    def __init__(self, bbs_file_path: str):
        with open(bbs_file_path, "r") as f:
            self._key = bitarray(f.read())

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
            raise AttributeError("BBS sequence should be at least as long as the bit form of the message")

        key_bits = self._key
        if len(self._key) > len(msg_bits):
            key_bits = self._key[:len(msg_bits)]

        return (msg_bits ^ key_bits).tobytes()


class BlockCipher:
    enc_data: str = ""
    dec_data: str = ""

    def __init__(self, algorithm: algorithms.CipherAlgorithm, mode: modes.Mode, data: bytes):
        self.data = data
        self.cipher = Cipher(algorithm, mode)

    @property
    def details(self) -> dict[str:str]:
        return {
            "algo": self.cipher.algorithm.name,
            "mode": self.cipher.mode.name,
        }

    def encrypt(self):
        encryptor = self.cipher.encryptor()
        self.enc_data = encryptor.update(self.data) + encryptor.finalize()

    def decrypt(self):
        decryptor = self.cipher.decryptor()
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

    def run(self, data: bytes):
        encrypted_block = self._encrypt(data)
        decrypted_blocks = self._decrypt(b"".join(encrypted_block))

        input_blocks = self._split(data)
        block_n = 0
        for i, enc, dec in zip(input_blocks, encrypted_block, decrypted_blocks):
            block_n += 1
            console.print(f"""BLOCK {block_n}
• IN:  [bold blue]'{i.decode('utf-8')}'[/bold blue]
• ENC: [bold red]{enc.__str__().lstrip("b")}[/bold red]
• DEC: [bold yellow]'{dec.decode('utf-8')}'[/bold yellow]
            """, style="bold green")

    @abstractmethod
    def _encrypt(self, data: bytes) -> list[bytes]:
        raise NotImplementedError("CustomMode must implement _encrypt method")

    @abstractmethod
    def _decrypt(self, data: bytes) -> list[bytes]:
        raise NotImplementedError("CustomMode must implement _decrypt method")

    @staticmethod
    def _xor(first: bytes, second: bytes) -> bytes:
        if len(first) != len(second):
            raise ValueError("to perform xor both bytes should be equal")
        return bytes(b1 ^ b2 for b1, b2 in zip(first, second))

    def _split(self, s: bytes) -> list[bytes]:
        return [s[k:k + self.block_size] for k in range(0, len(s), self.block_size)]


class CBCMode(CustomMode):

    def __init__(self):
        super().__init__()
        self.iv = os.urandom(self.block_size)

    def _encrypt(self, data: bytes) -> list[bytes]:
        blocks = self._split(data)

        encrypted: list[bytes] = []
        previous_result = self.iv

        for block in blocks:
            block = CMS.add_padding(block, self.block_size)
            previous_result = self.black_box.encrypt(self._xor(previous_result, block))
            encrypted.append(previous_result)

        return encrypted

    def _decrypt(self, enc: bytes) -> list[bytes]:
        blocks = self._split(enc)

        decrypted: list[bytes] = []
        previous_block = self.iv

        for block in blocks:
            dec_block = self._xor(previous_block, self.black_box.decrypt(block))
            dec_block = CMS.rm_padding(dec_block, self.block_size)
            decrypted.append(dec_block)
            previous_block = block

        return decrypted


class GCMMode(CustomMode):

    def __init__(self):
        super().__init__()
        self.nonce = os.urandom(self.block_size)

    def _encrypt(self, data: bytes) -> list[bytes]:
        pass

    def _decrypt(self, data: bytes) -> list[bytes]:
        pass


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
