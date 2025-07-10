import pytest
from uuid import uuid4
from datetime import datetime

from app.modules.master_data.categories.models import Category, CategoryPath


class TestCategoryModel:
    """Tests for Category model."""
    
    def test_category_creation_root(self):
        """Test creating a root category."""
        category = Category(
            name="Electronics",
            category_level=1,
            display_order=1
        )
        
        assert category.name == "Electronics"
        assert category.parent_category_id is None
        assert category.category_path == "Electronics"
        assert category.category_level == 1
        assert category.display_order == 1
        assert category.is_leaf is True
        assert category.is_active is True
        assert category.id is not None
        assert category.created_at is not None
    
    def test_category_creation_child(self):
        """Test creating a child category."""
        parent_id = uuid4()
        category = Category(
            name="Computers",
            parent_category_id=parent_id,
            category_path="Electronics/Computers",
            category_level=2,
            display_order=1
        )
        
        assert category.name == "Computers"
        assert category.parent_category_id == parent_id
        assert category.category_path == "Electronics/Computers"
        assert category.category_level == 2
        assert category.display_order == 1
        assert category.is_leaf is True
    
    def test_category_validation_empty_name(self):
        """Test validation fails for empty name."""
        with pytest.raises(ValueError, match="Category name cannot be empty"):
            Category(name="")
    
    def test_category_validation_long_name(self):
        """Test validation fails for name too long."""
        long_name = "a" * 101
        with pytest.raises(ValueError, match="Category name cannot exceed 100 characters"):
            Category(name=long_name)
    
    def test_category_validation_invalid_level(self):
        """Test validation fails for invalid level."""
        with pytest.raises(ValueError, match="Category level must be at least 1"):
            Category(name="Test", category_level=0)
    
    def test_category_validation_negative_display_order(self):
        """Test validation fails for negative display order."""
        with pytest.raises(ValueError, match="Display order cannot be negative"):
            Category(name="Test", display_order=-1)
    
    def test_category_validation_root_with_parent(self):
        """Test validation fails for root category with parent."""
        with pytest.raises(ValueError, match="Root categories cannot have a parent"):
            Category(
                name="Test",
                parent_category_id=uuid4(),
                category_level=1
            )
    
    def test_category_validation_non_root_without_parent(self):
        """Test validation fails for non-root category without parent."""
        with pytest.raises(ValueError, match="Non-root categories must have a parent"):
            Category(
                name="Test",
                category_level=2
            )
    
    def test_category_validation_empty_path(self):
        """Test validation fails for empty path."""
        with pytest.raises(ValueError, match="Category path cannot be empty"):
            Category(
                name="Test",
                category_path=""
            )
    
    def test_category_validation_long_path(self):
        """Test validation fails for path too long."""
        long_path = "a" * 501
        with pytest.raises(ValueError, match="Category path cannot exceed 500 characters"):
            Category(
                name="Test",
                category_path=long_path
            )
    
    def test_category_update_info(self):
        """Test updating category info."""
        category = Category(name="Original")
        
        category.update_info(
            name="Updated",
            display_order=5,
            updated_by="user123"
        )
        
        assert category.name == "Updated"
        assert category.display_order == 5
        assert category.updated_by == "user123"
    
    def test_category_update_path(self):
        """Test updating category path."""
        category = Category(name="Test")
        
        category.update_path("Electronics/Test", updated_by="user123")
        
        assert category.category_path == "Electronics/Test"
        assert category.updated_by == "user123"
    
    def test_category_mark_as_parent(self):
        """Test marking category as parent."""
        category = Category(name="Test")
        
        category.mark_as_parent(updated_by="user123")
        
        assert category.is_leaf is False
        assert category.updated_by == "user123"
    
    def test_category_mark_as_leaf(self):
        """Test marking category as leaf."""
        category = Category(name="Test", is_leaf=False)
        
        category.mark_as_leaf(updated_by="user123")
        
        assert category.is_leaf is True
        assert category.updated_by == "user123"
    
    def test_category_move_to_parent(self):
        """Test moving category to new parent."""
        category = Category(name="Test")
        new_parent_id = uuid4()
        
        category.move_to_parent(
            new_parent_id=new_parent_id,
            new_level=2,
            new_path="Electronics/Test",
            updated_by="user123"
        )
        
        assert category.parent_category_id == new_parent_id
        assert category.category_level == 2
        assert category.category_path == "Electronics/Test"
        assert category.updated_by == "user123"
    
    def test_category_can_have_items(self):
        """Test can_have_items property."""
        leaf_category = Category(name="Test", is_leaf=True)
        parent_category = Category(name="Test", is_leaf=False)
        
        assert leaf_category.can_have_items() is True
        assert parent_category.can_have_items() is False
    
    def test_category_can_have_children(self):
        """Test can_have_children property."""
        category = Category(name="Test")
        assert category.can_have_children() is True
    
    def test_category_can_delete(self):
        """Test can_delete property."""
        category = Category(name="Test")
        # Mock the properties
        category.child_count = 0
        category.item_count = 0
        category.is_active = True
        
        assert category.can_delete() is True
        
        # With children, cannot delete
        category.child_count = 1
        assert category.can_delete() is False
    
    def test_category_is_root(self):
        """Test is_root property."""
        root_category = Category(name="Test", category_level=1)
        child_category = Category(
            name="Child",
            parent_category_id=uuid4(),
            category_level=2,
            category_path="Test/Child"
        )
        
        assert root_category.is_root() is True
        assert child_category.is_root() is False
    
    def test_category_is_descendant_of(self):
        """Test is_descendant_of method."""
        category = Category(
            name="Laptops",
            category_path="Electronics/Computers/Laptops"
        )
        
        assert category.is_descendant_of("Electronics") is True
        assert category.is_descendant_of("Electronics/Computers") is True
        assert category.is_descendant_of("Other") is False
        assert category.is_descendant_of("") is False
    
    def test_category_is_ancestor_of(self):
        """Test is_ancestor_of method."""
        category = Category(
            name="Electronics",
            category_path="Electronics"
        )
        
        assert category.is_ancestor_of("Electronics/Computers") is True
        assert category.is_ancestor_of("Electronics/Computers/Laptops") is True
        assert category.is_ancestor_of("Other/Path") is False
        assert category.is_ancestor_of("") is False
    
    def test_category_get_path_segments(self):
        """Test get_path_segments method."""
        category = Category(
            name="Laptops",
            category_path="Electronics/Computers/Laptops"
        )
        
        segments = category.get_path_segments()
        assert segments == ["Electronics", "Computers", "Laptops"]
    
    def test_category_get_depth(self):
        """Test get_depth method."""
        category = Category(
            name="Test",
            category_level=3
        )
        
        assert category.get_depth() == 3
    
    def test_category_get_breadcrumb(self):
        """Test get_breadcrumb method."""
        category = Category(
            name="Laptops",
            category_path="Electronics/Computers/Laptops"
        )
        
        breadcrumb = category.get_breadcrumb()
        assert breadcrumb == ["Electronics", "Computers", "Laptops"]
    
    def test_category_get_parent_path(self):
        """Test get_parent_path method."""
        root_category = Category(name="Electronics")
        child_category = Category(
            name="Computers",
            category_path="Electronics/Computers"
        )
        
        assert root_category.get_parent_path() is None
        assert child_category.get_parent_path() == "Electronics"
    
    def test_category_generate_path(self):
        """Test generate_path method."""
        category = Category(name="Computers")
        
        path_with_parent = category.generate_path("Electronics")
        path_without_parent = category.generate_path()
        
        assert path_with_parent == "Electronics/Computers"
        assert path_without_parent == "Computers"
    
    def test_category_full_name_property(self):
        """Test full_name property."""
        category = Category(
            name="Laptops",
            category_path="Electronics/Computers/Laptops"
        )
        
        assert category.full_name == "Electronics/Computers/Laptops"
    
    def test_category_has_children_property(self):
        """Test has_children property."""
        leaf_category = Category(name="Test", is_leaf=True)
        parent_category = Category(name="Test", is_leaf=False)
        
        assert leaf_category.has_children is False
        assert parent_category.has_children is True
    
    def test_category_str_representation(self):
        """Test string representation."""
        category = Category(
            name="Laptops",
            category_path="Electronics/Computers/Laptops"
        )
        
        assert str(category) == "Category(Electronics/Computers/Laptops)"
    
    def test_category_repr_representation(self):
        """Test repr representation."""
        category = Category(
            name="Laptops",
            category_path="Electronics/Computers/Laptops",
            category_level=3
        )
        
        repr_str = repr(category)
        assert "Category(" in repr_str
        assert "name='Laptops'" in repr_str
        assert "path='Electronics/Computers/Laptops'" in repr_str
        assert "level=3" in repr_str
        assert "is_leaf=True" in repr_str
        assert "active=True" in repr_str


