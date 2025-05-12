"""Custom model ready to use custom items."""

from __future__ import annotations
from collections.abc import Iterator
from typing import Any, TypeVar

import math

import Qt.QtCore as qtc

from .item import Item, TreeItem

T = TypeVar("T", bound=Item)
TT = TypeVar("TT", bound=TreeItem)


class ListModel(qtc.QAbstractListModel):
    """List Model without columns."""

    DataRole = qtc.Qt.UserRole + 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__items: list[T] = []

    def insert_item(self, item: T, pos: int = -1) -> bool:
        pos = _get_abs_pos(pos, self.rowCount())
        return self.insertRow(pos, item=item)

    def insert_items(self, items: list[T], pos: int = -1) -> bool:
        pos = _get_abs_pos(pos, self.rowCount())
        return self.insertRows(pos, len(items), items=items)

    def delete_item(self, item: T) -> bool:
        return self.removeRow(self.__items.index(item))

    def delete_items(self, items: list[T]):
        for item in sorted(items, key=lambda i: self.__items.index(i), reverse=True):
            self.delete_item(item)

    def move_item(self, item: T, pos: int = -1):
        item_pos = self.__items.index(item)
        pos = _get_abs_pos(pos, self.rowCount())
        return self.moveRow(item_pos, pos)

    def move_items(self, items: list[T], pos: int = -1):
        pos = _get_abs_pos(pos, self.rowCount())
        for i, item in enumerate(sorted(items, key=lambda idx: self.__items.index(idx), reverse=True)):
            item_pos = self.__items.index(item)
            self.moveRow(item_pos, pos + i)

    def clear(self):
        self.beginResetModel()
        del self.__items[:]
        self.endResetModel()

    def index(self, row: int = 0, column: int = 0,
              parent: qtc.QModelIndex | None = None) -> qtc.QModelIndex:
        if 0 <= row <= self.rowCount():
            return self.createIndex(row, column, self.__items[row])

        return qtc.QModelIndex()

    def iter_indices(self) -> Iterator[qtc.QModelIndex]:
        for i in range(self.rowCount()):
            index = self.index(i)

            if index.isValid():
                yield index

    def rowCount(self, _: qtc.QModelIndex | None = None) -> int:
        return len(self.__items)

    def data(self, index: qtc.QModelIndex, role: qtc.Qt.ItemDataRole) -> Any:
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == self.DataRole:
            return item.data

        return None

    def insertRow(self, row: int,
                  parent: qtc.QModelIndex | None = None,
                  item: Item | None = None,
                  ) -> bool:
        if not 0 <= row <= self.rowCount():
            return False

        if parent is None:
            parent = qtc.QModelIndex()

        self.beginInsertRows(parent, row, row)
        if item:
            self.__items.insert(row, item)
        self.endInsertRows()
        return True

    def insertRows(self, row: int, count: int,
                   parent: qtc.QModelIndex | None = None,
                   items: list[T] | None = None,
                   ) -> bool:

        if not 0 <= row <= self.rowCount():
            return False

        if items and len(items) != count:
            return False

        if parent is None:
            parent = qtc.QModelIndex()

        self.beginInsertRows(parent, row, row + count - 1)
        if items:
            for i in range(count):
                self.__items.insert(row + i, items[i])
        self.endInsertRows()
        return True

    def removeRow(self, row: int, parent: qtc.QModelIndex | None = None) -> bool:
        if parent is None:
            parent = qtc.QModelIndex

        if not 0 <= row < self.rowCount():
            return False

        self.beginRemoveRows(parent, row, row)
        del self.__items[row]
        self.endRemoveRows()
        return True

    def removeRows(self, row: int, count: int, parent: qtc.QModelIndex | None = None) -> bool:
        end_row = row + count - 1
        if not 0 <= row < end_row < self.rowCount():
            return False

        if parent is None:
            parent = qtc.QModelIndex()

        self.beginRemoveRows(parent, row, end_row)
        del self.__items[row: end_row + 1]
        self.endRemoveRows()
        return True

    def moveRow(self, src_row: int, dst_row: int,
                parent: qtc.QModelIndex | None = None) \
            -> bool:
        if not 0 <= src_row | dst_row < self.rowCount():
            return False

        if parent is None:
            parent = qtc.QModelIndex()

        self.beginMoveRows(parent, src_row, src_row, parent, dst_row)
        item = self.__items.pop(src_row)
        self.__items.insert(dst_row, item)
        self.endMoveRows()
        return True

    def moveRows(self, src_row: int, count: int,
                 dst_row: int,
                 parent: qtc.QModelIndex | None = None) -> bool:
        end_row = src_row + count - 1
        if 0 < src_row | dst_row < self.rowCount():
            return False

        if parent is None:
            parent = qtc.QModelIndex()

        self.beginMoveRows(parent, src_row, end_row, parent, dst_row)
        items = self.__items[src_row: src_row + count]
        [self.__items.remove(n) for n in items]

        for i in range(count):
            self.__items.insert(dst_row + count, items[i])
        self.endMoveRows()
        return True

    @property
    def items(self) -> Iterator[T]:
        yield from self.__items


