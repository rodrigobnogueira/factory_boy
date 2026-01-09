# Copyright: See the LICENSE file.


"""Additional declarations for "fuzzy" attribute definitions."""


import datetime
import decimal
import string
import warnings

from . import declarations, random

random_seed_warning = (
    "Setting a specific random seed for {} can still have varying results "
    "unless you also set a specific end date. For details and potential solutions "
    "see https://github.com/FactoryBoy/factory_boy/issues/331"
)


class BaseFuzzyAttribute(declarations.BaseDeclaration):
    """Base class for fuzzy attributes.

    Custom fuzzers should override the `fuzz()` method.
    """

    def _resolve(self, value, instance, step):
        if isinstance(value, declarations.BaseDeclaration):
            return value.evaluate_pre(instance=instance, step=step, overrides={})
        return value

    def fuzz(self, instance, step):
        raise NotImplementedError()

    def evaluate(self, instance, step, extra):
        return self.fuzz(instance, step)


class FuzzyAttribute(BaseFuzzyAttribute):
    """Similar to LazyAttribute, but yields random values.

    Attributes:
        function (callable): function taking no parameters and returning a
            random value.
    """

    def __init__(self, fuzzer):
        super().__init__()
        self.fuzzer = fuzzer

    def fuzz(self, instance, step):
        return self.fuzzer()


class FuzzyText(BaseFuzzyAttribute):
    """Random string with a given prefix.

    Generates a random string of the given length from chosen chars.
    If a prefix or a suffix are supplied, they will be prepended / appended
    to the generated string.

    Args:
        prefix (text): An optional prefix to prepend to the random string
        length (int): the length of the random part
        suffix (text): An optional suffix to append to the random string
        chars (str list): the chars to choose from

    Useful for generating unique attributes where the exact value is
    not important.
    """

    def __init__(self, prefix='', length=12, suffix='', chars=string.ascii_letters):
        super().__init__()
        self.prefix = prefix
        self.suffix = suffix
        self.length = length
        self.chars = tuple(chars)  # Unroll iterators

    def fuzz(self, instance, step):
        chars = [random.randgen.choice(self.chars) for _i in range(self.length)]
        return self.prefix + ''.join(chars) + self.suffix


class FuzzyChoice(BaseFuzzyAttribute):
    """Handles fuzzy choice of an attribute.

    Args:
        choices (iterable): An iterable yielding options; will only be unrolled
            on the first call.
        getter (callable or None): a function to parse returned values
    """

    def __init__(self, choices, getter=None):
        self.choices = None
        self.choices_generator = choices
        self.getter = getter
        super().__init__()

    def fuzz(self, instance, step):
        if self.choices is None:
            resolved = self._resolve(self.choices_generator, instance, step)
            self.choices = list(resolved)
        value = random.randgen.choice(self.choices)
        if self.getter is None:
            return value
        return self.getter(value)


class FuzzyInteger(BaseFuzzyAttribute):
    """Random integer within a given range."""

    def __init__(self, low, high=None, step=1):
        self.low = low
        self.high = high
        self.step = step
        super().__init__()

    def fuzz(self, instance, step):
        low = self._resolve(self.low, instance, step)
        high = self._resolve(self.high, instance, step)
        if high is None:
            high = low
            low = 0
        return random.randgen.randrange(low, high + 1, self.step)


class FuzzyDecimal(BaseFuzzyAttribute):
    """Random decimal within a given range."""

    def __init__(self, low, high=None, precision=2):
        self.low = low
        self.high = high
        self.precision = precision
        super().__init__()

    def fuzz(self, instance, step):
        low = self._resolve(self.low, instance, step)
        high = self._resolve(self.high, instance, step)
        if high is None:
            high = low
            low = 0.0
        base = decimal.Decimal(str(random.randgen.uniform(low, high)))
        return base.quantize(decimal.Decimal(10) ** -self.precision)


class FuzzyFloat(BaseFuzzyAttribute):
    """Random float within a given range."""

    def __init__(self, low, high=None, precision=15):
        self.low = low
        self.high = high
        self.precision = precision
        super().__init__()

    def fuzz(self, instance, step):
        low = self._resolve(self.low, instance, step)
        high = self._resolve(self.high, instance, step)
        if high is None:
            high = low
            low = 0
        base = random.randgen.uniform(low, high)
        return float(format(base, '.%dg' % self.precision))


