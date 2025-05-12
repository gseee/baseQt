"""Items to use on model and view."""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any, TypeVar, Generic

T = TypeVar("T")
TT = TypeVar("TT")

class Item(Generic[T]):
    """Base item used in view."""

    def __init__(self, name: str, data: Any | None = None):
        self.name = name
        self.data = data

class TreeItem(Generic[TT]):
    """Base item used in TreeView."""

    def __init__(self, name: str, data: Any | None = None,
                 parent: TT | None = None):
        self.name = name
        self.data = data
        self.__parent = parent
        self.__children = []

    def insert_child(self, children: TT, pos: int = -1):
        """Insert given tree item in children in given position."""
        self.__children.insert(pos, children)
        children.parent = self

    def remove_child(self, child: TT):
        """Remove given item from children."""
        self.__children.remove(child)
        child.parent = None

    def child(self, pos: int) -> TT:
        """Return the child on given position."""
        return self.__children[pos]

    def iter_children(self, recursive: bool = False) -> Iterator[TT]:
        """Iterate children.

        Args:
            recursive: Iterate recursively.
        """
        for child in self.__children:
            yield child

            if child.children and recursive:
                yield from child.iter_children(recursive)

    def iter_parent(self) -> Iterator[TT]:
        """Iterate all parents."""
        item = self

        while True:
            parent = item.parent

            if parent:
                yield parent
            else:
                return

            item = parent

    @property
    def child_count(self) -> int:
        """Return the child count of the tree item."""
        return len(self.__children)

    @property
    def index(self) -> int:
        """Return the item position of the item parent."""
        return self.__parent.children.index(self) if self.__parent else 0

    @property
    def children(self) -> list[TT]:
        """Return children."""
        return self.__children

    @property
    def parent(self) -> TT | None:
        """Return the parent of the tree item."""
        return self.__parent

    @parent.setter
    def parent(self, parent: TT | None):
        """Set the parent of the item."""
        if self.__parent is not None:
            self.__parent.remove_child(self)

        self.__parent = parent
