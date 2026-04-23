"""Tests for ScalarContent."""

import pytest

from asyoulikeit import ReportContent, ScalarContent


class TestScalarContentBasics:
    def test_is_a_report_content(self):
        assert issubclass(ScalarContent, ReportContent)

    def test_kind(self):
        assert ScalarContent.kind() == "scalar"

    def test_value_only(self):
        sc = ScalarContent("00001900")
        assert sc.value == "00001900"
        assert sc.title is None
        assert sc.description is None

    def test_value_and_title(self):
        sc = ScalarContent("00001900", title="Load")
        assert sc.value == "00001900"
        assert sc.title == "Load"
        assert sc.description is None

    def test_value_and_description(self):
        sc = ScalarContent("00001900", description="An address.")
        assert sc.value == "00001900"
        assert sc.title is None
        assert sc.description == "An address."

    def test_value_title_and_description(self):
        sc = ScalarContent(
            "00001900", title="Load", description="An address."
        )
        assert sc.value == "00001900"
        assert sc.title == "Load"
        assert sc.description == "An address."


class TestScalarContentValueTypes:
    """ScalarContent accepts any Python value."""

    @pytest.mark.parametrize(
        "value",
        [
            "a string",
            "",          # empty string
            42,
            3.14,
            True,
            False,
            None,
            -1,
            0,
        ],
        ids=lambda v: f"value={v!r}",
    )
    def test_roundtrips_primitive_values(self, value):
        sc = ScalarContent(value)
        assert sc.value == value or (sc.value is None and value is None)

    def test_nested_container_value(self):
        """Even containers work — they're just opaque payload."""
        sc = ScalarContent([1, 2, 3])
        assert sc.value == [1, 2, 3]


class TestScalarContentImmutability:
    def test_value_property_not_writable(self):
        sc = ScalarContent("x")
        with pytest.raises(AttributeError):
            sc.value = "y"

    def test_title_property_not_writable(self):
        sc = ScalarContent("x", title="T")
        with pytest.raises(AttributeError):
            sc.title = "new"

    def test_description_property_not_writable(self):
        sc = ScalarContent("x", description="D")
        with pytest.raises(AttributeError):
            sc.description = "new"