class TableModel(qtc.QAbstractTableModel):

    DataRole = qtc.Qt.UserRole + 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__items = []
        self.COL_COUNT = 1

    def insert_item(self, item: T, pos: int = -1):
        pos = _get_abs_pos(pos, self.rowCount())
        column = self.rowCount() % self.columnCount()

        if column == 0:
            self.insertRow(self.rowCount() - 1, item=item)
        else:
            self.__items.insert(pos, item)
            self.dataChanged.emit(self.rowCount(), column)

    def insert_items(self, items: list[T], pos: int = -1):
        pos = _get_abs_pos(pos, self.rowCount())

        column = self.rowCount() % self.columnCount()
        if column:
            for i in range(self.columnCount() - column):
                self.__items.insert(pos + i, items.pop(0))
                self.dataChanged.emit(self.rowCount(), column)
                pos += 1

        if items:
            row = math.floor(pos / self.columnCount())
            row_count = (
                math.ceil(
                    (len(items) + self.rowCount()) / self.columnCount(),
                )
                - self.rowCount()
            )
            self.insertRows(row, row_count, items=items)

    def clear(self):
        self.beginResetModel()
        del self.__items[:]
        self.endResetModel()

    def index(
        self, row: int = 0, column: int = 0, parent: qtc.QModelIndex | None = None,
    ) -> qtc.QModelIndex:
        pos = self.columnCount() * row + column

        if (
            0 <= row < self.rowCount()
            and 0 <= column < self.columnCount()
            and pos < self.rowCount()
        ):
            return self.createIndex(row, column, self.__items[pos])

        return qtc.QModelIndex()

    def data(self, index: qtc.QModelIndex, role: qtc.Qt.ItemDataRole) -> Any:
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == self.DataRole:
            return item.data

        return None

    def iter_indices(self) -> Iterator[qtc.QModelIndex]:
        row = -1
        column = 0
        for i in range(self.rowCount()):
            if i % self.columnCount() == 0:
                row += 1
                column = 0
            else:
                column += 1

            index = self.index(row, column)

            if index.isValid():
                yield index

    def rowCount(self, parent: qtc.QModelIndex | None = None) -> int:
        return math.ceil(len(self.__items) / self.columnCount())

    def columnCount(self, parent: qtc.QModelIndex | None = None) -> int:
        return self.COL_COUNT

    def insertRow(
        self,
        row: int,
        parent: qtc.QModelIndex | None = None,
        item: Item | None = None,
    ) -> bool:
        if parent is None:
            parent = qtc.QModelIndex()

        if not 0 <= row <= self.rowCount():
            return False

        self.beginInsertRows(parent, row, row)

        if item:
            pos = row * self.columnCount()
            self.__items.insert(pos, item)

        self.endInsertRows()
        return True

    def insertRows(
            self,
            row: int,
            count: int,
            parent: qtc.QModelIndex | None = None,
            items: list[T] | None = None,
    ) -> bool:
        end_row = row + count - 1

        if not 0 <= row < end_row <= self.rowCount():
            return False

        if parent is None:
            parent = qtc.QModelIndex()

        self.beginInsertRows(parent, row, end_row)

        if items:
            pos = row * self.columnCount()

            for i in range(len(items)):
                self.__items.insert(pos + i, items[i])

        self.endInsertRows()
        return True

    def insertColumn(
            self,
            column: int,
            parent: qtc.QModelIndex | None = None,
            item: T | None = None,
    ) -> bool:
        if not 0 <= column <= self.columnCount():
            return False

        if parent is None:
            parent = qtc.QModelIndex()

        self.beginInsertColumns(parent, column, column)

        # TODO(amallaroni): use node data
        row_count = abs(
            math.ceil(self.rowCount() / self.columnCount()) - self.rowCount(),
        )

        if row_count:
            self.removeRows(self.rowCount(), row_count, parent)

        self.endInsertColumns()
        return True

    def insertColumns(
            self,
            column: int,
            count: int,
            parent: qtc.QModelIndex | None = None,
            items: list[T] | None = None,
    ) -> bool:
        end_col = column + count - 1

        if not 0 <= column < end_col <= self.columnCount():
            return False

        if parent is None:
            parent = qtc.QModelIndex()

        self.beginInsertColumns(parent, column, end_col)

        # TODO(amallaroni): use node data
        row_count = abs(
            math.ceil(self.rowCount() / self.columnCount()) - self.rowCount(),
        )

        if row_count:
            self.removeRows(self.rowCount(), row_count, parent)

        self.endInsertColumns()
        return True

    def removeRow(self, row: int, parent: qtc.QModelIndex | None = None) -> bool:
        if not 0 < row < self.rowCount():
            return False

        if parent is None:
            parent = qtc.QModelIndex()

        self.beginRemoveRows(parent, row, row)

        pos = row * self.columnCount()
        end_pos = min(pos + self.columnCount(), self.rowCount())
        del self.__items[pos:end_pos]

        self.endRemoveRows()
        return True

    def removeRows(
            self, row: int, count: int, parent: qtc.QModelIndex | None = None
    ) -> bool:
        if parent is None:
            parent = qtc.QModelIndex()

        end_row = row + count - 1

        if not 0 <= row < end_row <= self.rowCount():
            return False

        self.beginRemoveRows(parent, row, end_row)

        pos = row * self.columnCount()
        end_pos = min(pos + (count * self.columnCount()), self.rowCount())
        del self.__items[pos:end_pos]

        self.endRemoveRows()
        return True

    def removeColumn(self, column: int, parent: qtc.QModelIndex | None = None) -> bool:
        if parent is None:
            parent = qtc.QModelIndex()

        return self.removeColumns(column, 1, parent)

    def removeColumns(
            self, column: int, count: int, parent: qtc.QModelIndex | None = None
    ) -> bool:
        end_col = column + count - 1

        if not 0 < column < end_col < self.columnCount():
            return False

        if parent is None:
            parent = qtc.QModelIndex()

        self.beginRemoveColumns(parent, column, end_col)

        row_count = math.ceil(self.rowCount() / self.columnCount()) - self.rowCount()

        if row_count:
            self.insertRows(self.rowCount(), row_count, parent)

        self.endRemoveColumns()
        return True


