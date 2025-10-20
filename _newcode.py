# import sys

# from functools import partial
from typing import (Callable, List, Dict, Type, Any, )

from PySide6.QtCore import (
    Qt, QModelIndex,
    )
from PySide6.QtGui import (
    QIcon,
    )
from PySide6.QtWidgets import (
    QWidget,
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QDateEdit, QCheckBox, QLabel, 
    QPushButton,
    QTableView, QStyledItemDelegate, QItemDelegate,
    QLayout, QBoxLayout, QVBoxLayout, QHBoxLayout, QGridLayout,
    )
import qtawesome

from sqlalchemy import (
    literal, 
    )
from sqlalchemy.orm import (
    sessionmaker, Session,
    )

from cMenu.utils import (
    SQLAlchemyTableModel,
    cSimpleRecordForm, 
    cDataList,
    cComboBoxFromDict,
    get_primary_key_column,
    )

from cMenu.utils.cQdbFormWidgets import cSimpleRecordSubForm2

class cSimpleFormBase(QWidget):
    _ORMmodel:Type[Any]|None = None
    _primary_key: Any
    _ssnmaker:sessionmaker[Session]|None = None
    pages: List = []
    fieldDefs: Dict[str, Dict[str, Any]] = {}

    def __init__(self, 
        model: Type[Any]|None = None, 
        ssnmaker: sessionmaker[Session] | None = None, 
        
        parent: QWidget | None = None
        ):
        # super init
        super().__init__(parent)
 
        # set model, primary key
        if not self._ORMmodel:
            if not model:
                raise ValueError("A model class must be provided either in the constructor or as a class attribute")
            self.setORMmodel(model)

        # set ssnmaker
        if not self._ssnmaker:
            if not ssnmaker:
                raise ValueError("A sessionmaker must be provided either in the constructor or as a class attribute")
            self.setssnmaker(ssnmaker)

        self.layoutMain = self._buildFormLayout()

        # Let subclass build its widgets into self.layoutForm
        self._placeFields()

        # Add buttons
        self._addActionButtons()

        # Finalize layout
        self.layoutMain = self._finalizeMainLayout()

        self.initialdisplay()

    # __init__

       
    
    def ORMmodel(self):
        return self._ORMmodel
    def setORMmodel(self, model):
        self._ORMmodel = model
        self.setPrimary_key()
    def primary_key(self):
        return self._primary_key
    def setPrimary_key(self):
        model = self.ORMmodel()
        if model is None:
            raise Exception('ORMmodel must be set first')
        # model is now narrowed to a non-None Type[Any]
        self._primary_key = get_primary_key_column(model)
    # get/set ORFMmodel/primary_key

    def ssnmaker(self):
        return self._ssnmaker
    def setssnmaker(self,ssnmaker):
        self._ssnmaker = ssnmaker
    # get/set ssnmaker
        
    def _buildFormLayout(self) -> QBoxLayout:   # return tuple ? (layoutMain, layoutForm, layoutButtons)
        raise NotImplementedError

        # layoutMain = QVBoxLayout(self)
        # self.layoutForm = QGridLayout()
        # self.layoutButtons = QHBoxLayout()  # may get redefined in _addActionButtons
        # self._statusBar = QStatusBar(self)

        # self.layoutFormHdr = QHBoxLayout()
        # lblFormName = cQFmNameLabel(self.tr(self._formname), self)
        # self.layoutFormHdr.addWidget(lblFormName)
        
        # self._newrecFlag = QLabel("New Record", self)
        # fontNewRec = QFont()
        # fontNewRec.setBold(True)
        # fontNewRec.setPointSize(10)
        # fontNewRec.setItalic(True)
        # self._newrecFlag.setFont(fontNewRec)
        # self._newrecFlag.setStyleSheet("color: red;")
        # self.layoutFormHdr.addWidget(self._newrecFlag)
        # self._newrecFlag.setVisible(False)
        
        # self.setWindowTitle(self.tr(self._formname))
        
        return layoutMain
    # _buildFormLayout
    
    def _placeFields(self):
        pass
    # _placeFields

    def _addActionButtons(self):
        pass
    # _addActionButtons
        
    def _finalizeMainLayout(self):
        assert isinstance(self.layoutMain, QBoxLayout), 'layoutMain must be a Box Layout'
        
        lyout = getattr(self, 'layoutFormHdr', None)
        if isinstance(lyout, QLayout):
            self.layoutMain.addLayout(lyout)
        lyout = getattr(self, 'layoutForm', None)
        if isinstance(lyout, QLayout):
            self.layoutMain.addLayout(lyout)
        lyout = getattr(self, 'layoutButtons', None)
        if isinstance(lyout, QLayout):
            self.layoutMain.addLayout(lyout)
        lyout = getattr(self, '_statusBar', None)
        if isinstance(lyout, QLayout):
            self.layoutMain.addLayout(lyout)            #TODO: more flexibility in where status bar is placed

    # _finalizeMainLayout
        
    def initialdisplay(self):
        self.initializeRec()
        self.on_loadfirst_clicked()
        
        self.showNewRecordFlag(self.isNewRecord())
    # initialdisplay()

