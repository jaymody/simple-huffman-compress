import compress


def test_bytes(input_bytes: bytes):
    compressed_bytes = compress.compress(input_bytes)
    output_bytes = compress.decompress(compressed_bytes)
    assert input_bytes == output_bytes


def test_raises(input_bytes: bytes):
    try:
        compress.compress("")
        assert False, "no exception was raised"
    except Exception as e:
        assert repr(e) == "ValueError('must be more than one unique byte in input')"


if __name__ == "__main__":
    lorem_ipsum = b"Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."

    test_bytes(b"ab")
    test_bytes(b"abb")
    test_bytes(b"apple")
    test_bytes(b"banana")
    test_bytes(lorem_ipsum)
    test_bytes(lorem_ipsum * 100)
    test_bytes(bytes(list(range(256))))
    test_bytes(bytes(list(range(256))) * 100)

    test_raises("")
    test_raises("a")
    test_raises("aaaaaa")
    test_raises("  ")
