"""Tests for TableContent class."""

import pytest

from asyoulikeit.tabular_data import TableContent, Column, Importance


class TestColumn:
    """Tests for Column dataclass."""

    def test_column_frozen(self):
        """Columns should be immutable."""
        column = Column(key="name", label="Name")
        with pytest.raises(AttributeError):
            column.key = "different"


class TestTableContentConstruction:
    """Tests for TableContent construction and basic operations."""

    def test_add_column_returns_self(self):
        """add_column should return self for method chaining."""
        data = TableContent()
        result = data.add_column("name", "Name")
        assert result is data

    def test_columns_are_immutable_tuple(self):
        """columns property should return immutable tuple."""
        data = TableContent().add_column("name", "Name")
        assert isinstance(data.columns, tuple)

    def test_cannot_add_duplicate_column(self):
        """Should raise error when adding duplicate column key."""
        data = TableContent().add_column("name", "Name")
        with pytest.raises(ValueError, match="Column 'name' already defined"):
            data.add_column("name", "Name Again")

    def test_cannot_add_columns_after_rows(self):
        """Should raise error when adding columns after rows have been added."""
        data = TableContent()
        data.add_column("name", "Name")
        data.add_row(name="Alice")

        with pytest.raises(ValueError, match="Cannot add columns after rows"):
            data.add_column("age", "Age")

    def test_column_key_must_be_valid_identifier(self):
        """Column keys must be valid Python identifiers."""
        data = TableContent()

        # Should reject keys with spaces
        with pytest.raises(ValueError, match="must be a valid Python identifier"):
            data.add_column("my key", "My Key")

        # Should reject keys with hyphens
        with pytest.raises(ValueError, match="must be a valid Python identifier"):
            data.add_column("my-key", "My Key")

        # Should reject keys starting with numbers
        with pytest.raises(ValueError, match="must be a valid Python identifier"):
            data.add_column("1st", "First")

        # Should reject keys starting with underscore (reserved for internal use)
        with pytest.raises(ValueError, match="cannot start with underscore"):
            data.add_column("_private", "Private")

        # Should accept valid identifiers
        data.add_column("my_key", "My Key")  # Should not raise
        data.add_column("CamelCase", "Camel Case")  # Should not raise


class TestTableContentRows:
    """Tests for adding rows to TableContent."""

    def test_cannot_add_row_before_columns(self):
        """Should raise error when adding rows before defining columns."""
        data = TableContent()
        with pytest.raises(ValueError, match="Must define columns before adding rows"):
            data.add_row(name="Alice")

    def test_missing_column_raises_error(self):
        """Should raise error when row is missing required columns."""
        data = TableContent()
        data.add_column("name", "Name")
        data.add_column("age", "Age")

        with pytest.raises(ValueError, match="Row missing required columns: \\['age'\\]"):
            data.add_row(name="Alice")

    def test_extra_column_raises_error(self):
        """User requirement: extra keys must be an error, not ignored."""
        data = TableContent()
        data.add_column("name", "Name")

        with pytest.raises(ValueError, match="Row contains unexpected columns: \\['age'\\]"):
            data.add_row(name="Alice", age=30)

    def test_multiple_extra_columns_raises_error(self):
        """Should raise error listing all unexpected columns."""
        data = TableContent()
        data.add_column("name", "Name")

        with pytest.raises(ValueError, match="Row contains unexpected columns: \\['age', 'city'\\]"):
            data.add_row(name="Alice", age=30, city="NYC")

    def test_add_row_with_exact_columns(self):
        """Should successfully add row with exact column match."""
        data = TableContent()
        data.add_column("name", "Name")
        data.add_column("age", "Age")
        data.add_row(name="Alice", age=30)

        assert len(data.rows) == 1
        assert data.rows[0] == {"name": "Alice", "age": 30}

    def test_add_row_returns_self(self):
        """add_row should return self for method chaining."""
        data = TableContent()
        data.add_column("name", "Name")
        result = data.add_row(name="Alice")
        assert result is data

    def test_rows_are_immutable_tuple(self):
        """rows property should return immutable tuple."""
        data = TableContent()
        data.add_column("name", "Name")
        data.add_row(name="Alice")
        assert isinstance(data.rows, tuple)