# cSimpleFormBase

################# may not be needed ...
#######################################

####  New table model and delegate using column definitions  #####
####  to define columns, rather than reflecting the ORM model  #####
# may not be needed, but here for reference

# class SQLAlcColDefTblModel(SQLAlchemyTableModel):
#     def __init__(self, model_class:Type[Any], session_factory:sessionmaker, filter = None, orderby = None, colDef:List|None = None, parent=None):
#         super().__init__(model_class, session_factory, filter, orderby, parent)

#         self._colMeta = getattr(self, '_colDef', colDef)      # class attribute takes precedence
#         if not self._colMeta:
#             raise ValueError("Column definitions must be provided either in the constructor or as a class attribute")
#         assert isinstance(self._colMeta, list), "_colMeta must be a list of dictionaries"
#         self._setupColumns()

#     def _setupColumns(self):
#         """Set up columns based on _colMeta."""
#         assert isinstance(self._colMeta, list), "_colMeta must be a list of dictionaries"
#         return
#     # _setupColumns
    
#     def columnCount(self, parent=QModelIndex()):
#         assert isinstance(self._colMeta, list), "_colMeta must be a list of dictionaries"
#         return len(self._colMeta)

#     def data(self, index, role=Qt.ItemDataRole.DisplayRole):
#         if not index.isValid():
#             return None

#         assert isinstance(self._colMeta, list), "_colMeta must be a list of dictionaries"
#         colInfo = self._colMeta[index.column()]
#         field = colInfo.get("field")
#         row = self._data[index.row()]
#         if (role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole) and field:
#             return getattr(row, field, "")
#         return None

#     def headerData(self, section, orientation, role:int=Qt.ItemDataRole.DisplayRole):
#         if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
#             assert isinstance(self._colMeta, list), "_colMeta must be a list of dictionaries"
#             return self._colMeta[section].get("field", "")
#         return super().headerData(section, orientation, role)

#     def flags(self, index):
#         if not index.isValid():
#             return Qt.ItemFlag.NoItemFlags
#             # return Qt.ItemFlag.ItemIsEnabled
#         assert isinstance(self._colMeta, list), "_colMeta must be a list of dictionaries"
#         colInfo = self._colMeta[index.column()]
#         flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
#         if not colInfo.get("readonly", False) and colInfo.get("field"):
#             flags |= Qt.ItemFlag.ItemIsEditable
#         return flags

#     def setData(self, index, value, role=Qt.ItemDataRole.EditRole, persist:bool=False):
#         if not index.isValid() or role != Qt.ItemDataRole.EditRole:
#             return False

#         assert isinstance(self._colMeta, list), "_colMeta must be a list of dictionaries"
#         colInfo = self._colMeta[index.column()]
#         field = colInfo.get("field")
#         item = self._data[index.row()]
#         if field and not colInfo.get("readonly", False):
#             setattr(item, field, value)
#             self._dirty.add((index.row(), index.column()))

#             if persist:
#                 with self.session_factory() as session:
#                     session.add(item)  # re-attach item to session
#                     session.commit()
#                     session.expunge(item)  # detach again
#             # endif persist
            
#             self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
#             return True
#         return False


# class cColDefOmniDelegate(QStyledItemDelegate):
#     Value: List[Callable[[], Any]] = []
#     setValue: List[Callable[[Any], None]] = []
#     addChoices: List[Callable[[dict], None]] = []
#     replaceDict: List[Callable[[dict], None]] = []
    
    
#     def __init__(self, colDef:List|None = None, parent=None):
#         super().__init__(parent)

