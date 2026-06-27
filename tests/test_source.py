from conftest import to_bit_list


def test_utf8_text_and_bitstream_round_trip(find_function):
    encode = find_function(
        ["src.source", "src.source_codec", "src.codec"],
        ["source_encode", "text_to_bits"],
        "src.source.source_encode not implemented yet",
    )
    decode = find_function(
        ["src.source", "src.source_codec", "src.codec"],
        ["source_decode", "bits_to_text"],
        "src.source.source_decode not implemented yet",
    )

    text = "无线通信技术：QPSK、AWGN、同步与信道编码。"
    bits = to_bit_list(encode(text))

    assert bits, "source_encode should return a non-empty bitstream"
    assert len(bits) % 8 == 0, "UTF-8 source bits should be byte aligned"
    assert set(bits) <= {0, 1}
    assert decode(bits) == text