class TestTableContentMethodChaining:
    """Tests for method chaining fluent API."""

    def test_fluent_api_column_chaining(self):
        """Should be able to chain multiple add_column calls."""
        data = (
            TableContent()
            .add_column("name", "Name")
            .add_column("age", "Age")
            .add_column("city", "City")
        )

        assert len(data.columns) == 3

    def test_fluent_api_row_chaining(self):
        """Should be able to chain multiple add_row calls."""
        data = (
            TableContent()
            .add_column("name", "Name")
            .add_column("age", "Age")
            .add_row(name="Alice", age=30)
            .add_row(name="Bob", age=25)
            .add_row(name="Charlie", age=35)
        )

        assert len(data.rows) == 3

    def test_fluent_api_full_workflow(self):
        """Should be able to chain entire workflow."""
        data = (
            TableContent()
            .add_column("name", "Name")
            .add_column("age", "Age")
            .add_row(name="Alice", age=30)
            .add_row(name="Bob", age=25)
        )

        assert len(data.columns) == 2
        assert len(data.rows) == 2
        assert data.rows[0]["name"] == "Alice"
        assert data.rows[1]["name"] == "Bob"


class TestTableContentColumnOrdering:
    """Tests for column ordering behavior."""

    def test_columns_maintain_insertion_order(self):
        """Columns should maintain the order they were added."""
        data = TableContent()
        data.add_column("first", "First")
        data.add_column("second", "Second")
        data.add_column("third", "Third")

        keys = [col.key for col in data.columns]
        assert keys == ["first", "second", "third"]

    def test_row_values_follow_column_order(self):
        """Row dictionary iteration should follow column definition order."""
        data = TableContent()
        data.add_column("name", "Name")
        data.add_column("age", "Age")
        data.add_column("city", "City")
        data.add_row(city="NYC", name="Alice", age=30)  # Intentionally wrong order

        # Access via columns to verify order is preserved
        row = data.rows[0]
        values = [row[col.key] for col in data.columns]
        assert values == ["Alice", 30, "NYC"]


class TestTableContentMetadata:
    """Tests for table metadata (title and description)."""

    def test_default_metadata_is_none(self):
        """Title and description should default to None."""
        data = TableContent()
        assert data.title is None
        assert data.description is None

    def test_default_present_transposed_is_false(self):
        """present_transposed should default to False."""
        data = TableContent()
        assert data.present_transposed is False

    def test_title_only(self):
        """Can set title without description."""
        data = TableContent(title="My Table")
        assert data.title == "My Table"
        assert data.description is None

    def test_description_only(self):
        """Can set description without title."""
        data = TableContent(description="This is a table of users")
        assert data.title is None
        assert data.description == "This is a table of users"

    def test_title_and_description(self):
        """Can set both title and description."""
        data = TableContent(
            title="User Report",
            description="Active users in the system"
        )
        assert data.title == "User Report"
        assert data.description == "Active users in the system"

    def test_metadata_persists_after_adding_columns_and_rows(self):
        """Metadata should remain accessible after building table."""
        data = TableContent(
            title="Test Table",
            description="Test description"
        )
        data.add_column("name", "Name")
        data.add_row(name="Alice")

        assert data.title == "Test Table"
        assert data.description == "Test description"

    def test_can_set_present_transposed(self):
        """Can set present_transposed flag on construction."""
        data = TableContent(present_transposed=True)
        assert data.present_transposed is True

    def test_can_set_all_metadata_together(self):
        """Can set title, description, and present_transposed together."""
        data = TableContent(
            title="Test Table",
            description="Test description",
            present_transposed=True
        )
        assert data.title == "Test Table"
        assert data.description == "Test description"
        assert data.present_transposed is True


