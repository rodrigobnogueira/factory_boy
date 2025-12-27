# Copyright: See the LICENSE file.

import unittest

import factory
from factory import MISSING


class MissingSentinelTestCase(unittest.TestCase):
    """Tests for the MISSING sentinel object."""

    def test_missing_basic(self):
        """Test basic MISSING exclusion from DictFactory."""

        class MyDictFactory(factory.DictFactory):
            name = "John"
            email = MISSING
            phone = "123-456"

        result = MyDictFactory()
        self.assertEqual(result, {"name": "John", "phone": "123-456"})
        self.assertNotIn("email", result)

    def test_missing_override(self):
        """Test MISSING can be overridden per-instance."""

        class MyDictFactory(factory.DictFactory):
            name = "John"
            email = "default@example.com"

        result = MyDictFactory(email=MISSING)
        self.assertEqual(result, {"name": "John"})
        self.assertNotIn("email", result)

    def test_missing_all(self):
        """Test all fields can be MISSING."""

        class MyDictFactory(factory.DictFactory):
            field1 = MISSING
            field2 = MISSING

        result = MyDictFactory()
        self.assertEqual(result, {})

    def test_missing_with_lazy_function(self):
        """Test MISSING works with declarations."""

        class MyDictFactory(factory.DictFactory):
            name = factory.LazyFunction(lambda: "Generated")
            skipped = MISSING
            value = 42

        result = MyDictFactory()
        self.assertEqual(result["name"], "Generated")
        self.assertEqual(result["value"], 42)
        self.assertNotIn("skipped", result)

    def test_missing_singleton(self):
        """Test MISSING is a singleton."""
        another_missing = factory.MISSING
        self.assertIs(MISSING, another_missing)

    def test_missing_bool(self):
        """Test MISSING is falsy."""
        self.assertFalse(MISSING)
        self.assertFalse(bool(MISSING))

    def test_missing_repr(self):
        """Test MISSING has readable repr."""
        self.assertEqual(repr(MISSING), "<MISSING>")

    def test_missing_with_transformer(self):
        """Test MISSING works with Transformer declarations."""

        class MyDictFactory(factory.DictFactory):
            timeout = factory.Transformer(30.0, transform=int)

        result = MyDictFactory()
        self.assertEqual(result, {"timeout": 30})

        result = MyDictFactory(timeout=MISSING)
        self.assertEqual(result, {})
        self.assertNotIn("timeout", result)

    def test_missing_transformer_default(self):
        """Test MISSING as Transformer default excludes without error."""

        class MyDictFactory(factory.DictFactory):
            timeout = factory.Transformer(MISSING, transform=int)

        result = MyDictFactory()
        self.assertEqual(result, {})
        self.assertNotIn("timeout", result)
