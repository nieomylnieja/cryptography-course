import os
from random import randint


# TODO add summary
class BooBoo:
    """
    BooBoo will try to break the cipher in some way.
    """

    Blocks = list[bytes]

    def __init__(self, blocks: Blocks):
        self.blocks = blocks

    def from_args(self, boo_boo: str) -> Blocks:
        boo_boo_func_name = "_" + boo_boo.replace("-", "_")
        if not hasattr(self, boo_boo_func_name):
            raise ValueError(f"unsupported boo-boo: {boo_boo}")
        mess_with_the_blocks = getattr(self, boo_boo_func_name)

        mess_with_the_blocks()

        return self.blocks

    def _none(self):
        pass

    def _rm_random_block(self):
        self.blocks.pop(self._rnd_idx())

    def _clone_random_block(self):
        rnd_block_idx = self._rnd_idx()
        self.blocks.insert(rnd_block_idx + 1, self.blocks[rnd_block_idx])

    def _swap_random_blocks(self):
        rnd_block_idx_1 = self._rnd_idx()
        rnd_block_idx_2 = self._rnd_idx()
        while rnd_block_idx_2 == rnd_block_idx_1:
            rnd_block_idx_2 = self._rnd_idx()

        self.blocks[rnd_block_idx_1], self.blocks[rnd_block_idx_2] = \
            self.blocks[rnd_block_idx_2], self.blocks[rnd_block_idx_1]

    def _swap_random_bytes_in_random_block(self):
        rnd_block_idx = self._rnd_idx()
        rnd_block = self.blocks[rnd_block_idx]

        rnd_byte_idx_1 = self._rnd_idx(len(rnd_block) - 1)
        rnd_byte_idx_2 = self._rnd_idx(len(rnd_block) - 1)
        while rnd_byte_idx_2 == rnd_byte_idx_1:
            rnd_byte_idx_2 = self._rnd_idx(len(rnd_block) - 1)

        rnd_block_arr = bytearray(rnd_block)

        rnd_block_arr[rnd_byte_idx_1], rnd_block_arr[rnd_byte_idx_2] = \
            rnd_block_arr[rnd_byte_idx_2], rnd_block_arr[rnd_byte_idx_1]

        self.blocks[rnd_block_idx] = bytes(rnd_block_arr)

    def _modify_random_byte_in_random_block(self):
        rnd_block_idx = self._rnd_idx()
        rnd_block = self.blocks[rnd_block_idx]

        rnd_block_arr = bytearray(rnd_block)

        rnd_byte_idx = self._rnd_idx(len(rnd_block) - 1)
        rnd_block_arr[rnd_byte_idx] = int.from_bytes(os.urandom(1), "big")

        self.blocks[rnd_block_idx] = bytes(rnd_block_arr)

    def _rm_random_byte_from_random_block(self):
        rnd_block_idx = self._rnd_idx()
        rnd_block = self.blocks[rnd_block_idx]

        rnd_block_arr = bytearray(rnd_block)

        rnd_byte_idx = self._rnd_idx(len(rnd_block) - 1)
        rnd_block_arr.pop(rnd_byte_idx)

        self.blocks[rnd_block_idx] = bytes(rnd_block_arr)

    def _rnd_idx(self, upper_bound: int = 0) -> int:
        if upper_bound == 0:
            upper_bound = len(self.blocks) - 1
        return randint(0, upper_bound)