#         if isinstance(parent, QTableView) and isinstance(parent.model(), SQLAlcColDefTblModel):
#             self._colMeta = getattr(parent.model(), '_colMeta', [])
#         else:
#             self._colMeta = getattr(self, '_colDef', colDef)      # class attribute takes precedence
#             if not self._colMeta:
#                 self._colMeta = []
#     # __init__
            
    
#     def _setTextstring(self, widget: QWidget, text: Any) -> None:
#         """If the widget has a setText method, call it with a string."""
#         setter = getattr(widget, "setText", None)
#         if callable(setter):
#             setter('' if text is None else str(text))  # cast to str to be safe
#     # _setTextstring

#     def _process_datalist(self, op, index = None, widgType = None, colInfo = None, editor = None, model = None) -> Any:
#         """Process cDataList widgets."""
#         if op == 'createEditor':
#             assert colInfo is not None, "Column info must be provided"
#             assert issubclass(widgType, cDataList), "Expected a cDataList widget"    # type: ignore
#             wdgt = widgType(colInfo.get("choices", {}), '')
#             return wdgt
#         elif op == 'setEditorData':
#             assert isinstance(index, QModelIndex), "index must be provided"
#             assert isinstance(editor, cDataList), "Expected a cDataList widget"
#             value = index.model().data(index, Qt.ItemDataRole.DisplayRole)
#             editor.setChoice(value)
#             return
#         elif op == 'setModelData':
#             assert isinstance(index, QModelIndex), "index must be provided"
#             assert isinstance(editor, cDataList), "Expected a cDataList widget"
#             assert isinstance(model, SQLAlchemyTableModel), "Expected a SQLAlchemyTableModel"
#             val = editor.selectedItem()['keys']
#             if val:
#                 model.setData(index, val[0], Qt.ItemDataRole.EditRole)
#             return
#         else:
#             raise ValueError(f"Unknown operation '{op}'")
#         # endif op
#     # process_datalist
    
#     def _process_lineedit(self, op, index = None, widgType = None, colInfo = None, editor = None, model = None) -> Any:
#         """Process QLineEdit widgets."""
#         if op == 'createEditor':
#             assert issubclass(widgType, QLineEdit), "Expected a QLineEdit widget"    # type: ignore
#             wdgt = widgType()
#             return wdgt
#         elif op == 'setEditorData':
#             assert isinstance(index, QModelIndex), "index must be provided"
#             assert isinstance(editor, QLineEdit), "Expected a QLineEdit widget"
#             value = index.model().data(index, Qt.ItemDataRole.DisplayRole)
#             editor.setText(value)
#             return
#         elif op == 'setModelData':
#             assert isinstance(index, QModelIndex), "index must be provided"
#             assert isinstance(editor, QLineEdit), "Expected a QLineEdit widget"
#             assert isinstance(model, SQLAlchemyTableModel), "Expected a SQLAlchemyTableModel"
#             val = editor.text()
#             if val:
#                 model.setData(index, val, Qt.ItemDataRole.EditRole)
#             return
#         else:
#             raise ValueError(f"Unknown operation '{op}'")
#         # endif op
#     # process_lineedit

#     def _process_label(self, op, index = None, widgType = None, colInfo = None, editor = None, model = None) -> Any:
#         """Process QLabel widgets."""
#         if op == 'createEditor':
#             assert issubclass(widgType, QLabel), "Expected a QLabel widget"    # type: ignore
#             wdgt = widgType()
#             return wdgt
#         elif op == 'setEditorData':
#             assert isinstance(index, QModelIndex), "index must be provided"
#             assert isinstance(editor, QLabel), "Expected a QLabel widget"
#             value = index.model().data(index, Qt.ItemDataRole.DisplayRole)
#             editor.setText(value)
#             return
#         elif op == 'setModelData':
#             assert isinstance(index, QModelIndex), "index must be provided"
#             assert isinstance(editor, QLabel), "Expected a QLabel widget"
#             assert isinstance(model, SQLAlchemyTableModel), "Expected a SQLAlchemyTableModel"
#             val = editor.text()
#             if val:
#                 model.setData(index, val, Qt.ItemDataRole.EditRole)
#             return
#         else:
#             raise ValueError(f"Unknown operation '{op}'")
#         # endif op
#     # process_label