class TestTableContentHeaderColumn:
    """Tests for header column functionality (row labels)."""

    def test_header_column_defaults_to_false(self):
        """Column header flag should default to False."""
        data = TableContent()
        data.add_column("name", "Name")

        assert data.columns[0].header is False

    def test_can_mark_first_column_as_header(self):
        """Should be able to mark the first column as a header column."""
        data = TableContent()
        data.add_column("label", "Label", header=True)
        data.add_column("value", "Value")

        assert data.columns[0].header is True
        assert data.columns[1].header is False

    def test_cannot_mark_second_column_as_header(self):
        """Should raise error when trying to mark non-first column as header."""
        data = TableContent()
        data.add_column("first", "First")

        with pytest.raises(ValueError, match="Header column must be the first column"):
            data.add_column("second", "Second", header=True)

    def test_cannot_mark_third_column_as_header(self):
        """Should raise error when trying to mark third column as header."""
        data = TableContent()
        data.add_column("first", "First")
        data.add_column("second", "Second")

        with pytest.raises(ValueError, match="Header column must be the first column"):
            data.add_column("third", "Third", header=True)

    def test_header_column_property_returns_header_column(self):
        """header_column property should return the header column if one exists."""
        data = TableContent()
        data.add_column("label", "Label", header=True)
        data.add_column("value", "Value")

        header_col = data.header_column
        assert header_col is not None
        assert header_col.key == "label"
        assert header_col.label == "Label"
        assert header_col.header is True

    def test_header_column_property_returns_none_when_no_header(self):
        """header_column property should return None when no header column exists."""
        data = TableContent()
        data.add_column("name", "Name")
        data.add_column("age", "Age")

        assert data.header_column is None

    def test_header_column_works_with_rows(self):
        """Header column should work normally when adding rows."""
        data = TableContent()
        data.add_column("category", "Category", header=True)
        data.add_column("count", "Count")
        data.add_row(category="Apples", count=10)
        data.add_row(category="Oranges", count=15)

        assert len(data.rows) == 2
        assert data.header_column.key == "category"


class TestColumnImportance:
    """Tests for column importance feature."""

    def test_column_importance_defaults_to_essential(self):
        """Columns should default to ESSENTIAL importance."""
        data = TableContent()
        data.add_column("name", "Name")

        assert data.columns[0].importance == Importance.ESSENTIAL

    def test_can_mark_column_as_detail(self):
        """Should be able to mark a column as DETAIL."""
        data = TableContent()
        data.add_column("name", "Name", importance=Importance.ESSENTIAL)
        data.add_column("notes", "Notes", importance=Importance.DETAIL)

        assert data.columns[0].importance == Importance.ESSENTIAL
        assert data.columns[1].importance == Importance.DETAIL

    def test_header_column_cannot_be_detail(self):
        """Header columns must be ESSENTIAL."""
        data = TableContent()

        with pytest.raises(ValueError, match="Header columns must be ESSENTIAL"):
            data.add_column("label", "Label", header=True, importance=Importance.DETAIL)

    def test_essential_columns_property(self):
        """essential_columns should return only ESSENTIAL columns."""
        data = TableContent()
        data.add_column("name", "Name", importance=Importance.ESSENTIAL)
        data.add_column("age", "Age", importance=Importance.ESSENTIAL)
        data.add_column("notes", "Notes", importance=Importance.DETAIL)
        data.add_column("city", "City", importance=Importance.DETAIL)

        essential = data.essential_columns
        assert len(essential) == 2
        assert essential[0].key == "name"
        assert essential[1].key == "age"

    def test_detailed_columns_property(self):
        """detailed_columns should return only DETAIL columns."""
        data = TableContent()
        data.add_column("name", "Name", importance=Importance.ESSENTIAL)
        data.add_column("age", "Age", importance=Importance.ESSENTIAL)
        data.add_column("notes", "Notes", importance=Importance.DETAIL)
        data.add_column("bio", "Bio", importance=Importance.DETAIL)

        detailed = data.detailed_columns
        assert len(detailed) == 2
        assert detailed[0].key == "notes"
        assert detailed[1].key == "bio"

    def test_essential_columns_empty_when_none_exist(self):
        """essential_columns should return empty tuple when no ESSENTIAL columns exist."""
        data = TableContent()
        data.add_column("notes", "Notes", importance=Importance.DETAIL)
        data.add_column("bio", "Bio", importance=Importance.DETAIL)

        assert len(data.essential_columns) == 0
        assert isinstance(data.essential_columns, tuple)

    def test_detailed_columns_empty_when_none_exist(self):
        """detailed_columns should return empty tuple when no DETAIL columns exist."""
        data = TableContent()
        data.add_column("name", "Name", importance=Importance.ESSENTIAL)
        data.add_column("age", "Age", importance=Importance.ESSENTIAL)

        assert len(data.detailed_columns) == 0
        assert isinstance(data.detailed_columns, tuple)

    def test_columns_maintain_order_regardless_of_importance(self):
        """Columns should maintain insertion order regardless of importance."""
        data = TableContent()
        data.add_column("first", "First", importance=Importance.DETAIL)
        data.add_column("second", "Second", importance=Importance.ESSENTIAL)
        data.add_column("third", "Third", importance=Importance.DETAIL)
        data.add_column("fourth", "Fourth", importance=Importance.ESSENTIAL)

        keys = [col.key for col in data.columns]
        assert keys == ["first", "second", "third", "fourth"]

    def test_importance_works_with_rows(self):
        """Column importance should work normally when adding rows."""
        data = TableContent()
        data.add_column("name", "Name", importance=Importance.ESSENTIAL)
        data.add_column("notes", "Notes", importance=Importance.DETAIL)
        data.add_row(name="Alice", notes="Test note")

        assert len(data.rows) == 1
        assert data.rows[0] == {"name": "Alice", "notes": "Test note"}


