"""Tests for TreeContent and Node."""

import pytest

from asyoulikeit import Importance, Node, ReportContent, TreeContent


# -----------------------------------------------------------------------------
# Construction and schema
# -----------------------------------------------------------------------------

class TestTreeContentBasics:
    def test_is_a_report_content(self):
        assert issubclass(TreeContent, ReportContent)

    def test_kind(self):
        assert TreeContent.kind() == "tree"

    def test_default_metadata_is_none(self):
        tree = TreeContent()
        assert tree.title is None
        assert tree.description is None

    def test_title_and_description(self):
        tree = TreeContent(title="t", description="d")
        assert tree.title == "t"
        assert tree.description == "d"

    def test_columns_empty_initially(self):
        tree = TreeContent()
        assert tree.columns == ()
        assert tree.roots == ()


class TestAddColumn:
    def test_returns_self_for_chaining(self):
        tree = TreeContent()
        assert tree.add_column("name", "Name", header=True) is tree

    def test_columns_maintain_insertion_order(self):
        tree = (
            TreeContent()
            .add_column("name", "Name", header=True)
            .add_column("size", "Size")
            .add_column("kind", "Kind")
        )
        assert [c.key for c in tree.columns] == ["name", "size", "kind"]

    def test_duplicate_column_raises(self):
        tree = TreeContent().add_column("name", "Name", header=True)
        with pytest.raises(ValueError, match="already defined"):
            tree.add_column("name", "Name Again")

    def test_non_identifier_key_raises(self):
        tree = TreeContent()
        with pytest.raises(ValueError, match="valid Python identifier"):
            tree.add_column("my name", "Bad")

    def test_leading_underscore_key_raises(self):
        tree = TreeContent()
        with pytest.raises(ValueError, match="cannot start with underscore"):
            tree.add_column("_private", "Private")

    def test_header_must_be_essential(self):
        tree = TreeContent()
        with pytest.raises(ValueError, match="Header columns must be ESSENTIAL"):
            tree.add_column(
                "name", "Name", header=True, importance=Importance.DETAIL
            )

    def test_cannot_add_column_after_root(self):
        tree = TreeContent().add_column("name", "Name", header=True)
        tree.add_root(name="root")
        with pytest.raises(ValueError, match="after roots"):
            tree.add_column("size", "Size")

    def test_essential_and_detailed_columns_partition(self):
        tree = (
            TreeContent()
            .add_column("name", "Name", header=True)
            .add_column("size", "Size")
            .add_column("note", "Note", importance=Importance.DETAIL)
        )
        assert [c.key for c in tree.essential_columns] == ["name", "size"]
        assert [c.key for c in tree.detailed_columns] == ["note"]


class TestHeaderColumnEnforcement:
    def test_adding_root_without_header_column_raises(self):
        tree = TreeContent().add_column("name", "Name")  # no header=True
        with pytest.raises(ValueError, match="exactly one column marked header"):
            tree.add_root(name="root")

    def test_adding_root_with_two_header_columns_raises(self):
        # TreeContent's `add_column` permits marking multiple columns
        # `header=True` (unlike TableContent, which forbids a second
        # header at column-declaration time). The constraint is
        # enforced lazily at the first `add_root` call instead.
        tree = (
            TreeContent()
            .add_column("first", "First", header=True)
            .add_column("second", "Second", header=True)
        )
        with pytest.raises(
            ValueError, match="exactly one column marked header"
        ):
            tree.add_root(first="a", second="b")

    def test_header_column_property_returns_the_header(self):
        tree = (
            TreeContent()
            .add_column("name", "Name", header=True)
            .add_column("size", "Size")
        )
        hc = tree.header_column
        assert hc is not None
        assert hc.key == "name"

    def test_header_column_property_none_when_missing(self):
        tree = TreeContent().add_column("name", "Name")
        assert tree.header_column is None


class TestAddRoot:
    def test_requires_columns_declared(self):
        tree = TreeContent()
        with pytest.raises(ValueError, match="before adding roots"):
            tree.add_root(name="x")

    def test_missing_value_raises(self):
        tree = (
            TreeContent()
            .add_column("name", "Name", header=True)
            .add_column("size", "Size")
        )
        with pytest.raises(ValueError, match="missing required columns"):
            tree.add_root(name="only-name")

    def test_extra_value_raises(self):
        tree = TreeContent().add_column("name", "Name", header=True)
        with pytest.raises(ValueError, match="unexpected columns"):
            tree.add_root(name="x", extra="no")

    def test_returns_the_new_node(self):
        tree = TreeContent().add_column("name", "Name", header=True)
        root = tree.add_root(name="r")
        assert isinstance(root, Node)
        assert root.values["name"] == "r"

    def test_multiple_roots_permitted(self):
        tree = TreeContent().add_column("name", "Name", header=True)
        r1 = tree.add_root(name="a")
        r2 = tree.add_root(name="b")
        r3 = tree.add_root(name="c")
        assert tree.roots == (r1, r2, r3)
        assert [r.values["name"] for r in tree.roots] == ["a", "b", "c"]

    def test_default_importance_is_essential(self):
        tree = TreeContent().add_column("name", "Name", header=True)
        root = tree.add_root(name="r")
        assert root.importance == Importance.ESSENTIAL

    def test_can_set_root_importance(self):
        tree = TreeContent().add_column("name", "Name", header=True)
        root = tree.add_root(name="r", _importance=Importance.DETAIL)
        assert root.importance == Importance.DETAIL