#     def _process_textedit(self, op, index = None, widgType = None, colInfo = None, editor = None, model = None) -> Any:
#         """Process text edit widgets."""
#         if op == 'createEditor':
#             assert issubclass(widgType, (QTextEdit, QPlainTextEdit)), "Expected a QTextEdit or QPlainTextEdit widget"    # type: ignore
#             wdgt = widgType()
#             return wdgt
#         elif op == 'setEditorData':
#             assert isinstance(index, QModelIndex), "index must be provided"
#             assert isinstance(editor, (QTextEdit, QPlainTextEdit)), "Expected a QTextEdit or QPlainTextEdit widget"
#             value = index.model().data(index, Qt.ItemDataRole.DisplayRole)
#             editor.setPlainText(value)
#             return
#         elif op == 'setModelData':
#             assert isinstance(index, QModelIndex), "index must be provided"
#             assert isinstance(editor, (QTextEdit, QPlainTextEdit)), "Expected a QTextEdit or QPlainTextEdit widget"
#             assert isinstance(model, SQLAlchemyTableModel), "Expected a SQLAlchemyTableModel"
#             val = editor.toPlainText()
#             if val:
#                 model.setData(index, val, Qt.ItemDataRole.EditRole)
#             return
#         else:
#             raise ValueError(f"Unknown operation '{op}'")
#         # endif op
#     # process_textedit

#     # def _create_combobox_setter(self, wdgt:cComboBoxFromDict|QComboBox|QWidget) -> Callable[[Any], None]:
#     #     """Create a type-safe setter function for combo boxes."""
#     #     if not isinstance(wdgt, (cComboBoxFromDict, QComboBox)):
#     #         raise TypeError("Expected a cComboBoxFromDict or QComboBox widget")
#     #     def set_combobox_value(value: Any) -> None:
#     #         if wdgt.findData(value) == -1:
#     #             wdgt.setCurrentText(str(value))
#     #         else:
#     #             wdgt.setCurrentIndex(wdgt.findData(value))
#     #     return set_combobox_value
#     # # _create_combobox_setter
#     def _process_combobox(self, op, index = None, widgType = None, colInfo = None, editor = None, model = None) -> Any:
#         """Process combo box widgets."""
#         if op == 'createEditor':
#             assert issubclass(widgType, (cComboBoxFromDict, QComboBox)), "Expected a cComboBoxFromDict or QComboBox widget"    # type: ignore
#             assert colInfo is not None, "Column info must be provided"
#             if issubclass(widgType, cComboBoxFromDict):
#                 choices = colInfo.get("choices", {})
#                 wdgt = widgType(choices)
#             else:
#                 wdgt = widgType()
#             return wdgt
#         elif op == 'setEditorData':
#             assert isinstance(index, QModelIndex), "index must be provided"
#             assert isinstance(editor, (cComboBoxFromDict, QComboBox)), "Expected a cComboBoxFromDict or QComboBox widget"
#             value = index.model().data(index, Qt.ItemDataRole.DisplayRole)
#             i = editor.findText(value)
#             if i >= 0:
#                 editor.setCurrentIndex(i)
#             return
#         elif op == 'setModelData':
#             assert isinstance(index, QModelIndex), "index must be provided"
#             assert isinstance(editor, (cComboBoxFromDict, QComboBox)), "Expected a cComboBoxFromDict or QComboBox widget"
#             assert isinstance(model, SQLAlchemyTableModel), "Expected a SQLAlchemyTableModel"
#             model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)
#             return
#         else:
#             raise ValueError(f"Unknown operation '{op}'")
#         # endif op
#     # process_combobox

#     def _process_dateedit(self, op, index = None, widgType = None, colInfo = None, editor = None, model = None) -> Any:
#         """Process date edit widgets."""
#         if op == 'createEditor':
#             assert issubclass(widgType, QDateEdit), "Expected a QDateEdit widget"    # type: ignore
#             wdgt = widgType()
#             return wdgt
#         elif op == 'setEditorData':
#             assert isinstance(index, QModelIndex), "index must be provided"
#             assert isinstance(editor, QDateEdit), "Expected a QDateEdit widget"
#             value = index.model().data(index, Qt.ItemDataRole.DisplayRole)
#             editor.setDate(value)
#             return
#         elif op == 'setModelData':
#             assert isinstance(index, QModelIndex), "index must be provided"
#             assert isinstance(editor, QDateEdit), "Expected a QDateEdit widget"
#             assert isinstance(model, SQLAlchemyTableModel), "Expected a SQLAlchemyTableModel"
#             val = editor.date().toPython()
#             if val:
#                 model.setData(index, val, Qt.ItemDataRole.EditRole)
#             return
#         else:
#             raise ValueError(f"Unknown operation '{op}'")
#         # endif op
#     # process_dateedit

