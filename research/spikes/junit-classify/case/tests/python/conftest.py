def need_env(value):
    assert value, "SINGVST_X is not set (set by plan step S-017)"
    return value
