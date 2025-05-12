"""Custom views ready to use custom items."""

from __future__ import annotations

from typing import TypeVar

import Qt.QtCore as qtc
import Qt.QtWidgets as qtw

from .item import Item, TreeItem

T = TypeVar("T", bound=Item)
TT = TypeVar("TT", bound=TreeItem)


class AbstractView:
    """Abstract methods for views."""

    def select_index(self, index: qtc.QModelIndex):
        self.scrollTo(index, self.ScrollHint.PositionAtCenter)
        self.selectionModel().select(
            index, qtc.QItemSelectionModel.Select | qtc.QItemSelectionModel.Rows)

    def select_indices(self, indices: list[qtc.QModelIndex]):
        selection = qtc.QItemSelection
        for idx in indices:
            selection.select(idx, idx)

        self.selectionModel().select(
            selection, qtc.QItemSelectionModel.Select | qtc.QItemSelectionModel.Rows)

    def selected_index(self) -> qtc.QModelIndex:
        selection = self.selectionModel().selectedRows()
        if len(selection) == 1:
            return selection[0]

    def selected_indices(self) -> list[qtc.QModelIndex]:
        return self.selectionModel().selectedRows()

    def selected_item(self) -> T:
        return self.selected_index().internalPointer()

    def selected_items(self) -> list[T]:
        return [idx.internalPointer() for idx in self.selected_indices()]


class ListView(qtw.QListView, AbstractView):
    """List View without columns."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSelectionMode(qtw.QAbstractItemView.ExtendedSelection)
        self.setAlternatingRowColors(True)


class TableView(qtw.QTableView, AbstractView):
    """Table View"""


class ListTreeView(qtw.QTreeView, AbstractView):
    """List View with columns."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSelectionMode(qtw.QAbstractItemView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setUniformRowHeights(True)
        self.setRootIsDecorated(False)


class TreeView(qtw.QTreeView, AbstractView):
    """Tree View."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSelectionMode(qtw.QAbstractItemView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setUniformRowHeights(True)

    def selected_item(self) -> TT:
        return super().selected_item()

    def selected_items(self) -> list[TT]:
        return super().selected_items()

