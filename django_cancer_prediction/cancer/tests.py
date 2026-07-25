from pathlib import Path
from tempfile import NamedTemporaryFile

from django.test import SimpleTestCase

from . import views


class ModelLoadingTests(SimpleTestCase):
    def test_load_model_returns_fallback_when_pickle_is_invalid(self):
        views.model = None
        with NamedTemporaryFile("wb", delete=False) as tmp:
            tmp.write(b"not a valid pickle")
            tmp_path = tmp.name

        try:
            views.MODEL_PATH = tmp_path
            model = views.load_model()
            self.assertIsNotNone(model)
            self.assertTrue(hasattr(model, "predict_proba"))
        finally:
            Path(tmp_path).unlink(missing_ok=True)
            views.MODEL_PATH = views.DEFAULT_MODEL_PATH
