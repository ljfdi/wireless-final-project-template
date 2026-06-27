from conftest import call_with_compatible_kwargs, to_bit_list


def _field_names(parsed):
    if isinstance(parsed, dict):
        return {str(key).lower() for key in parsed.keys()}
    return set()


def test_frame_build_and_parse_expose_required_fields(find_function):
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

    payload = [int(ch) for ch in "101100111000101"]
    frame = call_with_compatible_kwargs(
        build_frame,
        payload,
        raw_payload_length=5,
        payload_length=5,
        checksum=0x2A,
        checksum_bits=[0, 0, 1, 0, 1, 0, 1, 0],
    )
    parsed = parse_frame(frame)
    frame_bits = to_bit_list(frame if not isinstance(frame, dict) else frame.get("bits", payload))
    names = _field_names(parsed if isinstance(parsed, dict) else frame)

    assert len(frame_bits) > len(payload), "Frame should add metadata around the coded payload"
    assert any("preamble" in name for name in names), "Frame should contain preamble"
    assert any(name in {"raw_payload_length", "length", "payload_length"} for name in names), (
        "Frame should contain raw_payload_length or compatible length field"
    )
    assert any("coded_payload_length" in name or "payload_length" in name or name == "length" for name in names), (
        "Frame should contain coded_payload_length or compatible payload length field"
    )
    assert any("checksum" in name or "crc" in name for name in names), "Frame should contain checksum/CRC"
    assert any("payload" in name or "data" in name for name in names), "Frame should contain payload"