#     def _process_checkbox(self, op, index = None, widgType = None, colInfo = None, editor = None, model = None) -> Any:
#         """Process checkbox widgets."""
#         if op == 'createEditor':
#             assert issubclass(widgType, QCheckBox), "Expected a QCheckBox widget"    # type: ignore
#             wdgt = widgType()
#             return wdgt
#         elif op == 'setEditorData':
#             assert isinstance(index, QModelIndex), "index must be provided"
#             assert isinstance(editor, QCheckBox), "Expected a QCheckBox widget"
#             value = index.model().data(index, Qt.ItemDataRole.DisplayRole)
#             editor.setChecked(value)
#             return
#         elif op == 'setModelData':
#             assert isinstance(index, QModelIndex), "index must be provided"
#             assert isinstance(editor, QCheckBox), "Expected a QCheckBox widget"
#             assert isinstance(model, SQLAlchemyTableModel), "Expected a SQLAlchemyTableModel"
#             val = editor.isChecked()
#             model.setData(index, val, Qt.ItemDataRole.EditRole)
#             return
#         else:
#             raise ValueError(f"Unknown operation '{op}'")
#         # endif op
#     # process_checkbox
    
#     def _process_pushbutton(self, op, index = None, widgType = None, colInfo = None, editor = None, model = None) -> Any:
#         """Process push button widgets."""
#         if op == 'createEditor':
#             assert issubclass(widgType, QPushButton), "Expected a QPushButton widget"    # type: ignore
#             assert isinstance(index, QModelIndex), "index must be provided"
#             assert colInfo is not None, "Column info must be provided"
#             btn = widgType(colInfo.get("btnText", "Button"))
#             slotName = colInfo.get("btnSlot")
#             if slotName and hasattr(self.parent(), slotName):
#                 btn.clicked.connect(lambda _, row=index.row(): getattr(self.parent(), slotName)(row))

#             return btn
#         elif op == 'setEditorData':
#             # assert isinstance(index, QModelIndex), "index must be provided"
#             # assert isinstance(editor, QPushButton), "Expected a QPushButton widget"
#             # value = index.model().data(index, Qt.ItemDataRole.DisplayRole)
#             # editor.setChecked(value)
#             return
#         elif op == 'setModelData':
#             # assert isinstance(index, QModelIndex), "index must be provided"
#             # assert isinstance(editor, QPushButton), "Expected a QPushButton widget"
#             # assert isinstance(model, SQLAlchemyTableModel), "Expected a SQLAlchemyTableModel"
#             # val = editor.isChecked()
#             # model.setData(index, val, Qt.ItemDataRole.EditRole)
#             return
#         else:
#             raise ValueError(f"Unknown operation '{op}'")
#         # endif op
#     # process_pushbutton

#     def createEditor(self, parent, option, index) -> QWidget|None: # type: ignore
#         """Configure widget-specific behaviors with proper type checking."""
#         assert isinstance(self._colMeta, list), "_colMeta must be a list of dictionaries"
#         colNum = index.column()
#         colInfo = self._colMeta[colNum]

#         if colInfo.get("readonly", False):
#             return None

#         widgType = colInfo.get("widgetType", QLineEdit)
#         op = 'createEditor'
        
#         if   issubclass(widgType, cDataList):
#             editor = self._process_datalist(op, index=index, widgType=widgType, colInfo=colInfo)
#         elif issubclass(widgType, QLineEdit):
#             editor = self._process_lineedit(op, index=index, widgType=widgType, colInfo=colInfo)
#         elif issubclass(widgType, (QTextEdit, QPlainTextEdit)):
#             editor = self._process_textedit(op, index=index, widgType=widgType, colInfo=colInfo)
#         elif issubclass(widgType, (cComboBoxFromDict, QComboBox)):
#             editor = self._process_combobox(op, index=index, widgType=widgType, colInfo=colInfo)
#         elif issubclass(widgType, QDateEdit):
#             editor = self._process_dateedit(op, index=index, widgType=widgType, colInfo=colInfo)
#         elif issubclass(widgType, QCheckBox):
#             editor = self._process_checkbox(op, index=index, widgType=widgType, colInfo=colInfo)
#         elif issubclass(widgType, QLabel):
#             editor = self._process_label(op, index=index, widgType=widgType, colInfo=colInfo)
#         elif issubclass(widgType, QPushButton):
#             editor = self._process_pushbutton(op, index=index, widgType=widgType, colInfo=colInfo)
#         else:
#             editor = super().createEditor(parent, option, index)
#         #endif widget type