# -----------------------------------------------------------------------------
# Node and the tree shape
# -----------------------------------------------------------------------------

class TestNodeAddChild:
    def _empty_tree(self):
        return (
            TreeContent()
            .add_column("name", "Name", header=True)
            .add_column("size", "Size")
        )

    def test_returns_new_child(self):
        tree = self._empty_tree()
        root = tree.add_root(name="r", size=0)
        child = root.add_child(name="c", size=1)
        assert isinstance(child, Node)
        assert child is not root
        assert child.values["name"] == "c"

    def test_child_is_appended_to_children(self):
        tree = self._empty_tree()
        root = tree.add_root(name="r", size=0)
        c1 = root.add_child(name="a", size=1)
        c2 = root.add_child(name="b", size=2)
        assert root.children == (c1, c2)

    def test_deep_chaining_via_returned_child(self):
        tree = self._empty_tree()
        root = tree.add_root(name="r", size=0)
        inner = root.add_child(name="inner", size=1)
        leaf = inner.add_child(name="leaf", size=2)
        assert leaf in inner.children
        assert inner in root.children
        assert leaf not in root.children

    def test_sibling_addition_via_shared_parent(self):
        tree = self._empty_tree()
        root = tree.add_root(name="r", size=0)
        bin_dir = root.add_child(name="bin", size=0)
        ls = bin_dir.add_child(name="ls", size=100)
        cat = bin_dir.add_child(name="cat", size=50)
        assert bin_dir.children == (ls, cat)

    def test_child_schema_validation(self):
        tree = self._empty_tree()
        root = tree.add_root(name="r", size=0)
        with pytest.raises(ValueError, match="missing required columns"):
            root.add_child(name="only-name")
        with pytest.raises(ValueError, match="unexpected columns"):
            root.add_child(name="c", size=1, extra="no")


class TestNodeImmutableViews:
    def _populated_tree(self):
        tree = TreeContent().add_column("name", "Name", header=True)
        root = tree.add_root(name="r")
        root.add_child(name="c")
        return tree, root

    def test_values_view_is_mapping_proxy(self):
        tree, root = self._populated_tree()
        values = root.values
        with pytest.raises(TypeError):
            values["name"] = "mutated"  # MappingProxy is read-only

    def test_children_is_tuple(self):
        tree, root = self._populated_tree()
        assert isinstance(root.children, tuple)

    def test_roots_is_tuple(self):
        tree, _ = self._populated_tree()
        assert isinstance(tree.roots, tuple)


class TestChildImportance:
    def test_child_default_importance_is_essential(self):
        tree = TreeContent().add_column("name", "Name", header=True)
        root = tree.add_root(name="r")
        child = root.add_child(name="c")
        assert child.importance == Importance.ESSENTIAL

    def test_child_detail_importance(self):
        tree = TreeContent().add_column("name", "Name", header=True)
        root = tree.add_root(name="r")
        child = root.add_child(name="c", _importance=Importance.DETAIL)
        assert child.importance == Importance.DETAIL


# -----------------------------------------------------------------------------
# End-to-end smoke: a real-ish filesystem example
# -----------------------------------------------------------------------------

class TestRealisticTree:
    def test_filesystem_shape(self):
        tree = (
            TreeContent(title="/usr", description="a tiny subtree")
            .add_column("name", "Name", header=True)
            .add_column("size", "Size")
            .add_column("kind", "Kind", importance=Importance.DETAIL)
        )
        usr = tree.add_root(name="/usr", size=0, kind="dir")
        bin_dir = usr.add_child(name="bin", size=4096, kind="dir")
        bin_dir.add_child(name="ls", size=150_296, kind="exec")
        bin_dir.add_child(name="cat", size=52_024, kind="exec")
        lib_dir = usr.add_child(name="lib", size=8192, kind="dir")
        lib_dir.add_child(name="libc.so", size=2_000_000, kind="lib")

        assert tree.title == "/usr"
        assert tree.description == "a tiny subtree"
        assert [c.key for c in tree.columns] == ["name", "size", "kind"]
        assert [c.key for c in tree.essential_columns] == ["name", "size"]
        assert [c.key for c in tree.detailed_columns] == ["kind"]
        assert len(tree.roots) == 1
        (root,) = tree.roots
        assert root.values["name"] == "/usr"
        assert [c.values["name"] for c in root.children] == ["bin", "lib"]
        (bin_node, lib_node) = root.children
        assert [c.values["name"] for c in bin_node.children] == ["ls", "cat"]
        assert [c.values["name"] for c in lib_node.children] == ["libc.so"]
