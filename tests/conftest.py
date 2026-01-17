import pytest


@pytest.fixture(scope="module")
def module_version():
    from g726_seek import __version__

    return __version__
