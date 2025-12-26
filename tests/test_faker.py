# Copyright: See the LICENSE file.

import collections
import datetime
import random
import unittest

import faker.providers

import factory


class MockFaker:
    def __init__(self, expected):
        self.expected = expected
        self.random = random.Random()

    def format(self, provider, **kwargs):
        return self.expected[provider]


class AdvancedMockFaker:
    def __init__(self, handlers):
        self.handlers = handlers
        self.random = random.Random()

    def format(self, provider, **kwargs):
        handler = self.handlers[provider]
        return handler(**kwargs)


class FakerTests(unittest.TestCase):
    def setUp(self):
        self._real_fakers = factory.Faker._FAKER_REGISTRY
        factory.Faker._FAKER_REGISTRY = {}

    def tearDown(self):
        factory.Faker._FAKER_REGISTRY = self._real_fakers

    def _setup_mock_faker(self, locale=None, **definitions):
        if locale is None:
            locale = factory.Faker._DEFAULT_LOCALE
        factory.Faker._FAKER_REGISTRY[locale] = MockFaker(definitions)

    def _setup_advanced_mock_faker(self, locale=None, **handlers):
        if locale is None:
            locale = factory.Faker._DEFAULT_LOCALE
        factory.Faker._FAKER_REGISTRY[locale] = AdvancedMockFaker(handlers)

    def test_simple_biased(self):
        self._setup_mock_faker(name="John Doe")
        faker_field = factory.Faker("name")
        self.assertEqual("John Doe", faker_field.evaluate(None, None, {"locale": None}))

    def test_full_factory(self):
        class Profile:
            def __init__(self, first_name, last_name, email):
                self.first_name = first_name
                self.last_name = last_name
                self.email = email

        class ProfileFactory(factory.Factory):
            class Meta:
                model = Profile

            first_name = factory.Faker("first_name")
            last_name = factory.Faker("last_name", locale="fr_FR")
            email = factory.Faker("email")

        self._setup_mock_faker(
            first_name="John", last_name="Doe", email="john.doe@example.org"
        )
        self._setup_mock_faker(
            first_name="Jean",
            last_name="Valjean",
            email="jvaljean@exemple.fr",
            locale="fr_FR",
        )

        profile = ProfileFactory()
        self.assertEqual("John", profile.first_name)
        self.assertEqual("Valjean", profile.last_name)
        self.assertEqual("john.doe@example.org", profile.email)

    def test_override_locale(self):
        class Profile:
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name

        class ProfileFactory(factory.Factory):
            class Meta:
                model = Profile

            first_name = factory.Faker("first_name")
            last_name = factory.Faker("last_name", locale="fr_FR")

        self._setup_mock_faker(first_name="John", last_name="Doe")
        self._setup_mock_faker(first_name="Jean", last_name="Valjean", locale="fr_FR")
        self._setup_mock_faker(
            first_name="Johannes", last_name="Brahms", locale="de_DE"
        )

        profile = ProfileFactory()
        self.assertEqual("John", profile.first_name)
        self.assertEqual("Valjean", profile.last_name)

        with factory.Faker.override_default_locale("de_DE"):
            profile = ProfileFactory()
            self.assertEqual("Johannes", profile.first_name)
            self.assertEqual("Valjean", profile.last_name)

        profile = ProfileFactory()
        self.assertEqual("John", profile.first_name)
        self.assertEqual("Valjean", profile.last_name)

    def test_add_provider(self):
        class Face:
            def __init__(self, smiley, french_smiley):
                self.smiley = smiley
                self.french_smiley = french_smiley

        class FaceFactory(factory.Factory):
            class Meta:
                model = Face

            smiley = factory.Faker("smiley")
            french_smiley = factory.Faker("smiley", locale="fr_FR")

        class SmileyProvider(faker.providers.BaseProvider):
            def smiley(self):
                return ":)"

        class FrenchSmileyProvider(faker.providers.BaseProvider):
            def smiley(self):
                return "(:"

        factory.Faker.add_provider(SmileyProvider)
        factory.Faker.add_provider(FrenchSmileyProvider, "fr_FR")

        face = FaceFactory()
        self.assertEqual(":)", face.smiley)
        self.assertEqual("(:", face.french_smiley)

    def test_faker_customization(self):
        """Factory declarations in Faker parameters should be accepted."""
        Trip = collections.namedtuple("Trip", ["departure", "transfer", "arrival"])

        may_4th = datetime.date(1977, 5, 4)
        may_25th = datetime.date(1977, 5, 25)
        october_19th = datetime.date(1977, 10, 19)

        class TripFactory(factory.Factory):
            class Meta:
                model = Trip

            departure = may_4th
            arrival = may_25th
            transfer = factory.Faker(
                "date_between_dates",
                start_date=factory.SelfAttribute("..departure"),
                end_date=factory.SelfAttribute("..arrival"),
            )

        def fake_select_date(start_date, end_date):
            """Fake date_between_dates."""
            # Ensure that dates have been transferred from the factory
            # to Faker parameters.
            self.assertEqual(start_date, may_4th)
            self.assertEqual(end_date, may_25th)
            return october_19th

        self._setup_advanced_mock_faker(
            date_between_dates=fake_select_date,
        )

        trip = TripFactory()
        self.assertEqual(may_4th, trip.departure)
        self.assertEqual(october_19th, trip.transfer)
        self.assertEqual(may_25th, trip.arrival)


