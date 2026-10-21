from conftest import need_env
def _toolkit(): raise ValueError("metric failed")
def test_own_assert(): assert {"status": "invalid: x"} == {"status": "measured"}
def test_need_env(): need_env("")
def test_toolkit_exception(): _toolkit()
def test_type_error(): min([1.0, None])
