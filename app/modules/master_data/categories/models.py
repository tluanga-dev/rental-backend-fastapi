from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
from uuid import UUID

from app.db.base import BaseModel, UUIDType

if TYPE_CHECKING:
    from app.modules.inventory.models import Item


class Category(BaseModel):
    """
    Category model with hierarchical support.
    
    Attributes:
        name: Category name
        parent_category_id: UUID of parent category (None for root categories)
        category_path: Full path like "Electronics/Computers/Laptops"
        category_level: Hierarchy level (1=root, 2=sub, etc.)
        display_order: Sort order within parent
        is_leaf: True if category has no children
        parent: Parent category relationship
        children: Child categories relationship
        items: Items in this category
    """
    
    __tablename__ = "categories"
    
    name = Column(String(100), nullable=False, comment="Category name")
    parent_category_id = Column(UUIDType(), ForeignKey("categories.id"), nullable=True, comment="Parent category ID")
    category_path = Column(String(500), nullable=False, index=True, comment="Full category path")
    category_level = Column(Integer, nullable=False, default=1, comment="Hierarchy level")
    display_order = Column(Integer, nullable=False, default=0, comment="Display order within parent")
    is_leaf = Column(Boolean, nullable=False, default=True, comment="True if category has no children")
    
    # Self-referential relationship - temporarily disabled to prevent async issues
    # parent = relationship("Category", remote_side="Category.id", back_populates="children")
    # children = relationship("Category", back_populates="parent", cascade="all, delete-orphan")
    
    # Items in this category
    # items = relationship("Item", back_populates="category", lazy="select")  # Temporarily disabled
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_category_parent', 'parent_category_id'),
        Index('idx_category_path', 'category_path'),
        Index('idx_category_active_leaf', 'is_active', 'is_leaf'),
        Index('idx_category_level', 'category_level'),
        Index('idx_category_display_order', 'display_order'),
        Index('idx_category_parent_order', 'parent_category_id', 'display_order'),
        # Unique constraint: category name must be unique within parent
        Index('uk_category_name_parent', 'name', 'parent_category_id', unique=True),
    )
    
    def __init__(
        self,
        name: str,
        parent_category_id: Optional[UUID] = None,
        category_path: Optional[str] = None,
        category_level: int = 1,
        display_order: int = 0,
        is_leaf: bool = True,
        **kwargs
    ):
        """
        Initialize a Category.
        
        Args:
            name: Category name
            parent_category_id: UUID of parent category (None for root categories)
            category_path: Full path like "Electronics/Computers/Laptops"
            category_level: Hierarchy level (1=root, 2=sub, etc.)
            display_order: Sort order within parent
            is_leaf: True if category has no children
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.name = name
        self.parent_category_id = parent_category_id
        self.category_path = category_path or name
        self.category_level = category_level
        self.display_order = display_order
        self.is_leaf = is_leaf
        self._validate()
    
    def _validate(self):
        """Validate category business rules."""
        # Name validation
        if not self.name or not self.name.strip():
            raise ValueError("Category name cannot be empty")
        
        if len(self.name) > 100:
            raise ValueError("Category name cannot exceed 100 characters")
        
        # Level validation
        if self.category_level < 1:
            raise ValueError("Category level must be at least 1")
        
        # Display order validation
        if self.display_order < 0:
            raise ValueError("Display order cannot be negative")
        
        # Root categories should not have parent
        if self.category_level == 1 and self.parent_category_id is not None:
            raise ValueError("Root categories cannot have a parent")
        
        # Non-root categories must have parent
        if self.category_level > 1 and self.parent_category_id is None:
            raise ValueError("Non-root categories must have a parent")
        
        # Path validation
        if not self.category_path:
            raise ValueError("Category path cannot be empty")
        
        if len(self.category_path) > 500:
            raise ValueError("Category path cannot exceed 500 characters")
    
    @validates('name')
    def validate_name(self, key, value):
        """Validate category name."""
        if not value or not value.strip():
            raise ValueError("Category name cannot be empty")
        if len(value) > 100:
            raise ValueError("Category name cannot exceed 100 characters")
        return value.strip()
    
    @validates('category_level')
    def validate_level(self, key, value):
        """Validate category level."""
        if value < 1:
            raise ValueError("Category level must be at least 1")
        return value
    
    @validates('display_order')
    def validate_display_order(self, key, value):
        """Validate display order."""
        if value < 0:
            raise ValueError("Display order cannot be negative")
        return value
    
    @validates('category_path')
    def validate_path(self, key, value):
        """Validate category path."""
        if not value:
            raise ValueError("Category path cannot be empty")
        if len(value) > 500:
            raise ValueError("Category path cannot exceed 500 characters")
        return value.strip()
    
    def update_info(
        self,
        name: Optional[str] = None,
        display_order: Optional[int] = None,
        updated_by: Optional[str] = None
    ):
        """
        Update category information.
        
        Args:
            name: New category name
            display_order: New display order
            updated_by: User making the update
        """
        if name is not None:
            if not name or not name.strip():
                raise ValueError("Category name cannot be empty")
            if len(name) > 100:
                raise ValueError("Category name cannot exceed 100 characters")
            self.name = name.strip()
        
        if display_order is not None:
            if display_order < 0:
                raise ValueError("Display order cannot be negative")
            self.display_order = display_order
        
        self.updated_by = updated_by
    
    def update_path(self, new_path: str, updated_by: Optional[str] = None):
        """
        Update category path. Usually called when parent category is renamed.
        
        Args:
            new_path: New category path
            updated_by: User making the update
        """
        if not new_path:
            raise ValueError("Category path cannot be empty")
        if len(new_path) > 500:
            raise ValueError("Category path cannot exceed 500 characters")
        
        self.category_path = new_path
        self.updated_by = updated_by
    
    def mark_as_parent(self, updated_by: Optional[str] = None):
        """Mark category as parent (not leaf)."""
        self.is_leaf = False
        self.updated_by = updated_by
    
    def mark_as_leaf(self, updated_by: Optional[str] = None):
        """Mark category as leaf (no children)."""
        self.is_leaf = True
        self.updated_by = updated_by
    
    def move_to_parent(
        self,
        new_parent_id: Optional[UUID],
        new_level: int,
        new_path: str,
        updated_by: Optional[str] = None
    ):
        """
        Move category to a new parent.
        
        Args:
            new_parent_id: New parent category ID
            new_level: New category level
            new_path: New category path
            updated_by: User making the update
        """
        if new_level < 1:
            raise ValueError("Category level must be at least 1")
        
        if new_level == 1 and new_parent_id is not None:
            raise ValueError("Root categories cannot have a parent")
        
        if new_level > 1 and new_parent_id is None:
            raise ValueError("Non-root categories must have a parent")
        
        self.parent_category_id = new_parent_id
        self.category_level = new_level
        self.category_path = new_path
        self.updated_by = updated_by
    
    @hybrid_property
    def child_count(self) -> int:
        """Get number of direct children."""
        # Always return 0 to prevent lazy loading in async context
        # Child count will be calculated explicitly in the service layer
        return 0
    
    @hybrid_property
    def item_count(self) -> int:
        """Get number of items in this category."""
        # items relationship is temporarily disabled
        # if self.items:
        #     return len(self.items)
        return 0
    
    def can_have_items(self) -> bool:
        """Check if this category can have items assigned."""
        return self.is_leaf
    
    def can_have_children(self) -> bool:
        """Check if this category can have child categories."""
        return True  # Any category can have children
    
    def can_delete(self) -> bool:
        """Check if category can be deleted."""
        # Can only delete if no children and no items
        return (
            self.is_active and 
            self.child_count == 0 and 
            self.item_count == 0
        )
    
    def is_root(self) -> bool:
        """Check if this is a root category."""
        return self.category_level == 1 and self.parent_category_id is None
    
    def is_descendant_of(self, ancestor_path: str) -> bool:
        """Check if this category is a descendant of the given ancestor path."""
        if not ancestor_path:
            return False
        return self.category_path.startswith(f"{ancestor_path}/")
    
    def is_ancestor_of(self, descendant_path: str) -> bool:
        """Check if this category is an ancestor of the given descendant path."""
        if not descendant_path:
            return False
        return descendant_path.startswith(f"{self.category_path}/")
    
    def get_path_segments(self) -> List[str]:
        """Get category path as a list of segments."""
        if not self.category_path:
            return []
        return self.category_path.split("/")
    
    def get_depth(self) -> int:
        """Get the depth of this category in the hierarchy."""
        return self.category_level
    
    def get_breadcrumb(self) -> List[str]:
        """Get breadcrumb trail as list of category names."""
        return self.get_path_segments()
    
    def get_parent_path(self) -> Optional[str]:
        """Get parent category path."""
        if self.is_root():
            return None
        
        segments = self.get_path_segments()
        if len(segments) <= 1:
            return None
        
        return "/".join(segments[:-1])
    
    def generate_path(self, parent_path: Optional[str] = None) -> str:
        """Generate category path based on parent path and current name."""
        if parent_path:
            return f"{parent_path}/{self.name}"
        return self.name
    
    @property
    def full_name(self) -> str:
        """Get full category name with path."""
        return self.category_path
    
    @property
    def has_children(self) -> bool:
        """Check if category has children."""
        return not self.is_leaf
    
    @property
    def has_items(self) -> bool:
        """Check if category has items."""
        # items relationship is temporarily disabled
        return False
    
    def __str__(self) -> str:
        """String representation of category."""
        return f"Category({self.category_path})"
    
    def __repr__(self) -> str:
        """Developer representation of category."""
        return (
            f"Category(id={self.id}, name='{self.name}', "
            f"path='{self.category_path}', level={self.category_level}, "
            f"is_leaf={self.is_leaf}, active={self.is_active})"
        )


class CategoryPath:
    """Value object for managing category paths."""
    
    def __init__(self, path: str):
        """Initialize category path."""
        if not path:
            raise ValueError("Category path cannot be empty")
        self.path = path.strip().strip("/")  # Remove leading/trailing slashes and whitespace
    
    def append(self, segment: str) -> "CategoryPath":
        """Append a segment to the path."""
        if not segment or not segment.strip():
            raise ValueError("Path segment cannot be empty")
        segment = segment.strip()
        return CategoryPath(f"{self.path}/{segment}")
    
    def parent_path(self) -> Optional["CategoryPath"]:
        """Get the parent path, or None if this is root."""
        segments = self.path.split("/")
        if len(segments) <= 1:
            return None
        return CategoryPath("/".join(segments[:-1]))
    
    def replace_segment(self, old_segment: str, new_segment: str) -> "CategoryPath":
        """Replace a segment in the path."""
        if not old_segment or not new_segment:
            raise ValueError("Segments cannot be empty")
        
        segments = self.path.split("/")
        new_segments = [new_segment.strip() if seg == old_segment else seg for seg in segments]
        return CategoryPath("/".join(new_segments))
    
    def starts_with(self, prefix: str) -> bool:
        """Check if path starts with a prefix."""
        if not prefix:
            return False
        return self.path.startswith(prefix)
    
    def get_segments(self) -> List[str]:
        """Get path segments as a list."""
        return self.path.split("/")
    
    def get_level(self) -> int:
        """Get the level (depth) of this path."""
        return len(self.get_segments())
    
    def get_last_segment(self) -> str:
        """Get the last segment (category name)."""
        segments = self.get_segments()
        return segments[-1] if segments else ""
    
    def get_first_segment(self) -> str:
        """Get the first segment (root category name)."""
        segments = self.get_segments()
        return segments[0] if segments else ""
    
    def is_root(self) -> bool:
        """Check if this is a root path (single segment)."""
        return len(self.get_segments()) == 1
    
    def is_descendant_of(self, ancestor: "CategoryPath") -> bool:
        """Check if this path is a descendant of the given ancestor."""
        return self.path.startswith(f"{ancestor.path}/")
    
    def is_ancestor_of(self, descendant: "CategoryPath") -> bool:
        """Check if this path is an ancestor of the given descendant."""
        return descendant.path.startswith(f"{self.path}/")
    
    def common_ancestor(self, other: "CategoryPath") -> Optional["CategoryPath"]:
        """Find the common ancestor path with another path."""
        self_segments = self.get_segments()
        other_segments = other.get_segments()
        
        common_segments = []
        for i in range(min(len(self_segments), len(other_segments))):
            if self_segments[i] == other_segments[i]:
                common_segments.append(self_segments[i])
            else:
                break
        
        if not common_segments:
            return None
        
        return CategoryPath("/".join(common_segments))
    
    def __str__(self) -> str:
        """String representation."""
        return self.path
    
    def __eq__(self, other) -> bool:
        """Check equality."""
        if not isinstance(other, CategoryPath):
            return False
        return self.path == other.path
    
    def __hash__(self) -> int:
        """Hash for use in sets and dicts."""
        return hash(self.path)
    
    def __lt__(self, other) -> bool:
        """Less than comparison for sorting."""
        if not isinstance(other, CategoryPath):
            return NotImplemented
        return self.path < other.path