class FakerUniqueTests(unittest.TestCase):
    """Tests for the unique parameter in Faker declarations."""

    def setUp(self):
        self._real_fakers = factory.Faker._FAKER_REGISTRY
        factory.Faker._FAKER_REGISTRY = {}
        try:
            factory.Faker._get_faker().unique.clear()
        except Exception:
            pass

    def tearDown(self):
        factory.Faker._FAKER_REGISTRY = self._real_fakers
        try:
            factory.Faker._get_faker().unique.clear()
        except Exception:
            pass

    def test_unique_faker_generates_unique_values(self):
        """Test that Faker with unique=True generates unique values."""

        class User:
            def __init__(self, email):
                self.email = email

        class UserFactory(factory.Factory):
            class Meta:
                model = User

            email = factory.Faker("email", unique=True)

        emails = {UserFactory().email for _ in range(10)}
        self.assertEqual(len(emails), 10)

    def test_unique_false_allows_duplicates(self):
        """Test that Faker with unique=False (default) can generate duplicates."""
        import random

        random.seed(42)

        class User:
            def __init__(self, value):
                self.value = value

        class UserFactory(factory.Factory):
            class Meta:
                model = User

            value = factory.Faker("random_int", min=1, max=3, unique=False)

        values = [UserFactory().value for _ in range(20)]
        unique_values = set(values)
        self.assertLess(len(unique_values), 20)

    def test_unique_clears_between_factories(self):
        """Test that unique cache can be cleared between test runs."""

        class User:
            def __init__(self, email):
                self.email = email

        class UserFactory(factory.Factory):
            class Meta:
                model = User

            email = factory.Faker("email", unique=True)

        emails_first = {UserFactory().email for _ in range(5)}
        factory.Faker._get_faker().unique.clear()

        emails_second = {UserFactory().email for _ in range(5)}

        self.assertEqual(len(emails_first), 5)
        self.assertEqual(len(emails_second), 5)

    def test_unique_with_locale(self):
        """Test that unique works with custom locales."""

        class User:
            def __init__(self, name):
                self.name = name

        class UserFactory(factory.Factory):
            class Meta:
                model = User

            name = factory.Faker("name", locale="fr_FR", unique=True)

        names = {UserFactory().name for _ in range(5)}
        self.assertEqual(len(names), 5)

    def test_unique_exhaustion_raises_error(self):
        """Test that exhausting unique values raises UniquenessException."""
        import faker.exceptions

        class User:
            def __init__(self, value):
                self.value = value

        class UserFactory(factory.Factory):
            class Meta:
                model = User

            value = factory.Faker("boolean", unique=True)

        UserFactory()
        UserFactory()

        with self.assertRaises(faker.exceptions.UniquenessException):
            UserFactory()
