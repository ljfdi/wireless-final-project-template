from conftest import call_with_compatible_kwargs, to_bit_list


def test_odd_bit_payload_survives_frame_qpsk_and_length_trim(find_function):
    build_frame = find_function(
        ["src.framing", "src.frame"],
        ["build_frame", "frame_build", "create_frame", "make_frame"],
        "src.framing.build_frame not implemented yet",
    )
    parse_frame = find_function(
        ["src.framing", "src.frame"],
        ["parse_frame", "frame_parse", "extract_frame", "decode_frame"],
        "src.framing.parse_frame not implemented yet",
    )
    modulate = find_function(
        ["src.modulation", "src.modem", "src.qpsk"],
        ["qpsk_modulate", "modulate_qpsk", "qpsk_mapper", "modulate"],
        "src.modulation.qpsk_modulate not implemented yet",
    )
    demodulate = find_function(
        ["src.modulation", "src.modem", "src.qpsk"],
        ["qpsk_demodulate", "demodulate_qpsk", "qpsk_demapper", "demodulate"],
        "src.modulation.qpsk_demodulate not implemented yet",
    )

    payload = [1, 0, 1, 1, 0, 1, 0]
    frame = call_with_compatible_kwargs(
        build_frame,
        payload,
        raw_payload_length=len(payload),
        payload_length=len(payload),
        checksum=0,
        checksum_bits=[0] * 8,
    )
    frame_bits = frame if not isinstance(frame, dict) else frame.get("bits") or frame.get("frame")
    symbols = modulate(to_bit_list(frame_bits))
    recovered_frame_bits = to_bit_list(demodulate(symbols))
    parsed = parse_frame(recovered_frame_bits)

    recovered_payload = parsed.get("payload") if isinstance(parsed, dict) else parsed
    assert to_bit_list(recovered_payload)[: len(payload)] == payload