class TestCategoryPath:
    """Tests for CategoryPath value object."""
    
    def test_category_path_creation(self):
        """Test creating category path."""
        path = CategoryPath("Electronics/Computers/Laptops")
        assert str(path) == "Electronics/Computers/Laptops"
    
    def test_category_path_strip_slashes(self):
        """Test that leading/trailing slashes are stripped."""
        path = CategoryPath("/Electronics/Computers/Laptops/")
        assert str(path) == "Electronics/Computers/Laptops"
    
    def test_category_path_empty_validation(self):
        """Test validation fails for empty path."""
        with pytest.raises(ValueError, match="Category path cannot be empty"):
            CategoryPath("")
    
    def test_category_path_append(self):
        """Test appending segment to path."""
        path = CategoryPath("Electronics/Computers")
        new_path = path.append("Laptops")
        
        assert str(new_path) == "Electronics/Computers/Laptops"
    
    def test_category_path_append_empty_segment(self):
        """Test appending empty segment fails."""
        path = CategoryPath("Electronics")
        
        with pytest.raises(ValueError, match="Path segment cannot be empty"):
            path.append("")
    
    def test_category_path_parent_path(self):
        """Test getting parent path."""
        path = CategoryPath("Electronics/Computers/Laptops")
        parent = path.parent_path()
        
        assert str(parent) == "Electronics/Computers"
        
        # Root path has no parent
        root_path = CategoryPath("Electronics")
        assert root_path.parent_path() is None
    
    def test_category_path_replace_segment(self):
        """Test replacing segment in path."""
        path = CategoryPath("Electronics/Computers/Laptops")
        new_path = path.replace_segment("Computers", "Tablets")
        
        assert str(new_path) == "Electronics/Tablets/Laptops"
    
    def test_category_path_starts_with(self):
        """Test starts_with method."""
        path = CategoryPath("Electronics/Computers/Laptops")
        
        assert path.starts_with("Electronics") is True
        assert path.starts_with("Electronics/Computers") is True
        assert path.starts_with("Other") is False
        assert path.starts_with("") is False
    
    def test_category_path_get_segments(self):
        """Test get_segments method."""
        path = CategoryPath("Electronics/Computers/Laptops")
        segments = path.get_segments()
        
        assert segments == ["Electronics", "Computers", "Laptops"]
    
    def test_category_path_get_level(self):
        """Test get_level method."""
        path = CategoryPath("Electronics/Computers/Laptops")
        assert path.get_level() == 3
        
        root_path = CategoryPath("Electronics")
        assert root_path.get_level() == 1
    
    def test_category_path_get_last_segment(self):
        """Test get_last_segment method."""
        path = CategoryPath("Electronics/Computers/Laptops")
        assert path.get_last_segment() == "Laptops"
    
    def test_category_path_get_first_segment(self):
        """Test get_first_segment method."""
        path = CategoryPath("Electronics/Computers/Laptops")
        assert path.get_first_segment() == "Electronics"
    
    def test_category_path_is_root(self):
        """Test is_root method."""
        root_path = CategoryPath("Electronics")
        child_path = CategoryPath("Electronics/Computers")
        
        assert root_path.is_root() is True
        assert child_path.is_root() is False
    
    def test_category_path_is_descendant_of(self):
        """Test is_descendant_of method."""
        path = CategoryPath("Electronics/Computers/Laptops")
        ancestor = CategoryPath("Electronics/Computers")
        
        assert path.is_descendant_of(ancestor) is True
        
        non_ancestor = CategoryPath("Other")
        assert path.is_descendant_of(non_ancestor) is False
    
    def test_category_path_is_ancestor_of(self):
        """Test is_ancestor_of method."""
        path = CategoryPath("Electronics/Computers")
        descendant = CategoryPath("Electronics/Computers/Laptops")
        
        assert path.is_ancestor_of(descendant) is True
        
        non_descendant = CategoryPath("Other/Path")
        assert path.is_ancestor_of(non_descendant) is False
    
    def test_category_path_common_ancestor(self):
        """Test common_ancestor method."""
        path1 = CategoryPath("Electronics/Computers/Laptops")
        path2 = CategoryPath("Electronics/Computers/Desktops")
        
        common = path1.common_ancestor(path2)
        assert str(common) == "Electronics/Computers"
        
        # No common ancestor
        path3 = CategoryPath("Home/Furniture")
        common_none = path1.common_ancestor(path3)
        assert common_none is None
    
    def test_category_path_equality(self):
        """Test path equality."""
        path1 = CategoryPath("Electronics/Computers")
        path2 = CategoryPath("Electronics/Computers")
        path3 = CategoryPath("Electronics/Tablets")
        
        assert path1 == path2
        assert path1 != path3
        assert path1 != "Electronics/Computers"  # Different type
    
    def test_category_path_hash(self):
        """Test path hashing."""
        path1 = CategoryPath("Electronics/Computers")
        path2 = CategoryPath("Electronics/Computers")
        
        assert hash(path1) == hash(path2)
        
        # Can be used in sets
        path_set = {path1, path2}
        assert len(path_set) == 1
    
    def test_category_path_comparison(self):
        """Test path comparison for sorting."""
        path1 = CategoryPath("Electronics/Computers")
        path2 = CategoryPath("Electronics/Tablets")
        path3 = CategoryPath("Home/Furniture")
        
        paths = [path3, path2, path1]
        sorted_paths = sorted(paths)
        
        assert sorted_paths[0] == path1
        assert sorted_paths[1] == path2
        assert sorted_paths[2] == path3