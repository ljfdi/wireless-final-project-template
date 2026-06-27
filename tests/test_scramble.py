from conftest import to_bit_list


def test_pn_scramble_and_descramble_round_trip(find_function):
    scramble = find_function(
        ["src.scramble", "src.scrambler", "src.crypto"],
        ["scramble", "scramble_bits", "encrypt", "encrypt_bits"],
        "src.scramble.scramble not implemented yet",
    )
    descramble = find_function(
        ["src.scramble", "src.scrambler", "src.crypto"],
        ["descramble", "descramble_bits", "decrypt", "decrypt_bits"],
        "src.scramble.descramble not implemented yet",
    )

    bits = [int(ch) for ch in "010011101011000111010101001101"]
    scrambled_1 = to_bit_list(scramble(bits, seed=2026))
    scrambled_2 = to_bit_list(scramble(bits, seed=2026))
    recovered = to_bit_list(descramble(scrambled_1, seed=2026))

    assert scrambled_1 == scrambled_2, "PN scrambling should be reproducible for a fixed seed"
    assert recovered[: len(bits)] == bits
