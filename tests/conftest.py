import pytest

from core import i18n


@pytest.fixture(autouse=True)
def _no_translations(tmp_path):
    i18n.load_language("fr", lang_dir=str(tmp_path))
    i18n.set_scope("common")