#         return editor
#     # createEditor

#     def setEditorData(self, editor, index):
#         op = 'setEditorData'

#         if   isinstance(editor, cDataList):
#             self._process_datalist(op, index=index, editor=editor)
#         elif isinstance(editor, QLineEdit):
#             self._process_lineedit(op, index=index, editor=editor)
#         elif isinstance(editor, (QTextEdit, QPlainTextEdit)):
#             self._process_textedit(op, index=index, editor=editor)
#         elif isinstance(editor, (cComboBoxFromDict, QComboBox)):
#             self._process_combobox(op, index=index, editor=editor)
#         elif isinstance(editor, QDateEdit):
#             self._process_dateedit(op, index=index, editor=editor)
#         elif isinstance(editor, QCheckBox):
#             self._process_checkbox(op, index=index, editor=editor)
#         elif isinstance(editor, QLabel):
#             self._process_label(op, index=index, editor=editor)
#         elif isinstance(editor, QPushButton):
#             self._process_pushbutton(op, index=index, editor=editor)
#         else:
#             super().setEditorData(editor, index)
#         #endif editor type
#     # setEditorData

#     def setModelData(self, editor, model, index):
#         if isinstance(editor, QComboBox):
#             model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)
#         else:
#             super().setModelData(editor, model, index)

#         op = 'setModelData'
#         if   isinstance(editor, cDataList):
#             self._process_datalist(op, index=index, editor=editor, model=model)
#         elif isinstance(editor, QLineEdit):
#             self._process_lineedit(op, index=index, editor=editor, model=model)
#         elif isinstance(editor, (QTextEdit, QPlainTextEdit)):
#             self._process_textedit(op, index=index, editor=editor, model=model)
#         elif isinstance(editor, (cComboBoxFromDict, QComboBox)):
#             self._process_combobox(op, index=index, editor=editor, model=model)
#         elif isinstance(editor, QDateEdit):
#             self._process_dateedit(op, index=index, editor=editor, model=model)
#         elif isinstance(editor, QCheckBox):
#             self._process_checkbox(op, index=index, editor=editor, model=model)
#         elif isinstance(editor, QLabel):
#             self._process_label(op, index=index, editor=editor, model=model)
#         elif isinstance(editor, QPushButton):
#             self._process_pushbutton(op, index=index, editor=editor, model=model)
#         else:
#             super().setEditorData(editor, index)
#         #endif editor type


# class TblViewWithColDef(QTableView):
#     _colMeta = []

#     def __init__(self, colDef:List|None = None, parent=None):
#         super().__init__(parent)

#         if isinstance(parent, cSimpleRecordSubForm2):
#             self._colMeta = getattr(parent, '_colDef', [])
#         else:
#             self._colMeta = getattr(self, '_colDef', colDef)      # class attribute takes precedence
#             if not self._colMeta:
#                 self._colMeta = []

#         self.setItemDelegate(cColDefOmniDelegate(colDef=self._colMeta, parent=self))
#         self._setupColumns()
        
#     def _setupColumns(self):
#         """Set up columns based on _colMeta."""
#         assert isinstance(self._colMeta, list), "_colMeta must be a list of dictionaries"
#         for i, colInfo in enumerate(self._colMeta):
#             if not isinstance(colInfo, dict):
#                 raise TypeError("Each column definition must be a dictionary")
#             if all( ['field' not in colInfo, 'colmn' not in colInfo] ):
#                 raise ValueError("Each column definition must include a 'field' or 'colmn' key")
#             # handle adding colmn fields here?
#             if colInfo.get('hidden', False):
#                 self.setColumnHidden(i, True)
#         # endfor
#     # _setupColumns
# #endclass TblViewWithColDef
    