class ListTreeModel(qtc.QAbstractItemModel):
    """List on Tree Model with columns."""

    HEADERS_NAME: tuple[str] = ("Name",)
    DataRole = qtc.Qt.UserRole + 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__items: list[T] = []
        self.COL_COUNT = len(self.HEADERS_NAME)

    def insert_item(self, item: T, pos: int = -1) -> bool:
        pos = _get_abs_pos(pos, self.rowCount())
        return self.insertRow(pos, item=item)

    def insert_items(self, items: list[T], pos: int = -1) -> bool:
        pos = _get_abs_pos(pos, self.rowCount())
        return self.insertRows(pos, len(items), items=items)

    def delete_item(self, item: T) -> bool:
        return self.removeRow(self.__items.index(item))

    def delete_items(self, items: list[T]):
        for item in sorted(items, key=lambda i: self.__items.index(i), reverse=True):
            self.delete_item(item)

    def move_item(self, item: T, pos: int = -1):
        item_pos = self.__items.index(item)
        pos = _get_abs_pos(pos, self.rowCount())
        return self.moveRow(item_pos, pos)

    def move_items(self, items: list[T], pos: int = -1):
        pos = _get_abs_pos(pos, self.rowCount())
        for i, item in enumerate(sorted(items, key=lambda i: self.__items.index(i), reverse=True)):
            item_pos = self.__items.index(item)
            self.moveRow(item_pos, pos + i)

    def clear(self):
        self.beginResetModel()
        del self.__items[:]
        self.endResetModel()

    def index(self, row: int = 0, column: int = 0,
              parent: qtc.QModelIndex | None = None) -> qtc.QModelIndex:
        if 0 <= row <= self.rowCount():
            return self.createIndex(row, column, self.__items[row])

    def data(self, index: qtc.QModelIndex, role: qtc.Qt.ItemDataRole) -> Any:

        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == self.DataRole:
            return item.data

        return None

    def iter_indices(self) -> Iterator[qtc.QModelIndex]:
        for i in range(self.rowCount()):
            index = self.index(i)

            if index.isValid():
                yield index

    def rowCount(self, _: qtc.QModelIndex | None = None) -> int:
        return len(self.__items)

    def columnCount(self, _: qtc.QModelIndex | None = None) -> int:
        return self.COL_COUNT

    def headerData(self, section: int, orientation: qtc.Qt.Orientation, role: qtc.Qt.ItemDataRole) -> str:
        if role == qtc.Qt.DisplayRole and orientation == qtc.Qt.Horizontal:
            return self.HEADERS_NAME[section]

        return super().headerData(section, orientation, role)

    def insertRow(self, row: int,
                  parent: qtc.QModelIndex | None = None,
                  item: T | None = None,
                  ) -> bool:
        if not 0 <= row <= self.rowCount():
            return False

        if parent is None:
            parent = qtc.QModelIndex()

        self.beginInsertRows(parent, row, row)
        if item:
            self.__items.insert(row, item)
        self.endInsertRows()
        return True

    def insertRows(self, row: int, count: int,
                   parent: qtc.QModelIndex | None = None,
                   items: list[T] | None = None,
                   ) -> bool:
        if not 0 <= row <= self.rowCount():
            return False

        if items and len(items) != count:
            return False

        if parent is None:
            parent = qtc.QModelIndex()

        self.beginInsertRows(parent, row, row + count - 1)
        if items:
            for i in range(count):
                self.__items.insert(row + i, items[i])
        self.endInsertRows()
        return True

    def removeRow(self, row: int, parent: qtc.QModelIndex | None = None) -> bool:
        if parent is None:
            parent = qtc.QModelIndex

        if not 0 <= row < self.rowCount():
            return False

        self.beginRemoveRows(parent, row, row)
        del self.__items[row]
        self.endRemoveRows()
        return True

    def removeRows(self, row: int, count: int, parent: qtc.QModelIndex | None = None) -> bool:
        end_row = row + count - 1
        if not 0 <= row < end_row < self.rowCount():
            return False

        if parent is None:
            parent = qtc.QModelIndex()

        self.beginRemoveRows(parent, row, end_row)
        del self.__items[row: end_row + 1]
        self.endRemoveRows()
        return True

    def moveRow(self, src_row: int, dst_row: int,
                parent: qtc.QModelIndex | None = None) \
            -> bool:
        if not 0 <= src_row | dst_row < self.rowCount():
            return False

        if parent is None:
            parent = qtc.QModelIndex()

        self.beginMoveRows(parent, src_row, src_row, parent, dst_row)
        item = self.__items.pop(src_row)
        self.__items.insert(dst_row, item)
        self.endMoveRows()
        return True

    def moveRows(self, src_row: int, count: int,
                 dst_row: int,
                 parent: qtc.QModelIndex | None = None) -> bool:
        end_row = src_row + count - 1
        if 0 < src_row | dst_row < self.rowCount():
            return False

        if parent is None:
            parent = qtc.QModelIndex()

        self.beginMoveRows(parent, src_row, end_row, parent, dst_row)
        items = self.__items[src_row: src_row + count]
        [self.__items.remove(n) for n in items]

        for i in range(count):
            self.__items.insert(dst_row + count, items[i])
        self.endMoveRows()
        return True

    @property
    def items(self) -> Iterator[T]:
        yield from self.__items