class TestTransposeWithImportance:
    """Tests for transpose() with column importance."""

    def test_transpose_defaults_value_columns_to_essential(self):
        """Transposed value columns should default to ESSENTIAL."""
        data = TableContent()
        data.add_column("label", "Label", header=True)
        data.add_column("value", "Value")
        data.add_row(label="Row1", value=10)
        data.add_row(label="Row2", value=20)

        transposed = data.transpose()

        # First column (field names) is always ESSENTIAL header
        assert transposed.columns[0].importance == Importance.ESSENTIAL
        assert transposed.columns[0].header is True

        # Value columns default to ESSENTIAL
        assert transposed.columns[1].importance == Importance.ESSENTIAL
        assert transposed.columns[2].importance == Importance.ESSENTIAL

    def test_transpose_can_set_value_columns_to_detail(self):
        """Should be able to set value columns as DETAIL in transpose."""
        data = TableContent()
        data.add_column("label", "Label", header=True)
        data.add_column("value", "Value")
        data.add_row(label="Row1", value=10)
        data.add_row(label="Row2", value=20)

        transposed = data.transpose(value_column_importance=Importance.DETAIL)

        # First column (field names) is always ESSENTIAL header
        assert transposed.columns[0].importance == Importance.ESSENTIAL
        assert transposed.columns[0].header is True

        # Value columns are DETAIL as specified
        assert transposed.columns[1].importance == Importance.DETAIL
        assert transposed.columns[2].importance == Importance.DETAIL

    def test_transpose_preserves_data_regardless_of_importance(self):
        """Transpose should preserve data structure regardless of importance settings."""
        data = TableContent()
        data.add_column("category", "Category", header=True)
        data.add_column("count", "Count")
        data.add_row(category="Apples", count=10)
        data.add_row(category="Oranges", count=15)

        # Transpose with DETAIL importance
        transposed = data.transpose(value_column_importance=Importance.DETAIL)

        # Verify structure
        assert len(transposed.columns) == 3  # label + 2 value columns
        assert len(transposed.rows) == 1  # 1 data column from original

        # Verify data
        assert transposed.rows[0]["label"] == "Count"
        assert transposed.rows[0]["row_0"] == 10
        assert transposed.rows[0]["row_1"] == 15

    def test_transpose_original_column_importance_not_preserved(self):
        """Original column importance is not preserved through transpose."""
        data = TableContent()
        data.add_column("label", "Label", header=True, importance=Importance.ESSENTIAL)
        data.add_column("essential_col", "Essential", importance=Importance.ESSENTIAL)
        data.add_column("detail_col", "Detail", importance=Importance.DETAIL)
        data.add_row(label="Row1", essential_col=10, detail_col="note1")
        data.add_row(label="Row2", essential_col=20, detail_col="note2")

        # Transpose with ESSENTIAL importance
        transposed = data.transpose(value_column_importance=Importance.ESSENTIAL)

        # All value columns are ESSENTIAL (original importance is not preserved)
        for col in transposed.columns[1:]:  # Skip first (header) column
            assert col.importance == Importance.ESSENTIAL

        # Verify both original ESSENTIAL and DETAIL columns became rows
        assert len(transposed.rows) == 2
        row_labels = [row["label"] for row in transposed.rows]
        assert "Essential" in row_labels
        assert "Detail" in row_labels
