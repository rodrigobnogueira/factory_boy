# Copyright: See the LICENSE file.

import unittest

import factory
from factory import SKIP


class SkipSentinelTestCase(unittest.TestCase):
    """Tests for the SKIP sentinel object."""

    def test_skip_basic(self):
        """Test basic SKIP exclusion from DictFactory."""

        class MyDictFactory(factory.DictFactory):
            name = "John"
            email = SKIP
            phone = "123-456"

        result = MyDictFactory()
        self.assertEqual(result, {"name": "John", "phone": "123-456"})
        self.assertNotIn("email", result)

    def test_skip_override(self):
        """Test SKIP can be overridden per-instance."""

        class MyDictFactory(factory.DictFactory):
            name = "John"
            email = "default@example.com"

        result = MyDictFactory(email=SKIP)
        self.assertEqual(result, {"name": "John"})
        self.assertNotIn("email", result)

    def test_skip_all(self):
        """Test all fields can be SKIP."""

        class MyDictFactory(factory.DictFactory):
            field1 = SKIP
            field2 = SKIP

        result = MyDictFactory()
        self.assertEqual(result, {})

    def test_skip_with_lazy_function(self):
        """Test SKIP works with declarations."""

        class MyDictFactory(factory.DictFactory):
            name = factory.LazyFunction(lambda: "Generated")
            skipped = SKIP
            value = 42

        result = MyDictFactory()
        self.assertEqual(result["name"], "Generated")
        self.assertEqual(result["value"], 42)
        self.assertNotIn("skipped", result)

    def test_skip_singleton(self):
        """Test SKIP is a singleton."""
        another_skip = factory.SKIP
        self.assertIs(SKIP, another_skip)

    def test_skip_bool(self):
        """Test SKIP is falsy."""
        self.assertFalse(SKIP)
        self.assertFalse(bool(SKIP))

    def test_skip_with_transformer(self):
        """Test SKIP works with Transformer declarations."""

        class MyDictFactory(factory.DictFactory):
            timeout = factory.Transformer(30.0, transform=int)

        result = MyDictFactory()
        self.assertEqual(result, {"timeout": 30})

        result = MyDictFactory(timeout=SKIP)
        self.assertEqual(result, {})
        self.assertNotIn("timeout", result)

    def test_skip_transformer_default(self):
        """Test SKIP as Transformer default excludes without error."""

        class MyDictFactory(factory.DictFactory):
            timeout = factory.Transformer(SKIP, transform=int)

        result = MyDictFactory()
        self.assertEqual(result, {})
        self.assertNotIn("timeout", result)
