from conftest import to_bit_list


def test_channel_encode_and_decode_noiseless_round_trip(find_function):
    encode = find_function(
        ["src.channel_coding", "src.coding", "src.channel_code"],
        ["channel_encode", "encode", "encode_bits", "fec_encode"],
        "src.channel_coding.channel_encode not implemented yet",
    )
    decode = find_function(
        ["src.channel_coding", "src.coding", "src.channel_code"],
        ["channel_decode", "decode", "decode_bits", "fec_decode"],
        "src.channel_coding.channel_decode not implemented yet",
    )

    bits = [int(ch) for ch in "10110011100010101101"]
    encoded = to_bit_list(encode(bits))
    recovered = to_bit_list(decode(encoded))

    assert encoded, "channel_encode should return coded bits"
    assert recovered[: len(bits)] == bits
