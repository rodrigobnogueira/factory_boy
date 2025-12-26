# Copyright: See the LICENSE file.

import unittest

import factory
from factory import declarations
from factory.fuzzy import FuzzyChoice

from . import utils


class ExcludingTestCase(unittest.TestCase):

    def test_basic_exclusion(self):
        """Test basic exclusion with FuzzyChoice."""
        decl = declarations.Excluding(
            FuzzyChoice(["a", "b", "c", "d"]), exclude=["a", "b"]
        )
        for _ in range(20):
            value = utils.evaluate_declaration(decl)
            self.assertIn(value, ["c", "d"])
            self.assertNotIn(value, ["a", "b"])

    def test_single_exclusion(self):
        """Test excluding a single value."""
        decl = declarations.Excluding(FuzzyChoice(["x", "y", "z"]), exclude="x")
        for _ in range(20):
            value = utils.evaluate_declaration(decl)
            self.assertIn(value, ["y", "z"])

    def test_no_exclusion(self):
        """Test with no exclusions."""
        decl = declarations.Excluding(FuzzyChoice(["a", "b", "c"]), exclude=[])
        value = utils.evaluate_declaration(decl)
        self.assertIn(value, ["a", "b", "c"])

    def test_with_faker(self):
        """Test Excluding works with Faker."""
        excluded_value = "fixed@example.com"
        decl = declarations.Excluding(factory.Faker("email"), exclude=excluded_value)
        for _ in range(10):
            value = utils.evaluate_declaration(decl)
            self.assertNotEqual(value, excluded_value)
            self.assertIn("@", value)

    def test_with_lazy_attribute(self):
        """Test Excluding works with LazyAttribute."""
        import random

        random.seed(42)

        decl = declarations.Excluding(
            declarations.LazyAttribute(lambda x: random.choice(["a", "b", "c", "d"])),
            exclude=["a", "b"],
        )
        for _ in range(20):
            value = utils.evaluate_declaration(decl)
            self.assertIn(value, ["c", "d"])

    def test_exhaustion_error(self):
        """Test that ValueError is raised when all values are excluded."""
        decl = declarations.Excluding(
            FuzzyChoice(["a", "b"]), exclude=["a", "b"], max_retries=10
        )
        with self.assertRaisesRegex(ValueError, r"Could not generate.*10 attempts"):
            utils.evaluate_declaration(decl)

    def test_custom_max_retries(self):
        """Test custom max_retries parameter."""
        decl = declarations.Excluding(FuzzyChoice(["a"]), exclude=["a"], max_retries=5)
        with self.assertRaisesRegex(ValueError, r"5 attempts"):
            utils.evaluate_declaration(decl)

    def test_plain_value_exclusion_error(self):
        """Test that excluding a plain value raises immediately without retrying."""
        decl = declarations.Excluding("fixed_value", exclude="fixed_value")
        with self.assertRaisesRegex(ValueError, r"Plain value.*is excluded"):
            utils.evaluate_declaration(decl)

    def test_with_factory(self):
        """Test Excluding in a full factory context."""

        class MyModel:
            def __init__(self, status, code):
                self.status = status
                self.code = code

        class MyFactory(factory.Factory):
            class Meta:
                model = MyModel

            status = declarations.Excluding(
                FuzzyChoice(["active", "inactive", "pending", "banned"]),
                exclude=["banned"],
            )
            code = declarations.Excluding(factory.Faker("country_code"), exclude="US")

        for _ in range(10):
            obj = MyFactory()
            self.assertIn(obj.status, ["active", "inactive", "pending"])
            self.assertNotEqual(obj.status, "banned")
            self.assertNotEqual(obj.code, "US")

    def test_with_self_attribute(self):
        """Test dynamic exclusion using SelfAttribute."""

        class MyModel:
            def __init__(self, primary, secondary):
                self.primary = primary
                self.secondary = secondary

        class MyFactory(factory.Factory):
            class Meta:
                model = MyModel

            primary = FuzzyChoice(["en", "fr", "de", "es"])
            secondary = declarations.Excluding(
                FuzzyChoice(["en", "fr", "de", "es"]),
                exclude=declarations.SelfAttribute("primary"),
            )

        for _ in range(20):
            obj = MyFactory()
            self.assertIn(obj.primary, ["en", "fr", "de", "es"])
            self.assertIn(obj.secondary, ["en", "fr", "de", "es"])
            self.assertNotEqual(obj.primary, obj.secondary)

    def test_with_self_attribute_list(self):
        """Test dynamic exclusion with multiple values via SelfAttribute."""

        class MyModel:
            def __init__(self, excluded_values, value):
                self.excluded_values = excluded_values
                self.value = value

        class MyFactory(factory.Factory):
            class Meta:
                model = MyModel

            excluded_values = factory.List(
                [
                    factory.LazyFunction(lambda: "a"),
                    factory.LazyFunction(lambda: "b"),
                ]
            )
            value = declarations.Excluding(
                FuzzyChoice(["a", "b", "c", "d"]),
                exclude=declarations.SelfAttribute("excluded_values"),
            )

        obj = MyFactory()
        self.assertIn(obj.value, ["c", "d"])

    def test_override_works(self):
        """Test that factory overrides work correctly with Excluding."""

        class MyModel:
            def __init__(self, status):
                self.status = status

        class MyFactory(factory.Factory):
            class Meta:
                model = MyModel

            status = declarations.Excluding(
                FuzzyChoice(["active", "inactive"]), exclude="inactive"
            )

        obj = MyFactory(status="custom")
        self.assertEqual(obj.status, "custom")

    def test_hashable_values(self):
        """Test that unhashable values (lists, dicts) are properly handled."""
        decl = declarations.Excluding(
            declarations.LazyFunction(lambda: [1, 2, 3]),
            exclude=[[1, 2, 3]],
            max_retries=5,
        )
        with self.assertRaisesRegex(ValueError, r"5 attempts"):
            utils.evaluate_declaration(decl)

    def test_mixed_exclude_types(self):
        """Test excluding with a mix of types."""
        decl = declarations.Excluding(FuzzyChoice([1, 2, 3, 4, 5]), exclude=[1, 2])
        for _ in range(10):
            value = utils.evaluate_declaration(decl)
            self.assertIn(value, [3, 4, 5])


class ExcludingOrderingTestCase(unittest.TestCase):
    """Test that Excluding properly participates in declaration ordering."""

    def test_ordering(self):
        """Ensure Excluding is an OrderedDeclaration."""
        self.assertTrue(
            isinstance(
                declarations.Excluding(FuzzyChoice(["a", "b"])),
                declarations.OrderedDeclaration,
            )
        )
