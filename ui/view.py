"""Custom views ready to use custom items."""

from __future__ import annotations

import Qt.QtCore as qtc
import Qt.QtWidgets as qtw

from item import Item


class View(qtw.QAbstractItemView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSelectionMode(self.ExtendedSelection)

    def select_index(self, index: qtc.QModelIndex):
        self.scrollTo(index, self.PositionAtCenter)
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

    def selected_item(self) -> Item:
        return self.selected_index().internalPointer()

    def selected_items(self) -> list[Item]:
        return [idx.internalPointer() for idx in self.selected_indices()]


class TableView(qtw.QTableView, View):
    """Table View"""


class TreeView(qtw.QTreeView, View):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSelectionMode(qtw.QAbstractItemView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setUniformRowHeights(True)