class FuzzyDate(BaseFuzzyAttribute):
    """Random date within a given date range."""

    def __init__(self, start_date, end_date=None):
        super().__init__()
        self._start_is_decl = isinstance(start_date, declarations.BaseDeclaration)
        self._end_is_decl = isinstance(end_date, declarations.BaseDeclaration)
        self.start_date = start_date
        self.end_date = end_date
        if not self._start_is_decl and not self._end_is_decl:
            if end_date is None:
                if random.randgen.state_set:
                    cls_name = self.__class__.__name__
                    warnings.warn(random_seed_warning.format(cls_name), stacklevel=2)
                end_date = datetime.date.today()
                self.end_date = end_date
            if start_date > end_date:
                raise ValueError(
                    "FuzzyDate boundaries should have start <= end; got %r > %r."
                    % (start_date, end_date))
            self._start_ord = start_date.toordinal()
            self._end_ord = end_date.toordinal()

    def fuzz(self, instance, step):
        if self._start_is_decl or self._end_is_decl:
            start_date = self._resolve(self.start_date, instance, step)
            end_date = self._resolve(self.end_date, instance, step)
            if end_date is None:
                end_date = datetime.date.today()
            if start_date > end_date:
                raise ValueError(
                    "FuzzyDate boundaries should have start <= end; got %r > %r."
                    % (start_date, end_date))
            start_ord = start_date.toordinal()
            end_ord = end_date.toordinal()
        else:
            start_ord = self._start_ord
            end_ord = self._end_ord
        return datetime.date.fromordinal(random.randgen.randint(start_ord, end_ord))


class BaseFuzzyDateTime(BaseFuzzyAttribute):
    """Base class for fuzzy datetime-related attributes.

    Provides fuzz() computation, forcing year/month/day/hour/...
    """

    def _check_bounds(self, start_dt, end_dt):
        if start_dt > end_dt:
            raise ValueError(
                """%s boundaries should have start <= end, got %r > %r""" % (
                    self.__class__.__name__, start_dt, end_dt))

    def _now(self):
        raise NotImplementedError()

    def __init__(self, start_dt, end_dt=None,
                 force_year=None, force_month=None, force_day=None,
                 force_hour=None, force_minute=None, force_second=None,
                 force_microsecond=None):
        super().__init__()
        self._start_is_decl = isinstance(start_dt, declarations.BaseDeclaration)
        self._end_is_decl = isinstance(end_dt, declarations.BaseDeclaration)
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.force_year = force_year
        self.force_month = force_month
        self.force_day = force_day
        self.force_hour = force_hour
        self.force_minute = force_minute
        self.force_second = force_second
        self.force_microsecond = force_microsecond
        if not self._start_is_decl and not self._end_is_decl:
            if end_dt is None:
                if random.randgen.state_set:
                    cls_name = self.__class__.__name__
                    warnings.warn(random_seed_warning.format(cls_name), stacklevel=2)
                end_dt = self._now()
                self.end_dt = end_dt
            self._check_bounds(start_dt, end_dt)

    def fuzz(self, instance, step):
        if self._start_is_decl or self._end_is_decl:
            start_dt = self._resolve(self.start_dt, instance, step)
            end_dt = self._resolve(self.end_dt, instance, step)
            if end_dt is None:
                end_dt = self._now()
            self._check_bounds(start_dt, end_dt)
        else:
            start_dt = self.start_dt
            end_dt = self.end_dt

        delta = end_dt - start_dt
        microseconds = delta.microseconds + 1000000 * (delta.seconds + (delta.days * 86400))

        offset = random.randgen.randint(0, microseconds)
        result = start_dt + datetime.timedelta(microseconds=offset)

        if self.force_year is not None:
            result = result.replace(year=self.force_year)
        if self.force_month is not None:
            result = result.replace(month=self.force_month)
        if self.force_day is not None:
            result = result.replace(day=self.force_day)
        if self.force_hour is not None:
            result = result.replace(hour=self.force_hour)
        if self.force_minute is not None:
            result = result.replace(minute=self.force_minute)
        if self.force_second is not None:
            result = result.replace(second=self.force_second)
        if self.force_microsecond is not None:
            result = result.replace(microsecond=self.force_microsecond)

        return result


class FuzzyNaiveDateTime(BaseFuzzyDateTime):
    """Random naive datetime within a given range.

    If no upper bound is given, will default to datetime.datetime.now().
    """

    def _now(self):
        return datetime.datetime.now()

    def _check_bounds(self, start_dt, end_dt):
        if start_dt.tzinfo is not None:
            raise ValueError(
                "FuzzyNaiveDateTime only handles naive datetimes, got start=%r"
                % start_dt)
        if end_dt.tzinfo is not None:
            raise ValueError(
                "FuzzyNaiveDateTime only handles naive datetimes, got end=%r"
                % end_dt)
        super()._check_bounds(start_dt, end_dt)


class FuzzyDateTime(BaseFuzzyDateTime):
    """Random timezone-aware datetime within a given range.

    If no upper bound is given, will default to datetime.datetime.now()
    If no timezone is given, will default to utc.
    """

    def _now(self):
        return datetime.datetime.now(tz=datetime.timezone.utc)

    def _check_bounds(self, start_dt, end_dt):
        if start_dt.tzinfo is None:
            raise ValueError(
                "FuzzyDateTime requires timezone-aware datetimes, got start=%r"
                % start_dt)
        if end_dt.tzinfo is None:
            raise ValueError(
                "FuzzyDateTime requires timezone-aware datetimes, got end=%r"
                % end_dt)
        super()._check_bounds(start_dt, end_dt)
