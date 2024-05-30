import heapq
from typing import Generator
import collections
import itertools


HuffmanTree = tuple[int, "HuffmanTree", "HuffmanTree"] | tuple[int, int]
PrefixTable = dict[int, tuple[int]]
PrefixTree = tuple["PrefixTree", "PrefixTree"] | int | None


byte_to_bits = {i: b for i, b in enumerate(itertools.product((0, 1), repeat=8))}
bits_to_byte = {b: i for i, b in byte_to_bits.items()}


def bits_to_bytes(bits: tuple[int]) -> bytes:
    return bytes(
        bits_to_byte[b + (0,) * (8 - len(b))] for b in itertools.batched(bits, 8)
    )


def bytes_to_bits(bytes: bytes) -> tuple[int]:
    return tuple(itertools.chain.from_iterable(map(lambda i: byte_to_bits[i], bytes)))


def compress(s: bytes) -> bytes:
    def build_optimal_prefix_table(freqs: dict[int, int]) -> dict[int, tuple[int]]:
        def build_huffman_tree(freqs: dict[int, int]) -> HuffmanTree:
            def merge(l: HuffmanTree, r: HuffmanTree) -> HuffmanTree:
                (lf, li), l = l[0], l[1:]
                (rf, ri), r = r[0], r[1:]
                priority = (lf + rf, min(li, ri))
                return (priority, l, r) if lf <= rf else (priority, r, l)

            # to break ties in frequency, we use the index of the order in which we
            # iterated the items, which guarentees there are no ties after comparing the
            # tuple of (freq, i)
            pq = [((freq, i), val) for i, (val, freq) in enumerate(freqs.items())]
            heapq.heapify(pq)
            while len(pq) > 1:
                l = heapq.heappop(pq)
                r = heapq.heappop(pq)
                n = merge(l, r)
                heapq.heappush(pq, n)
            root = pq[0][1:]
            return root

        def build_table_from_huffman(root: HuffmanTree) -> PrefixTable:
            d = {}

            def visit(node: HuffmanTree, path: tuple[int]):
                match node:
                    case (data,):  # leaf
                        d[data] = path
                    case (l, r):  # node
                        visit(l, path + (0,))
                        visit(r, path + (1,))
                    case _:
                        raise Exception("unreachable")

            visit(root, ())
            return d

        root = build_huffman_tree(freqs)
        table = build_table_from_huffman(root)
        return table

    # frequency at which each byte appears in the data
    freqs = collections.Counter(s)
    if len(freqs) < 2:
        raise ValueError("must be more than one unique byte in input")

    # use the freqs to build an optimal prefix table
    prefix_table = build_optimal_prefix_table(freqs)

    # map the bytes to prefixes and chain it all together
    data_bits = tuple(itertools.chain.from_iterable(map(lambda i: prefix_table[i], s)))
    data_bytes = bits_to_bytes(data_bits)
    num_data_bits = len(data_bits)

    # save prefix table as bytes
    def prefix_table_to_bytes(
        prefix_table: PrefixTable,
    ) -> Generator[bytes, None, None]:
        for i, prefix in prefix_table.items():
            yield i
            yield len(prefix)
            yield from bits_to_bytes(prefix + (0,) * (64 - len(prefix)))

    prefix_bytes = bytes(prefix_table_to_bytes(prefix_table))
    num_prefixes = len(prefix_table)

    # output format:
    #   first 8 bytes = 64 bit int for num bits in data
    #   next 8 bytes = 64 bit int for num prefixes
    #   for num prefixes, we have:
    #       1 byte for the data itself (which char)
    #       1 byte for the len of path
    #       8 bytes for path as bitseq (right padded with 0 bits)
    #   remaining bits make up the data itself
    return (
        num_data_bits.to_bytes(8) + num_prefixes.to_bytes(8) + prefix_bytes + data_bytes
    )


def decompress(s: bytes) -> bytes:
    # get segments of the bytes
    num_data_bits = int.from_bytes(s[:8])
    num_prefixes = int.from_bytes(s[8:16])
    start_of_prefix_seg, end_of_prefix_seg = 16, 16 + num_prefixes * 10
    prefix_bytes = s[start_of_prefix_seg:end_of_prefix_seg]
    data_bytes = s[end_of_prefix_seg:]

    # recover prefix table
    prefix_table = {}
    for data, pathlen, *path in itertools.batched(prefix_bytes, 10):
        prefix_table[data] = bytes_to_bits(path)[:pathlen]

    # build prefix tree
    def build_prefix_tree(prefix_table: PrefixTable) -> PrefixTree:
        def add(node: PrefixTree, path: tuple[int], data: int) -> PrefixTree:
            match (node, path):
                case None, ():
                    return data
                case None, (bit, *rest):
                    t = add(None, rest, data)
                    return (t, None) if bit == 0 else (None, t)
                case (l, r), (bit, *rest):
                    return (
                        (add(l, rest, data), r) if bit == 0 else (l, add(r, rest, data))
                    )
                case _:
                    raise ValueError("unreachable")

        root = (None, None)
        for data, prefix in prefix_table.items():
            root = add(root, prefix, data)
        return root

    prefix_tree = build_prefix_tree(prefix_table)

    # decode data segement
    data_bits = bytes_to_bits(data_bytes)
    data_bits = data_bits[:num_data_bits]

    def decode_data_bits(
        prefix_tree: PrefixTree, data_bits: bytes
    ) -> Generator[int, None, None]:
        bits = iter(data_bits)
        node = prefix_tree
        try:
            while True:
                match node:
                    case int():
                        yield node
                        node = prefix_tree
                    case (l, r):
                        bit = next(bits)
                        node = l if bit == 0 else r
                    case _:
                        raise ValueError("unreachable")
        except StopIteration:
            pass

    return bytes(decode_data_bits(prefix_tree, data_bits))


if __name__ == "__main__":
    import argparse

    command_map = {"compress": compress, "decompress": decompress}

    parser = argparse.ArgumentParser(
        "File compression via huffman encodings on byte sequences.",
        usage="""
        python3.12 compress.py compress original.txt compressed.txt
        python3.12 compress.py decompress compressed.txt decompressed.txt
        """,
    )
    parser.add_argument("command", choices=command_map)
    parser.add_argument("input_file", type=str)
    parser.add_argument("output_file", type=str)
    args = parser.parse_args()

    with open(args.input_file, "rb") as fi:
        input_bytes = fi.read()
    output_bytes = command_map[args.command](input_bytes)
    with open(args.output_file, "wb") as fo:
        fo.write(output_bytes)