class TreeModel(qtc.QAbstractItemModel):
    """Tree Model."""

    HEADERS_NAME: tuple[str] = ("Name",)
    DataRole = qtc.Qt.UserRole + 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.COL_COUNT = len(self.HEADERS_NAME)
        self.root_item = TreeItem("root")

    def insert_item(self, item: TT,
                    parent_item: TT | None = None,
                    pos: int = -1):
        if parent_item is None:
            parent_item = self.root_item
            parent_index = None
        else:
            for index in self.iter_indices(recursive=True):
                if index.internalPointer() == parent_item:
                    parent_index = index
                    break
            else:
                raise ValueError(f"No parent index found from {parent_item.name!r}.")

        pos = _get_abs_pos(pos, parent_item.child_count)
        self.insertRow(pos, parent_index, item)

    def insert_items(self, items: list[TT],
                     parent_item: TT | None = None,
                     pos: int = -1):
        if parent_item is None:
            parent_item = self.root_item
            parent_index = None
        else:
            for index in self.iter_indices(recursive=True):
                if index.internalPointer() == parent_item:
                    parent_index = index
                    break
            else:
                raise ValueError(f"No parent index found from {parent_item.name!r}.")

        pos = _get_abs_pos(pos, parent_item.child_count)
        self.insertRows(pos, len(items), parent_index, items)

    def delete_item(self, item: TT):
        for idx in self.iter_indices(recursive=True):
            if idx.internalPointer() == item:
                self.removeRow(idx.row(), idx.parent())
                break

    def delete_items(self, items: list[TT]):
        idx_to_delete = []
        for idx in self.iter_indices(recursive=True):
            if idx.internalPointer() in items:
                idx_to_delete.append(idx)
                if len(idx_to_delete) == len(items):
                    break

        for idx in sorted(idx_to_delete, key=lambda i: i.row(), reverse=True):
            self.removeRow(idx.row(), idx.parent())

    def move_item(self, item: TT,
                  dst_parent_item: TT | None = None,
                  pos: int = -1):
        item_index = None
        dst_parent_index = None

        if dst_parent_item is None:
            dst_parent_item = self.root_item

        for index in self.iter_indices(recursive=True):
            it = index.internalPointer()
            if it == item:
                item_index = index
            elif it == dst_parent_item:
                dst_parent_index = index

            if item_index and dst_parent_index:
                break
        else:
            raise ValueError("Don't find parent index or destination index.")

        pos = _get_abs_pos(pos, dst_parent_item.child_count)
        self.moveRow(item_index.row(), pos, index.parent(), dst_parent_index)

    def move_items(self, items: list[TT],
                   dst_parent_item: TT | None = None,
                   pos: int = -1):
        item_indices = []
        dst_parent_index = None

        if dst_parent_item is None:
            dst_parent_item = self.root_item

        for index in self.iter_indices(recursive=True):
            item = index.internalPointer()
            if item in items:
                item_indices.append(index)

            elif item == dst_parent_item:
                dst_parent_index = index

            if len(items) == len(item_indices) and dst_parent_index:
                break
        else:
            raise ValueError("Don't find parent indices or destination index.")

        pos = _get_abs_pos(pos, dst_parent_item.child_count)
        for i, index in enumerate(sorted(item_indices, key=lambda idx: idx.row(), reverse=True)):
            self.moveRow(index.row(), pos + i, index.parent(), dst_parent_index)

    def clear(self):
        self.beginResetModel()
        self.root_item = TreeItem("root")
        self.endResetModel()

    def index(self, row: int, column: int,
              parent: qtc.QModelIndex | None = None) -> qtc.QModelIndex:
        if parent is None:
            parent = qtc.QModelIndex()

        if not self.hasIndex(row, column, parent):
            return qtc.QModelIndex()

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)

        return qtc.QModelIndex()

    def parent(self, index: qtc.QModelIndex):
        if not index.isValid():
            return qtc.QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent

        if parent_item == self.root_item or parent_item is None:
            return qtc.QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def data(self, index: qtc.QModelIndex, role: qtc.Qt.ItemDataRole) -> Any:
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == self.DataRole:
            return item.data

        return None

    def iter_indices(self, parent: qtc.QModelIndex | None = None,
                     recursive: bool = False) \
            -> Iterator[qtc.QModelIndex]:
        if parent is None:
            parent = qtc.QModelIndex()

        for row in range(self.rowCount(parent)):
            index = self.index(row, 0, parent)
            yield index

            if recursive:
                yield from self.iter_indices(index, recursive)

    def rowCount(self, index: qtc.QModelIndex | None = None) -> int:
        if index is None:
            index = qtc.QModelIndex()

        if not index.isValid():
            item = self.root_item
        else:
            item = index.internalPointer()

        return item.child_count

    def columnCount(self, parent: qtc.QModelIndex | None = None) -> int:
        return self.COL_COUNT

    def insertRow(self, row: int, parent: qtc.QModelIndex | None = None,
                  item: TT | None = None) -> bool:
        if parent is None:
            parent = qtc.QModelIndex()

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        if not 0 <= row <= parent_item.child_count:
            return False

        self.beginInsertRows(parent, row, row)
        if item:
            parent_item.insert_child(item, row)
        self.endInsertRows()
        return True

    def insertRows(self, row: int, count: int,
                   parent: qtc.QModelIndex | None = None,
                   items: list[TT] | None = None) -> bool:
        if parent is None:
            parent = qtc.QModelIndex()

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        if not 0 <= row < parent_item.child_count:
            return False

        if items and len(items) != count:
            return False

        self.beginInsertRows(parent, row, row + count - 1)
        if items:
            for i in range(count):
                parent_item.insert_child(items[i], row + i)
        self.endInsertRows()
        return True

    def removeRow(self, row: int,
                  parent: qtc.QModelIndex | None = None) -> bool:
        if parent is None:
            parent = qtc.QModelIndex()

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        if not 0 <= row < parent_item.child_count:
            return False

        self.beginRemoveRows(parent, row, row)
        parent_item.remove_child(parent_item.child(row))
        self.endRemoveRows()
        return True

    def removeRows(self, row: int, count: int,
                   parent: qtc.QModelIndex | None = None) -> bool:
        if parent is None:
            parent = qtc.QModelIndex()

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        end_row = row + count - 1
        if not 0 <= row < end_row < parent_item.child_count:
            return False

        self.beginRemoveRows(parent, row, end_row)
        for i in reversed(range(count)):
            parent_item.remove_child(parent_item.child(row + i))
        self.endRemoveRows()
        return True

    def moveRow(self, src_row: int, dst_row: int,
                src_parent: qtc.QModelIndex | None = None,
                dst_parent: qtc.QModelIndex | None = None) -> bool:
        if src_parent is None:
            src_parent = qtc.QModelIndex()

        if dst_parent is None:
            dst_parent = qtc.QModelIndex()

        if not src_parent.isValid():
            src_item = self.root_item
        else:
            src_item = src_parent.internalPointer()

        if not dst_parent.isValid():
            dst_item = self.root_item
        else:
            dst_item = dst_parent.internalPointer()

        if not 0 <= src_row < src_item.child_count:
            return False

        if not 0 <= dst_row < dst_item.child_count:
            return False

        self.beginMoveRows(src_parent, src_row, src_row,
                           dst_parent, dst_row)
        item = src_item.child(src_row)
        dst_item.insert_child(item, dst_row)
        self.endMoveRows()
        return True

    def moveRows(self, src_row, count: int, dst_row,
                 src_parent: qtc.QModelIndex | None = None,
                 dst_parent: qtc.QModelIndex | None = None) -> bool:

        if src_parent is None:
            src_parent = qtc.QModelIndex()

        if dst_parent is None:
            dst_parent = qtc.QModelIndex()

        if not src_parent.isValid():
            src_item = self.root_item
        else:
            src_item = src_parent.internalPointer()

        if not dst_parent.isValid():
            dst_item = self.root_item
        else:
            dst_item = dst_parent.internalPointer()

        if not 0 <= src_row < src_item.child_count:
            return False

        if not 0 <= dst_row < dst_item.child_count:
            return False

        self.beginMoveRows(src_parent, src_row, src_row + count,
                           dst_parent, dst_row)
        for i in range(count):
            item = src_item.child(src_row)
            dst_item.insert_child(item, dst_row + i)
        self.endMoveRows()
        return True


def _get_abs_pos(pos: int, len_: int) -> int:
    """Return the absolute pos (int >= 0).

    From the given pos and length of list.

    Args:
        pos (int): relative position.
        len_ (int): length of the list.

    Return:
        int
    """
    return pos if pos >= 0 else len_ + pos + 1
