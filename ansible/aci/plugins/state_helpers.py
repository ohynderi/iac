from ansible.errors import AnsibleFilterError


def _contains_state(data):
    if isinstance(data, dict):
        if 'state' in data:
            return True
        return any(_contains_state(value) for value in data.values())
    if isinstance(data, list):
        return any(_contains_state(item) for item in data)
    return False


def has_nested_state(data, include_keys=None, exclude_keys=None):
    """
    Return True if a 'state' key is present anywhere in a dict/list tree.

    include_keys / exclude_keys restrict which top-level keys of `data`
    are recursed into (only one of the two may be given). The root
    dict's own 'state' key, if present, is always honored regardless
    of these filters.
    """
    if include_keys and exclude_keys:
        raise AnsibleFilterError(
            "has_nested_state: specify only one of include_keys or exclude_keys"
        )

    if isinstance(data, list):
        return any(
            has_nested_state(item, include_keys=include_keys, exclude_keys=exclude_keys)
            for item in data
        )

    if not isinstance(data, dict):
        raise AnsibleFilterError(
            "has_nested_state expects a dict or list, got %s" % type(data).__name__
        )

    if 'state' in data:
        return True

    if include_keys is None and exclude_keys is None:
        return any(_contains_state(value) for value in data.values())

    for key, value in data.items():
        if include_keys is not None and key not in include_keys:
            continue
        if exclude_keys is not None and key in exclude_keys:
            continue
        if _contains_state(value):
            return True

    return False


class FilterModule(object):
    def filters(self):
        return {
            'has_nested_state': has_nested_state,
        }
