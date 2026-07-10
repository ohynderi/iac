ABSENT = object()  # sentinel: assert the key is not present at all


def assert_matches(actual, expected, path="body"):
    """Assert `actual` contains at least everything in `expected`.

    - dict: only keys present in `expected` are checked (extra keys in
      `actual` are ignored), except a value of ABSENT which asserts the
      key is *not* in `actual`.
    - list: compared elementwise, and lengths must match exactly.
    - anything else: compared with ==.
    """
    if isinstance(expected, dict):
        assert isinstance(actual, dict), f"{path}: expected dict, got {actual!r}"
        for key, exp_value in expected.items():
            sub_path = f"{path}.{key}"
            if exp_value is ABSENT:
                assert key not in actual, f"{sub_path}: expected key to be absent, found {actual[key]!r}"
                continue
            assert key in actual, f"{sub_path}: expected key missing from {actual!r}"
            assert_matches(actual[key], exp_value, sub_path)

    elif isinstance(expected, list):
        assert isinstance(actual, list), f"{path}: expected list, got {actual!r}"
        assert len(actual) == len(expected), (
            f"{path}: expected {len(expected)} item(s), got {len(actual)}: {actual!r}"
        )
        for i, (act_item, exp_item) in enumerate(zip(actual, expected)):
            assert_matches(act_item, exp_item, f"{path}[{i}]")

    else:
        assert actual == expected, f"{path}: expected {expected!r}, got {actual!r}"
