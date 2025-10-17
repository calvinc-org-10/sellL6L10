from typing import (Dict, List, Any, Type, )

from PySide6.QtCore import (
    Qt, 
    QAbstractTableModel, 
    QModelIndex, QPersistentModelIndex,
    )

import sqlalchemy
from sqlalchemy import (select, text, )
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (Session, sessionmaker, )
from sqlalchemy.dialects import sqlite

from .messageBoxes import pleaseWriteMe


class cDictModel(QAbstractTableModel):
    """ A model for displaying a dictionary in a table format.
    """
    def __init__(self, data:Dict[str, Any], parent=None):
        """
        Initialize the model with a dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary to model.
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)
        self._data = data
        self._keys = list(data.keys())

    def rowCount(self, parent=None):
        """Return the number of rows in the model."""
        return len(self._data)

    def columnCount(self, parent=None):
        """Return the number of columns in the model (Key and Value)."""
        return 2  # One for the key and one for the value

    def data(self, index, role:int=Qt.ItemDataRole.DisplayRole):
        """Return the data for a given cell."""
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None

        row = index.row()
        col = index.column()

        key = self._keys[row]
        if col == 0:  # Key column
            return key
        elif col == 1:  # Value column
            return self._data[key]
        return None

    def headerData(self, section, orientation, role:int=Qt.ItemDataRole.DisplayRole):
        """Return the header labels for rows or columns."""
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        if orientation == Qt.Orientation.Horizontal:
            return ["Key", "Value"][section]  # Column headers
        elif orientation == Qt.Orientation.Vertical:
            return str(section + 1)  # Row numbers
        return None

    def setData(self, index, value, role:int=Qt.ItemDataRole.EditRole):
        """Set the data for a given cell."""
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False

        row = index.row()
        col = index.column()
        key = self._keys[row]

        if col == 1:  # Only allow editing the value column
            self._data[key] = value
            self.dataChanged.emit(index, index, [role])
            return True

        return False

    def flags(self, index):
        """Set flags for each cell."""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        if index.column() == 1:  # Only value column is editable
            flags |= Qt.ItemFlag.ItemIsEditable

        return flags

class SQLAlchemyTableModel(QAbstractTableModel):
    def __init__(self, model_class:Type[Any], session_factory:sessionmaker, filter = None, orderby = None, parent=None):
        super().__init__(parent)
        self.session_factory = sessionmaker(
            class_=session_factory.class_,
            # bind=session_factory.kw['bind'],
            **{**session_factory.kw, "expire_on_commit": False}
        )
        self.model_class = model_class
        self._data = []
        self._dirty = set()  # {(row, col)} pairs that are dirty
        # self.header = []
        
        # Set headers based on model class (optional)
        # if hasattr(model_class, '__table__'):
        self.header = [column.name for column in model_class.__table__.columns]

        self.refresh(filter, orderby)
    
    def refresh(self, filter = None, orderby = None):
        """Reload data from the database"""
        with self.session_factory() as session:
            stmt = select(self.model_class)
            if filter is not None:
                stmt = stmt.where(filter)
            if orderby is not None:
                stmt = stmt.order_by(orderby)
            rows = session.execute(stmt).scalars().all()
            for row in rows:
                session.expunge(row)  # detach from session

        self.beginResetModel()
        self._data = rows
        self._dirty.clear()  # nothing's dirty
        self.endResetModel()
    
    def rowCount(self, parent:QModelIndex | QPersistentModelIndex=QModelIndex()):
        """Return number of rows"""
        return len(self._data)
    
    def columnCount(self, parent:QModelIndex | QPersistentModelIndex=QModelIndex()):
        """Return number of columns"""
        return len(self.header) if self.header else len(self._data[0].__table__.columns)
    
    def data(self, index, role:int=Qt.ItemDataRole.DisplayRole):
        """Return data at index for given role"""
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            row = index.row()
            col = index.column()
            
            if row >= len(self._data) or col >= self.columnCount():
                return None
                
            item = self._data[row]
            column_name = self.header[col] if self.header else item.__table__.columns[col].name
            return str(getattr(item, column_name))
        
        return None
    
    def headerData(self, section, orientation, role:int=Qt.ItemDataRole.DisplayRole):
        """Return header data"""
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if section < len(self.header):
                    return self.header[section]
                else:
                    return f"Column {section}"
            elif orientation == Qt.Orientation.Vertical:
                return str(section + 1)
        return None
    
    def flags(self, index):
        """Return item flags"""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable

    def setData(self, index, value, role:int=Qt.ItemDataRole.EditRole, persist:bool=False):
        """Set data at index"""
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
        
        row, col = index.row(), index.column()
        
        if row >= len(self._data) or col >= self.columnCount():
            return False
            
        item = self._data[row]
        column_name = self.header[col] if self.header else item.__table__.columns[col].name
        
        setattr(item, column_name, value)
        self._dirty.add((row, col))        # mark dirty

        if persist:
            with self.session_factory() as session:
                session.add(item)  # re-attach item to session
                session.commit()
                session.expunge(item)  # detach again
        # endif persist

        self.dataChanged.emit(index, index)
        return True

    def save_changes(self):
        with self.session_factory() as session:
            for row in self._data:
                session.merge(row)   # re-attach changes
            session.commit()
        self._dirty.clear()

    def insertRow(self, row, parent:QModelIndex | QPersistentModelIndex=QModelIndex(), persist:bool = False):
        """Insert a new row"""
        self.beginInsertRows(parent, row, row)
        new_item = self.model_class()  # Create new instance with default values
        if not persist:
            self._data.insert(row, new_item)
            self.endInsertRows()
            return True
        #endif
        
        # persist=True if we reach here
        try:
            with self.session_factory() as session:
                session.add(new_item)
                session.flush()  # to get any defaults set by the DB
                session.expunge(new_item)  # detach from session
                self._data.insert(row, new_item)
                session.commit()
            self.endInsertRows()
            return True
        except Exception as e:
            self.endInsertRows()
            print(f"Error inserting row: {e}")
            return False
    
    def removeRow(self, row, parent:QModelIndex | QPersistentModelIndex=QModelIndex()):
        """Remove a row"""
        if row < 0 or row >= len(self._data):
            return False
            
        self.beginRemoveRows(parent, row, row)
        item = self._data.pop(row)
        try:
            with self.session_factory() as session:
                session.delete(session.merge(item))
                session.commit()
            self.endRemoveRows()
            return True
        except Exception as e:
            self._data.insert(row, item)  # Reinsert if failed
            self.endRemoveRows()
            print(f"Error removing row: {e}")
            return False

    def record(self, row:int|None = None):
        """Return the record at the specified row"""
        if row is None:
            return self.header
        if 0 <= row < len(self._data):
            return self._data[row]
        return None
    
    def findData(self, value:Any, role:int=Qt.ItemDataRole.DisplayRole) -> int:
        """Find the index of the first occurrence of value in the model"""
        for row in range(self.rowCount()):
            if self.data(self.index(row, 0), role) == value:
                return row
        return -1
    
    def findColumn(self, column_name:str) -> int:
        """Find the index of the specified column name"""
        if self.header:
            try:
                return self.header.index(column_name)
            except ValueError:
                return -1
        return -1
    
    def getDataAsList(self) -> List[Dict[str, Any]]:
        """Return the data as a list of dictionaries"""
        return [{col: getattr(item, col) for col in self.header} for item in self._data]

    # is this needed?    
    def getDataAsDict(self) -> Dict[str, Any]:
        """Return the data as a dictionary with keys as column names and values as lists of column values"""
        data_dict = {col: [] for col in self.header}
        for item in self._data:
            for col in self.header:
                data_dict[col].append(getattr(item, col))
        return data_dict

    def getSQLStatement(self) -> str:
        """Return the SQL query string used to fetch the data."""
        try:
            stmt = select(self.model_class)
            compiled = stmt.compile(dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True})
            return str(compiled)
        except Exception as e:
            print(f"Error compiling SQL statement: {e}")
            return ""

    def isDirty(self, row, col) -> bool:
        return (row, col) in self._dirty

    def clearDirty(self, row:int|None = None, col:int|None = None):
        if row is not None and col is not None:
            self._dirty.discard((row, col))
        elif row is not None:
            self._dirty = {d for d in self._dirty if d[0] != row}
        elif col is not None:
            self._dirty = {d for d in self._dirty if d[1] != col}
        else:
            self._dirty.clear()

class SQLAlchemySQLQueryModel(QAbstractTableModel):
    def __init__(self, sql: str, engine: Engine, parent=None):
        super().__init__(parent)
        self.sql = sql
        self.engine = engine
        self.header: List[str] = []
        self._data: List[List[Any]] = []
        self.refresh()

    def refresh(self):
        self.beginResetModel()
        with self.engine.connect() as conn:
            result = conn.execute(sqlalchemy.text(self.sql))
            self.header = list(result.keys())
            self._data = [list(row) for row in result.fetchall()]
        self.endResetModel()

    def rowCount(self, parent: QModelIndex|QPersistentModelIndex = QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent: QModelIndex|QPersistentModelIndex = QModelIndex()) -> int:
        return len(self.header)

    def data(self, index: QModelIndex|QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != int(Qt.ItemDataRole.DisplayRole):
            return None
        row = index.row()
        column = index.column()
        if 0 <= row < len(self._data) and 0 <= column < len(self.header):
            return self._data[row][column]
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role != int(Qt.ItemDataRole.DisplayRole):
            return None
        if orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self.header):
                return self.header[section]
            return f"Column {section}"
        elif orientation == Qt.Orientation.Vertical:
            return str(section + 1)
        return None
    
    def query(self) -> str:
        """Return the last executed SQL query."""
        return self.sql
    
    def record(self, row: int | None = None) -> Any:
        """Return the record at the specified row."""
        if row is not None and 0 <= row < len(self._data):
            return self._data[row]
        return None

    def colIndex(self, colName: str) -> int:
        """Return the index of the specified column name."""
        if colName in self.header:
            return self.header.index(colName)
        return -1
    
    def save_changes(self):
        pleaseWriteMe(self.parent(), 'SQLAlchemySQLQueryModel does not support saving changes directly.')
        # with self.session_factory() as session:
        #     for row in self._data:
        #         session.merge(row)   # re-attach changes
        #     session.commit()
        # self._dirty.clear()

