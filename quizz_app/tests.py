import logging

from django.test import SimpleTestCase

from .safe_logging import RedactingFilter


class RedactingFilterTests(SimpleTestCase):
    def test_filter_preserves_numeric_logging_args(self):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="status=%d",
            args=(429,),
            exc_info=None,
        )

        RedactingFilter().filter(record)

        self.assertEqual(record.getMessage(), "status=429")

