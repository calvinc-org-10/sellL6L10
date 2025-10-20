from typing import (Dict, List, Any, Type, )
from collections.abc import (Callable, )
from functools import (partial, )

from PySide6.QtCore import (
    Qt, Slot, Signal, 
    )
from PySide6.QtGui import (
    QFont, QIcon, 
    )
from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QWidget,
    QFrame, QVBoxLayout, QHBoxLayout, QGridLayout, QLayoutItem, 
    QMessageBox, 
    QTableView, QHeaderView, 
    QLabel, QLineEdit,  QComboBox, QPushButton, QCheckBox, QTextEdit, QPlainTextEdit, QDateEdit, 
    QStatusBar, 
    )
import qtawesome

from sqlalchemy import (select, inspect, func, literal, )
from sqlalchemy.orm import (Session, sessionmaker, )

from .cQModels import (SQLAlchemyTableModel, )
from .cQWidgets import (cDataList, cComboBoxFromDict, )
from .SQLAlcTools import (get_primary_key_column, )

from app.database import app_Session


class cQFmNameLabel(QLabel):
    def __init__(self, formName:str = '', parent:QWidget|None = None):
        super().__init__(parent)
        
        fontFormTitle = QFont()
        fontFormTitle.setFamilies([u"Copperplate Gothic"])
        fontFormTitle.setPointSize(24)
        self.setFont(fontFormTitle)
        self.setFrameShape(QFrame.Shape.Panel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        
        if formName:
            self.setText(formName)

# TODO: implement editing
# deprecate? see subform widget 
class cSimpleTableForm(QWidget):
    _tbl = None
    _formname = None
    _ssnmaker: sessionmaker[Session]

    # TODO: pass in sessionmaker
    def __init__(self, 
        formname: str|None = None, 
        tbl: Type[Any]|None = None, 
        ssnmaker: sessionmaker[Session] = app_Session, 
        parent: QWidget|None = None
        ):
        """Initialize the SimpleTableForm.

        Args:
            formname (str): The name of the form.
            tbl (Type[Any]): The SQLAlchemy model class for the table.
            parent (QWidget | None, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)

        if formname:
            self._formname = formname
        if tbl:
            self._tbl = tbl
        if ssnmaker:
            self._ssnmaker = ssnmaker

        # Layout
        layoutForm = QVBoxLayout(self)

        layoutFormHdr = QHBoxLayout()
        lblFormName = cQFmNameLabel(parent=self)
        lblFormName.setText(self.tr(str(self._formname)))
        layoutFormHdr.addWidget(lblFormName)
        self.setWindowTitle(self.tr(str(self._formname)))

        # Setup model
        assert self._tbl, "Table model class must be provided"
        self.model = SQLAlchemyTableModel(self._tbl, ssnmaker)
        # self.model.setEditStrategy(QSqlTableModel.OnFieldChange)

        # Setup view
        layoutFormMain = QGridLayout()
        tableView = QTableView()
        header = tableView.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        # Apply stylesheet to control text wrapping
        tableView.setStyleSheet("""
        QHeaderView::section {
            padding: 5px;
            font-size: 12px;
            text-align: center;
            white-space: normal;  /* Allow text to wrap */
        }
        """)
        tableView.setModel(self.model)
        tableView.setEditTriggers(QTableView.EditTrigger.DoubleClicked | QTableView.EditTrigger.EditKeyPressed)
        rows = tableView.model().rowCount()
        colNames = [tableView.model().headerData(n, Qt.Orientation.Horizontal) for n in range(tableView.model().columnCount())]
        # tableView.resizeColumnsToContents()
        layoutFormMain.addWidget(tableView,0,0)

        # Add a add button
        addrow_button = QPushButton("Add Row")
        addrow_button.clicked.connect(lambda: self.addRow())

        # Add a save button
        save_button = QPushButton("Save Changes")
        save_button.clicked.connect(lambda: self.saveRow())

        layoutButtons = QHBoxLayout()
        layoutButtons.addWidget(addrow_button)
        layoutButtons.addWidget(save_button)

        layoutForm.addLayout(layoutFormHdr)
        layoutForm.addLayout(layoutFormMain)
        layoutForm.addLayout(layoutButtons)

    def addRow(self):
        self.model.insertRow(self.model.rowCount())

    def saveRow(self):
        self.model.save_changes()
        print("Saved!")
# endclass cSimpleTableForm

############################################################
############################################################
############################################################
############################################################


class cSimpRecFmElement_Base(QWidget):
    signalFldChanged: Signal = Signal(object)
    dirtyChanged = Signal(bool)
    
    def loadFromRecord(self, rec: object) -> None:
        """Fill widget from ORM record."""
        raise NotImplementedError

    def saveToRecord(self, rec: object) -> None:
        """Push widget state into ORM record."""
        raise NotImplementedError

    def isDirty(self) -> bool:
        """Return True if the widget's value differs from what was loaded."""
        return False

    def setDirty(self, dirty: bool = True, sendSignal:bool = True) -> None:
        """Mark the field/subform as dirty."""
        pass
# endclass cSimpRecFmElement_Base

###########################################
# Improved cQFmFldWidg Class with Type Safety

class cQFmFldWidg(cSimpRecFmElement_Base):
    _wdgt: QWidget
    _label: QLabel|QCheckBox|None = None
    _labelSetLblText: Callable[[str], None]|None = None
    _modlField: str = ''
    _lblChkYN: QLineEdit|None = None
    _lblChkYNValues: Dict[bool, str]|None = None

    # signalFldChanged: Signal = Signal(object)
    # dirtyChanged = Signal(bool)

    def __init__(
        self,
        widgType: Type[QWidget],
        lblText: str = ' ',
        lblChkBxYesNo: Dict[bool, str]|None = None,
        alignlblText: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft,
        modlFld: str = '',
        choices: Dict|List|None = None,
        initval: str = '',
        parent: QWidget|None = None,
    ):
        super().__init__(parent)
        
        # Create the widget with proper typing
        self._wdgt = self.createWidget(widgType, choices, initval)
        lblText = self.tr(lblText)
        
        # Set up widget-specific behaviors with proper type checking
        self._setup_widget_behavior(widgType, lblText, lblChkBxYesNo)
        
        # Set the ModelField
        self.setModelField(modlFld)
        
        # Set up the layout
        self._setup_layout(widgType, lblText, alignlblText, lblChkBxYesNo)
    # __init__

    def _setup_widget_behavior(
        self,
        widgType: Type[QWidget],
        lblText: str,
        lblChkBxYesNo: Dict[bool, str]|None = None
    ) -> None:
        """Configure widget-specific behaviors with proper type checking."""
        wdgt = self._wdgt
        
        if issubclass(widgType, cDataList):
            self._setup_datalist_behavior(wdgt, lblText)
        elif issubclass(widgType, QLineEdit):
            self._setup_lineedit_behavior(wdgt, lblText)
        elif issubclass(widgType, (QTextEdit, QPlainTextEdit)):
            self._setup_textedit_behavior(wdgt, lblText)
        elif issubclass(widgType, (cComboBoxFromDict, QComboBox)):
            self._setup_combobox_behavior(wdgt, lblText)
        elif issubclass(widgType, QDateEdit):
            self._setup_dateedit_behavior(wdgt, lblText)
        elif issubclass(widgType, QCheckBox):
            self._setup_checkbox_behavior(wdgt, lblText, lblChkBxYesNo)
        elif issubclass(widgType, QLabel):
            self._setup_label_behavior(wdgt, lblText)
        else:
            raise TypeError(f'type {widgType} is not implemented')
    # _setup_widget_behavior
    

    def _setTextstring(self, widget: QWidget, text: Any) -> None:
        """If the widget has a setText method, call it with a string."""
        setter = getattr(widget, "setText", None)
        if callable(setter):
            setter('' if text is None else str(text))  # cast to str to be safe
    # _setTextstring

    def _setup_datalist_behavior(self, wdgt: cDataList|QWidget, lblText: str) -> None:
        """Configure behavior for cDataList widgets."""
        if not isinstance(wdgt, cDataList):
            raise TypeError("Expected a cDataList widget")
        self._label = QLabel(lblText)
        self.LabelText = self._label.text
        self._labelSetLblText = partial(self._setTextstring, self._label)
        self._label.setBuddy(wdgt)

        self.Value = wdgt.selectedItem
        # self.setValue = partial(self._setTextstring, wdgt)
        self.setValue = self._create_datalist_setter(wdgt)
        self.addChoices = wdgt.addChoices
        wdgt.editingFinished.connect(self.fldChanged)
    def _create_datalist_setter(self, wdgt:cDataList|QWidget) -> Callable[[Any], None]:
        """Create a type-safe setter function for cDataList."""
        if not isinstance(wdgt, (cDataList, )):
            raise TypeError("Expected a cDataList widget")
        def set_datalist_value(value: Any) -> None:
            # value could be the actual data value, or the display text
            # assume key value first
            if value in wdgt.choices:
                wdgt.setText(wdgt.choices[value])
                return
            elif str(value) in wdgt.choices.values():
                wdgt.setText(str(value))
                return
            else:
                wdgt.setText(str(value))
                return
            #endif
        return set_datalist_value
    # _create_datalist_setter

    def _setup_lineedit_behavior(self, wdgt: QLineEdit|QWidget, lblText: str) -> None:
        """Configure behavior for QLineEdit widgets."""
        if not isinstance(wdgt, QLineEdit):
            raise TypeError("Expected a QLineEdit widget")
        self._label = QLabel(lblText)
        self.LabelText = self._label.text
        self._labelSetLblText = partial(self._setTextstring, self._label)
        self._label.setBuddy(wdgt)

        self.Value = wdgt.text
        self.setValue = partial(self._setTextstring, wdgt)
        wdgt.editingFinished.connect(self.fldChanged)

    def _setup_label_behavior(self, wdgt: QLabel|QWidget, lblText: str) -> None:
        """Configure behavior for QLabel widgets."""
        if not isinstance(wdgt, QLabel):
            raise TypeError("Expected a QLabel widget")
        self._label = QLabel(lblText)
        self.LabelText = self._label.text
        self._labelSetLblText = partial(self._setTextstring, self._label)
        self._label.setBuddy(wdgt)

        self.Value = wdgt.text
        self.setValue = partial(self._setTextstring, wdgt)

    def _setup_textedit_behavior(self, wdgt: QTextEdit|QPlainTextEdit|QWidget, lblText: str) -> None:
        """Configure behavior for text edit widgets."""
        if not isinstance(wdgt, (QTextEdit, QPlainTextEdit)):
            raise TypeError("Expected a QTextEdit or QPlainTextEdit widget")
        self._label = QLabel(lblText)
        self.LabelText = self._label.text
        self._labelSetLblText = partial(self._setTextstring, self._label)
        self._label.setBuddy(wdgt)

        self.Value = wdgt.toPlainText
        self.setValue = wdgt.setPlainText
        wdgt.textChanged.connect(self.fldChanged)

    def _setup_combobox_behavior(self, wdgt: cComboBoxFromDict|QComboBox|QWidget, lblText: str) -> None:
        """Configure behavior for combo box widgets."""
        if not isinstance(wdgt, (cComboBoxFromDict, QComboBox)):
            raise TypeError("Expected a cComboBoxFromDict or QComboBox widget")
        self._label = QLabel(lblText)
        self.LabelText = self._label.text
        self._labelSetLblText = partial(self._setTextstring, self._label)
        self._label.setBuddy(wdgt)

        self.Value = wdgt.currentData
        self.setValue = self._create_combobox_setter(wdgt)
        
        if isinstance(wdgt, cComboBoxFromDict):
            self.replaceDict = wdgt.replaceDict

        wdgt.activated.connect(self.fldChanged)
    def _create_combobox_setter(self, wdgt:cComboBoxFromDict|QComboBox|QWidget) -> Callable[[Any], None]:
        """Create a type-safe setter function for combo boxes."""
        if not isinstance(wdgt, (cComboBoxFromDict, QComboBox)):
            raise TypeError("Expected a cComboBoxFromDict or QComboBox widget")
        def set_combobox_value(value: Any) -> None:
            if wdgt.findData(value) == -1:
                wdgt.setCurrentText(str(value))
            else:
                wdgt.setCurrentIndex(wdgt.findData(value))
        return set_combobox_value

    def _setup_dateedit_behavior(self, wdgt: QDateEdit|QWidget, lblText: str) -> None:
        """Configure behavior for date edit widgets."""
        if not isinstance(wdgt, QDateEdit):
            raise TypeError("Expected a QDateEdit widget")
        self._label = QLabel(lblText)
        self.LabelText = self._label.text
        self._labelSetLblText = partial(self._setTextstring, self._label)
        self._label.setBuddy(wdgt)

        self.Value = lambda: wdgt.date().toPython()
        self.setValue = wdgt.setDate
        wdgt.userDateChanged.connect(self.fldChanged)

    def _setup_checkbox_behavior(
        self,
        wdgt: QCheckBox|QWidget,
        lblText: str,
        lblChkBxYesNo: Dict[bool, str]|None = None
    ) -> None:
        """Configure behavior for checkbox widgets."""
        if not isinstance(wdgt, QCheckBox):
            raise TypeError("Expected a QCheckBox widget")
        self._label = wdgt
        wdgt.setText(lblText)
        self.LabelText = wdgt.text
        self._labelSetLblText = partial(self._setTextstring, wdgt)

        self.Value = wdgt.isChecked
        self.setValue = lambda value: wdgt.setChecked(value if isinstance(value, bool) else False)
        
        if lblChkBxYesNo:
            self._lblChkYNValues = lblChkBxYesNo
            self._lblChkYN = QLineEdit()
            self._lblChkYN.setProperty('noedit', True)
            self._lblChkYN.setReadOnly(True)
            self._lblChkYN.setFrame(False)
            self._lblChkYN.setMaximumWidth(40)
            self._lblChkYN.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        wdgt.checkStateChanged.connect(self.fldChanged)

    def _setup_layout(
        self,
        widgType: Type[QWidget],
        lblText: str,
        alignlblText: Qt.AlignmentFlag,
        lblChkBxYesNo: Dict[bool, str]|None = None
    ) -> None:
        """Configure the layout based on widget type and alignment."""
        layout = QGridLayout()
        
        # Determine widget positions based on alignment
        if alignlblText == Qt.AlignmentFlag.AlignLeft:
            positions = ((0, 0), (0, 1))
        elif alignlblText == Qt.AlignmentFlag.AlignRight:
            positions = ((0, 1), (0, 0))
        elif alignlblText == Qt.AlignmentFlag.AlignTop:
            positions = ((0, 0), (1, 0))
        elif alignlblText == Qt.AlignmentFlag.AlignBottom:
            positions = ((1, 0), (0, 0))
        else:
            positions = ((0, 0), (0, 1))  # default to left
        
        # Place widgets in layout
        if issubclass(widgType, QCheckBox):
            if lblChkBxYesNo and self._lblChkYN:
                layout.addWidget(self._lblChkYN, *positions[0])
                layout.addWidget(self._wdgt, *positions[1])
            else:
                layout.addWidget(self._wdgt, 0, 0)
        else:
            if lblText and self._label:
                layout.addWidget(self._label, *positions[0])
                layout.addWidget(self._wdgt, *positions[1])
            else:
                layout.addWidget(self._wdgt, 0, 0)
        
        self.setLayout(layout)

    def createWidget(
        self,
        widgType: Type[QWidget],
        choices: Dict|List|None = None,
        initval: str = ''
    ) -> QWidget:
        """Create the appropriate widget based on type."""
        if issubclass(widgType, cComboBoxFromDict):
            if not isinstance(choices, dict):
                # raise TypeError("Expected choices to be a dictionary for cComboBoxFromDict")
                choices = {}
            return widgType(choices, self)
        elif issubclass(widgType, cDataList):
            if not isinstance(choices, (dict, )):
                # raise TypeError("Expected choices to be a dictionary or list for cDataList")
                choices = {}
            return widgType(choices, initval, self)
        elif issubclass(widgType, QComboBox):
            wdgt = widgType(self)
            if choices is not None:
                if isinstance(choices, dict):
                    for key, value in choices.items():
                        wdgt.addItem(str(value), key)
                else:
                    wdgt.addItems([str(item) for item in choices])
            return wdgt
        else:
            return widgType(self)
        # endif widgType class
    # createWidget

    def setLabelText(self, txt: str) -> None:
        """Set the label text if a label exists."""
        if self._labelSetLblText is not None:
            self._labelSetLblText(txt)
            if self._label is not None:
                self._label.repaint()

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the contained widget."""
        return getattr(self._wdgt, name, None)

    def modelField(self) -> str:
        """Get the model field name."""
        return self._modlField

    def setModelField(self, fldName: str) -> None:
        """Set the model field name."""
        self._modlField = fldName

    # ------------------------------
    # Internal helpers
    # ------------------------------

    def loadFromRecord(self, rec):
        """Load the ORM record value into the widget."""
        val = getattr(rec, self._modlField, None) if rec else None
        self._last_value = val
        self._setWidgetValue(val)
        self.setDirty(False, sendSignal=False)

    def saveToRecord(self, rec):
        """Write widget value back into ORM record, if dirty."""
        if not self._dirty:
            return
        new_val = self._getWidgetValue()
        setattr(rec, self._modlField, new_val)
        self._last_value = new_val
        self.setDirty(False, sendSignal=False)

    def isDirty(self) -> bool:
        return self._dirty

    def setDirty(self, dirty: bool = True, sendSignal:bool = True) -> None:
        if self._dirty == dirty:
            return
        self._dirty = dirty
        if sendSignal:
            self.dirtyChanged.emit(dirty)

    def _setWidgetValue(self, val):
        """Best-effort assignment based on widget type."""
        self.setValue(val)

    def _getWidgetValue(self):
        """Best-effort retrieval based on widget type."""
        return self.Value()

    @Slot()
    def fldChanged(self, *args: Any) -> None:
        """Handle field change events."""
        if self._lblChkYNValues and self._lblChkYN:
            # Update the check box label if configured
            newstate = (args[0] == Qt.CheckState.Checked) if args else False
            self._lblChkYN.setText(self._lblChkYNValues[newstate])
        
        new_val = self._getWidgetValue()
        self.setDirty(new_val != self._last_value)
        self.signalFldChanged.emit(args if args else (None,))
# endclass cQFmFldWidg

class cQFmLookupWidg(cSimpRecFmElement_Base):
    """
    returns a widget that allows the user to select from a list of values
    returns the text selected, not the key
    
    NOTE: any choices passed in will be overwritten when refreshChoices() is called

    """
    signalLookupSelected: Signal = Signal(object)

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        model: type[Any],
        lookup_field: str,
        lblText: str|None = None,
        alignlblText: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft,
        lookupWidgType: Type[QWidget] = cDataList,
        choices: Dict | None = {},
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._session_factory = session_factory
        self._model = model
        self._lookup_field = lookup_field
        if lblText is None:
            lblText = lookup_field.replace('_', ' ').title()

        # Create the widget with proper typing
        if not issubclass(lookupWidgType, (cComboBoxFromDict, cDataList)):
            lookupWidgType = cDataList  # force it to be a cDataList
        self._wdgt = self.createWidget(lookupWidgType, choices)
        lblText = self.tr(lblText)
        
        # Set up widget-specific behaviors with proper type checking
        self._setup_widget_behavior(lblText)
        
        # Set up the layout
        self._setup_layout(lblText, alignlblText)

        self.refreshChoices()
    # __init__

    def createWidget(self, widgType: Type[QWidget], choices: Dict | None = {}) -> QWidget:
        """Create the widget with the specified type, choices, and initial value."""
        initval = ''
        
        if issubclass(widgType, cDataList):
            if not isinstance(choices, (dict, )):
                # raise TypeError("Expected choices to be a dictionary or list for cDataList")
                choices = {}
            return widgType(choices, initval, self)
        elif issubclass(widgType, cComboBoxFromDict):
            if not isinstance(choices, dict):
                # raise TypeError("Expected choices to be a dictionary for cComboBoxFromDict")
                choices = {}
            return widgType(choices, self)
        else:
            return cDataList({}, '', self)
        # endif widgType class
    # createWidget

    def _setup_widget_behavior(self, lblText: str) -> None:
        """Configure widget-specific behaviors with proper type checking."""
        wdgt = self._wdgt
        widgType = type(wdgt)
        
        if issubclass(widgType, cDataList):
            self._setup_datalist_behavior(wdgt, lblText)
        elif issubclass(widgType, (cComboBoxFromDict, QComboBox)):
            self._setup_combobox_behavior(wdgt, lblText)
        else:
            raise TypeError(f'type {widgType} is not implemented')

    def _create_datalist_setter(self, wdgt:cDataList|QWidget) -> Callable[[Any], None]:
        """Create a type-safe setter function for cDataList."""
        if not isinstance(wdgt, (cDataList, )):
            raise TypeError("Expected a cDataList widget")
        def set_datalist_value(value: Any) -> None:
            # value could be the actual data value, or the display text
            # assume key value first
            if value in wdgt.choices:
                wdgt.setText(wdgt.choices[value])
                return
            elif str(value) in wdgt.choices.values():
                wdgt.setText(str(value))
                return
            else:
                wdgt.setText(str(value))
                return
            #endif
        return set_datalist_value
    # _create_datalist_setter
    def _setup_datalist_behavior(self, wdgt: cDataList|QWidget, lblText: str) -> None:
        """Configure behavior for cDataList widgets."""
        if not isinstance(wdgt, cDataList):
            raise TypeError("Expected a cDataList widget")
        self._label = QLabel(lblText)
        self.LabelText = self._label.text
        self._labelSetLblText = self._label.setText
        self._label.setBuddy(wdgt)

        self.Value = wdgt.selectedItem
        self.setValue = self._create_datalist_setter(wdgt)
        self.addChoices = wdgt.addChoices
        wdgt.editingFinished.connect(self._emitSelection)

    def _create_combobox_setter(self, wdgt:cComboBoxFromDict|QComboBox|QWidget) -> Callable[[Any], None]:
        """Create a type-safe setter function for combo boxes."""
        if not isinstance(wdgt, (cComboBoxFromDict, QComboBox)):
            raise TypeError("Expected a cComboBoxFromDict or QComboBox widget")
        def set_combobox_value(value: Any) -> None:
            if wdgt.findData(value) == -1:
                wdgt.setCurrentText(str(value))
            else:
                wdgt.setCurrentIndex(wdgt.findData(value))
        return set_combobox_value
    def _setup_combobox_behavior(self, wdgt: cComboBoxFromDict|QComboBox|QWidget, lblText: str) -> None:
        """Configure behavior for combo box widgets."""
        if not isinstance(wdgt, (cComboBoxFromDict, QComboBox)):
            raise TypeError("Expected a cComboBoxFromDict or QComboBox widget")
        self._label = QLabel(lblText)
        self.LabelText = self._label.text
        self._labelSetLblText = self._label.setText
        self._label.setBuddy(wdgt)

        self.Value = wdgt.currentData
        self.setValue = self._create_combobox_setter(wdgt)
        
        if isinstance(wdgt, cComboBoxFromDict):
            self.replaceDict = wdgt.replaceDict

        wdgt.activated.connect(self._emitSelection)

    def _setup_layout(
        self, 
        lblText: str,
        alignlblText: Qt.AlignmentFlag,
    ) -> None:
        """Configure the layout based on widget type and alignment."""
        layout = QGridLayout()
        
        # Determine widget positions based on alignment
        if alignlblText == Qt.AlignmentFlag.AlignLeft:
            positions = ((0, 0), (0, 1))
        elif alignlblText == Qt.AlignmentFlag.AlignRight:
            positions = ((0, 1), (0, 0))
        elif alignlblText == Qt.AlignmentFlag.AlignTop:
            positions = ((0, 0), (1, 0))
        elif alignlblText == Qt.AlignmentFlag.AlignBottom:
            positions = ((1, 0), (0, 0))
        else:
            positions = ((0, 0), (0, 1))  # default to left
        # Place widgets in layout
        if lblText and self._label:
            layout.addWidget(self._label, *positions[0])
            layout.addWidget(self._wdgt, *positions[1])
        else:
            layout.addWidget(self._wdgt, 0, 0)
            
        self.setLayout(layout)
        
    @Slot()
    def refreshChoices(self) -> None:
        """Reload available values from DB."""
        with self._session_factory() as session:
            field = getattr(self._model, self._lookup_field)
            values = session.scalars(select(field).distinct().order_by(field)).all()

        # Populate the list
        if isinstance(self._wdgt, cDataList):
            self._wdgt.clear()
            self._wdgt.addChoices({val: str(val) for val in values if val is not None})
        if isinstance(self._wdgt, cComboBoxFromDict):
            self._wdgt.replaceDict({str(val): val for val in values if val is not None})
    # refreshChoices            

    def _setWidgetValue(self, val):
        """Best-effort assignment based on widget type."""
        self.setValue(val)

    def _getWidgetValue(self):
        """Best-effort retrieval based on widget type."""
        return self.Value()

    def loadFromRecord(self, rec):
        """Load the ORM record value into the widget."""
        val = getattr(rec, self._lookup_field, None) if rec else None
        self._setWidgetValue(val)
        # no setting dirty for lookups

    def saveToRecord(self, rec):
        # lookups don't save their values to the record
        return

    # lookups don't become dirty
    def isDirty(self):
        return False
    def setDirty(self, dirty:bool = False, sendSignal:bool = False):
        return
        
    @Slot()
    def _emitSelection(self) -> None:
        """Emit the selected value."""
        value = None
        if isinstance(self._wdgt, (cComboBoxFromDict, QComboBox)):
            value = self._wdgt.currentData()
        elif isinstance(self._wdgt, cDataList):
            value = self._wdgt.selectedItem()
        self.signalLookupSelected.emit(value)
# endclass cQFmLookupWidg


# * **`cSimpleRecordForm`** → abstract base.

#   * Knows about the current record (`self.currRec`).
#   * Owns the `formFields: dict[str, cQFmFldWidg]`.
#   * Declares abstract hooks you *must* override:

#     * `_buildForm(self) -> None`: where the subclass lays out its widgets.
#     * `changeField(self, fld: cQFmFldWidg) -> None`: what to do when a field changes.
#   * Provides generic helpers: `bindField()`, `getValue()`, `setValue()`, maybe `loadRecord()` / `saveRecord()`.
#   * Provides the common action buttons (`add`, `save`, `delete`, `cancel`).

# * **Subclass (e.g. `cWidgetMenuItem`)** → just implements `_buildForm` to declare widgets.

#   * Doesn’t worry about buttons or record lifecycle; only about field arrangement and per-field behavior.

# That way your `cSimpleRecordForm` handles **record lifecycle + button bar**, and your subclasses handle **field layout + wiring**.

# So **the big win** is:

# * `cSimpleRecordForm` owns record + buttons + formFields.
# * Subclasses only worry about *which fields* and *how to lay them out*.

# Here’s a bare-bones outline:

# TODO: Handle foreign keys properly - let the children do the heavy lifting ??
# TODO: Handle fields that need special massaging   - let the children do the heavy lifting ??
# TODO: pretty up NEW RECORD FLAG
class cSimpleRecordForm(QWidget):
    """
    UPDATE THIS DOCUMENTATION!! UPDATE ME!!
    A simple record form for editing database records.

    Args:
        rec (SQLAlchemy Model Class Instance): The record to edit.
        formname (str | None, optional): The name of the form. Defaults to None.
        parent (QWidget | None, optional): The parent widget. Defaults to None.

    Properties and Methods implemented by child classes:
        _buildForm(self) -> None: where the subclass lays out its widgets.
        changeField(self, fld: cQFmFldWidg) -> None: what to do when a field changes.
        bindField(self, fld: cQFmFldWidg, get_value: Callable[[], Any], set_value: Callable[[Any], None]) -> None: bind a field to a record attribute.
        loadRecord(self) -> None: load the current record into the form fields.
        saveRecord(self) -> None: save the form field values back to the current record.

    Properties:
        formFields (dict[str, cQFmFldWidg]): The form fields in the record.
        currRec (Any): The current record being edited.

    Methods:
        getValue(self, fld: cQFmFldWidg) -> Any: Get the value of a form field.
        setValue(self, fld: cQFmFldWidg, value: Any) -> None: Set the value of a form field.

    Returns:
        _type_: _description_
    """
    _ORMmodel: Type[Any]  # the ORM model class
    _primary_key: Any  # the ORM PK column (InstrumentedAttribute)
    _ssnmaker: sessionmaker[Session]
    _formname = None
    fieldDefs: dict[str, dict[str, Any]] = {}
    currRec: Any
    _lookupFrmElements: List = []

    def __init__(self, 
        model: Type[Any]|None = None, 
        formname: str|None = None, 
        ssnmaker: sessionmaker[Session] | None = None, 
        parent: QWidget | None = None
        ):
        """
        Initialize the form with a record and optional name.

        Args:
            rec (SQLAlchemy Model Class Instance): The record to edit.
            formname (str | None, optional): The name of the form. Defaults to None.
            parent (QWidget | None, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
    
        if not self._ORMmodel:
            if not model:
                raise ValueError("A model class must be provided either in the constructor or as a class attribute")
            self._ORMmodel = model
        self._primary_key = get_primary_key_column(self._ORMmodel)

        if not self._formname:
            self._formname = formname if formname else 'Form'
        if not self._ssnmaker:
            if not ssnmaker:
                raise ValueError("A sessionmaker must be provided either in the constructor or as a class attribute")
            self._ssnmaker = ssnmaker

        self.layoutMain = QVBoxLayout(self)
        self.layoutForm = QGridLayout()
        self.layoutButtons = QHBoxLayout()  # may get redefined in _addActionButtons
        self._statusBar = QStatusBar(self)

        self.layoutFormHdr = QHBoxLayout()
        lblFormName = cQFmNameLabel(self.tr(self._formname), self)
        self.layoutFormHdr.addWidget(lblFormName)
        
        self._newrecFlag = QLabel("New Record", self)
        fontNewRec = QFont()
        fontNewRec.setBold(True)
        fontNewRec.setPointSize(10)
        fontNewRec.setItalic(True)
        self._newrecFlag.setFont(fontNewRec)
        self._newrecFlag.setStyleSheet("color: red;")
        self.layoutFormHdr.addWidget(self._newrecFlag)
        self._newrecFlag.setVisible(False)
        
        self.setWindowTitle(self.tr(self._formname))
        
        # Let subclass build its widgets into self.layoutForm
        self._buildForm()

        # Add buttons (always the same)
        self._addActionButtons()

        # Finalize layout
        self.layoutMain.addLayout(self.layoutFormHdr)
        self.layoutMain.addLayout(self.layoutForm)
        self.layoutMain.addLayout(self.layoutButtons)
        self.layoutMain.addWidget(self._statusBar)      #TODO: more flexibility in where status bar is placed

        self.initializeRec()
        self.on_loadfirst_clicked()
        
        self.showNewRecordFlag(self.isNewRecord())

    # init

    def statusBar(self) -> QStatusBar|None:
        """Get the status bar."""
        return self.findChild(QStatusBar)

    def showError(self, message: str, title: str = "Error") -> None:
        """Show an error message box."""
        QMessageBox.critical(self, title, message)
        # use status bar to show error message
        SB = self.statusBar()
        SB.showMessage(f"Error: {message}") if SB else None

        # TODO: choose whether to messageBox or status bar or both

    def _addActionButtons(self, 
            layoutHorizontal: bool = True, 
            NavActions: list[tuple[str, QIcon]]|None = None,
            CRUDActions: list[tuple[str, QIcon]]|None = None,
            ) -> None:
        """Add action buttons to the form.
        """

        _iconlib = qtawesome.icon
        dfltNavActions = [
                ("First", _iconlib("mdi.page-first")),
                ("Previous", _iconlib("mdi.arrow-left-bold")),
                ("Next", _iconlib("mdi.arrow-right-bold")),
                ("Last", _iconlib("mdi.page-last")),
        ]
        dfltCRUDActionsMain = [
                ("Add", _iconlib("mdi.plus")),
                ("Save", _iconlib("mdi.content-save")),
                ("Delete", _iconlib("mdi.delete")),
                ("Cancel", _iconlib("mdi.cancel")),
        ]
        dfltCRUDActionsSub = [
                ("Add", _iconlib("mdi.plus")),
                ("Save", _iconlib("mdi.content-save")),
                ("Delete", _iconlib("mdi.delete")),
        ]

        NavActns = NavActions if NavActions is not None else dfltNavActions
        CRUDActns = CRUDActions if CRUDActions is not None else dfltCRUDActionsMain

        if layoutHorizontal:
            self.layoutButtons = QHBoxLayout()
        else:
            self.layoutButtons = QVBoxLayout()

        # Navigation
        innerNavLayout = QHBoxLayout()
        for label, icon in NavActns:
            btn = QPushButton(label, self)
            btn.setIcon(icon)
            btn.clicked.connect(lambda _, l=label: self._handleAction(l))
            innerNavLayout.addWidget(btn)

            if label == "Save":
                self.btnCommit = btn
        # CRUD
        innerCRUDLayout = QHBoxLayout()
        for label, icon in CRUDActns:
            btn = QPushButton(label, self)
            btn.setIcon(icon)
            btn.clicked.connect(lambda _, l=label: self._handleAction(l))
            innerCRUDLayout.addWidget(btn)

            if label == "Save":
                self.btnCommit = btn

        self.layoutButtons.addLayout(innerNavLayout)
        if layoutHorizontal:
            self.layoutButtons.addSpacing(20)
        self.layoutButtons.addLayout(innerCRUDLayout)
    # _addNavButtons
    
    # TODO: do structure similar to _addActionButtons to allow custom button sets and define Action handlers
    def _handleAction(self, action: str) -> None:
        # Generic action dispatch — override if needed
        action = action.lower()
        if action == "first":
            self.on_loadfirst_clicked()
        elif action == "previous":
            self.on_loadprev_clicked()
        elif action == "next":
            self.on_loadnext_clicked()
        elif action == "last":
            self.on_loadlast_clicked()
        elif action == "add":
            self.on_add_clicked()
        elif action == "save":
            self.on_save_clicked()
        elif action == "delete":
            self.on_delete_clicked()
        elif action == "cancel":
            self.on_cancel_clicked()
        else:
            print(f"Unknown action: {action}")
            self.showError(f"Unknown action: {action}")
        #endif action
    # _handleAction

    def bindField(self, _fieldName: str, widget: QWidget) -> None:
        """Register field and connect to changeField."""
        fldDef = self.fieldDefs.get(_fieldName)
        if not fldDef:
            raise KeyError(f"Field '{_fieldName}' not found in fieldDefs")
        lookup = (_fieldName[0] == '@')
        fieldName = _fieldName if not lookup else _fieldName[1:]
        subFormElmnt = hasattr(fldDef, 'subform_class')
        
        fldDef["widget"] = widget

        if isinstance(widget, cQFmFldWidg) and not lookup and not subFormElmnt:
            widget.setModelField(fieldName)
        
        if isinstance(widget, cQFmFldWidg):
            widget.signalFldChanged.connect(lambda *_: self.changeField(widget, widget.modelField(), widget.Value()))
        elif isinstance(widget, cQFmLookupWidg):
            widget.signalLookupSelected.connect(lambda *_: self.changeField(widget, widget._lookup_field, widget.Value()))
        #endif isinstance(widget)
    # bindField

    def _buildForm(self) -> None:
        """
        Build widgets and wrap them into _cSimpRecFmElmnt_Base adapters.
        Each fieldDef ends up with:
            - "widget": the actual Qt widget
        """

        def _apply_optional_attrib(widget, attr, value):
            """
            helper function for setting optional attributes

            Args:
                widget (_type_): _description_
                attr (_type_): _description_
                value (_type_): _description_
            """
            if value is None: return
            if hasattr(widget, attr):
                getattr(widget, attr)(value)
            else:
                widget.setProperty(attr, value)
        # _apply_opt_attr
    
        for _fldName, fldDef in self.fieldDefs.items():
            widget = None

            # _fldName indicates a lookup field if the field name starts with '@'
            # lookup will be the boolean flag
            # fldName is the actual field name
            isLookup = (_fldName[0] == '@')
            fldName = _fldName if not isLookup else _fldName[1:]
            SubFormCls = fldDef.get("subform_class", None)
            isSubFormElmnt = (SubFormCls is not None)

            lookupHandler = fldDef.get('lookupHandler', None)
            lblText = fldDef.get('label', fldName)
            widgType = fldDef.get('widgetType', QLineEdit)
            alignlblText = fldDef.get('align', Qt.AlignmentFlag.AlignLeft)
            choices = fldDef.get('choices', None)
            initval = fldDef.get('initval', '')
            lblChkBxYesNo = fldDef.get('lblChkBxYesNo', None)
            focusPolicy = fldDef.get('focusPolicy', Qt.FocusPolicy.ClickFocus if (isLookup or isSubFormElmnt) else None)
            modlFld = fldName
            pos = fldDef.get('position', None)

            # --- Subform case ---
            if isSubFormElmnt:
                widget = SubFormCls(session_factory=self._ssnmaker, parent=self)
                if not isinstance(widget, cSimpRecFmElement_Base):
                    raise TypeError(f'class {SubFormCls.__name__} must inherit from _cSimpRecFmElement_Base')
            # --- Scalar case ---
            elif isLookup:
                if widgType not in (cDataList, cComboBoxFromDict):
                    widgType = cDataList  # force it to be a cDataList
                widget = cQFmLookupWidg(
                    session_factory=self._ssnmaker if self._ssnmaker else app_Session,
                    model=self._ORMmodel,
                    lookup_field=modlFld,
                    lblText=lblText,
                    alignlblText=alignlblText,
                    lookupWidgType=widgType,
                    choices=choices,
                    parent=self
                )
                if lookupHandler:
                    if isinstance(lookupHandler, str):
                        if not hasattr(self, lookupHandler):
                            raise AttributeError(f"lookupHandler method '{lookupHandler}' not found in {self.__class__.__name__}")
                        lookupHandler = getattr(self, lookupHandler)
                    if not callable(lookupHandler):
                        raise TypeError("lookupHandler must be a callable function or a string name of a method")
                    widget.signalLookupSelected.connect(lookupHandler)
                self._lookupFrmElements.append(widget)
            else:
                widget = cQFmFldWidg(
                    widgType=widgType,
                    lblText=lblText,
                    lblChkBxYesNo=lblChkBxYesNo,
                    alignlblText=alignlblText,
                    modlFld=modlFld,
                    choices=choices,
                    initval=initval,
                    parent=self
                )
            #endif subform vs scalar
            if widget is None:
                raise ValueError(f"Failed to create widget for field '{fldName}'")
            if focusPolicy:
                widget.setFocusPolicy(focusPolicy)
            
            if isinstance(widget, (cQFmFldWidg, cQFmLookupWidg)):
                # TODO: convert this to use _apply_opt_attr
                # optional field attributes
                W = widget._wdgt
                optAttributes = [
                    ('noedit', 'setProperty', W.setProperty),                                                                   # type: ignore
                    ('readonly', 'setReadOnly', W.setReadOnly if hasattr(W, 'setReadOnly') else W.setProperty),                 # type: ignore
                    ('frame', 'setFrame', W.setFrame if hasattr(W, 'setFrame') else W.setProperty),                             # type: ignore
                    ('maximumWidth', 'setMaximumWidth', W.setMaximumWidth if hasattr(W, 'setMaximumWidth') else W.setProperty), # type: ignore
                    ('focusPolicy', 'setFocusPolicy', W.setFocusPolicy if hasattr(W, 'setFocusPolicy') else W.setProperty),     # type: ignore
                    ('tooltip', 'setToolTip', W.setToolTip if hasattr(W, 'setToolTip') else W.setProperty),                     # type: ignore
                ]
                for attr, method_name, method in optAttributes:
                    attrVal = fldDef.get(attr, None)
                    if method_name == 'setProperty' or method is W.setProperty:
                        W.setProperty(attr, attrVal) if attrVal is not None else None 
                    elif attrVal is not None:
                        method(attrVal) if hasattr(W, method_name) else W.setProperty(attr, attrVal) # type: ignore
                    #endif attrVal
                #endfor attr, method_name, method in optAttributes

                # other optional attributes
                attrVal = fldDef.get('bgColor', None)
                if attrVal is not None:
                    W.setStyleSheet(f"background-color: {attrVal};") if hasattr(W, 'setStyleSheet') else W.setProperty('bgColor', attrVal) # type: ignore
            #endif isinstance(widget, (cQFmFldWidg, cQFmLookupWidg)):

            # Save references
            self.bindField(_fldName, widget)

            # Place in layout
            if isinstance(pos, tuple) and len(pos) >= 2:
                self.layoutForm.addWidget(widget, *pos)

            widget.dirtyChanged.connect(
                lambda dirty, w=widget: self.setDirty(w, dirty)
            )
        # endfor fldDef in self.fieldDefs
    # _buildForm

    def on_cancel_clicked(self):
        #for now, just close form
        self.close()
    # cancel_record

    def repopLookups(self) -> None:
        for lkupwdgt in self._lookupFrmElements:
            lkupwdgt.refreshChoices()

    def isNewRecord(self) -> bool:
        return self.currRec is None or getattr(self.currRec, self._primary_key.key) is None
    
    def isit_OKToLeaveRecord(self) -> bool:
        """
        Check if the form is dirty. If so, prompt user.
        Returns True if it is safe to proceed with navigation, False otherwise.
        """
        if not self.isDirty():
            return True

        choice = QMessageBox.question(
            self,
            "Unsaved changes",
            "You have unsaved changes. Save before continuing?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Yes,
        )

        if choice == QMessageBox.StandardButton.Yes:
            self.on_save_clicked()
            return True

        elif choice == QMessageBox.StandardButton.No:
            # Discard changes -> reload current record fresh
            if self.currRec:
                self.fillFormFromcurrRec()
            return True

        else:  # Cancel
            return False
    # isit_OKToLeaveRecord

    ##########################################
    ########    Create

    def initializeRec(self):
        """
        Initialize a new record with default values.

        implementation should call fillFormFromcurrRec() after setting default values in self.currRec
        """
        self.currRec = self._ORMmodel()  
        # raise NotImplementedError
    # initializeRec

    def on_add_clicked(self):
        """
        Add a new record to the database: initialize, set defaults and save.
        No, don't save. reserve that for the save button.
        """
        # if dirty, ask to save
        if not self.isit_OKToLeaveRecord():
            return
        
        self.initializeRec()
        self.fillFormFromcurrRec()
        self.showNewRecordFlag(True)
    # add_record
    
    ##########################################
    ########    Read / Navigation

    def load_record(self, recindex: int):
        """
        Load a record from the database.
        NOTE: For this class, recindex is the id of the record to load, not the index.

        Args:
            recindex (int): The ID of the record to load.
        """
        self._load_record_by_id(recindex)
    # load_record

    def get_prev_record_id(self, recID:int) -> int:
        with self._ssnmaker() as session:
            prev_id = session.query(func.max(self._primary_key)).where(self._primary_key < recID).scalar()
        return prev_id
    def get_next_record_id(self, recID:int) -> int:
        with self._ssnmaker() as session:
            next_id = session.query(func.min(self._primary_key)).where(self._primary_key > recID).scalar()
        return next_id
        
    def on_loadfirst_clicked(self):
        # determine minimum id in database and load it
        with self._ssnmaker() as session:
            min_id = session.query(func.min(self._primary_key)).scalar()
            if min_id:
                self._navigate_to(min_id)

    def on_loadprev_clicked(self):
        # determine previous id in database and load it
        currID = getattr(self.currRec, self._primary_key.key)
        prev_id = self.get_prev_record_id(currID)
        if prev_id:
            self._navigate_to(prev_id)

    def on_loadnext_clicked(self):
        # determine next id in database and load it
        currID = getattr(self.currRec, self._primary_key.key)
        next_id = self.get_next_record_id(currID)
        if next_id:
            self._navigate_to(next_id)

    def on_loadlast_clicked(self):
        # determine maximum id in database and load it
        with self._ssnmaker() as session:
            max_id = session.query(func.max(self._primary_key)).scalar()
            if max_id:
                self._navigate_to(max_id)

    # # --- Lookup navigation ---
    def _navigate_to(self, rec_id: int):
        """Navigate safely to a record (with save/discard prompt if dirty)."""
        if not self.isit_OKToLeaveRecord():
            return  # Cancel pressed → stay put

        self._load_record_by_id(rec_id)
    # _navigate_to

    def _load_record_by_id(self, pk_val):
        """Low-level load (assumes it's safe to replace current record)."""
        with self._ssnmaker() as session:
            rec = session.get(self._ORMmodel, pk_val)
            if rec is None:
                self.showError(f"No Record with id {pk_val}")
                return
            else:
                # detach rec from session and make it the current record
                session.expunge(rec)
                self.currRec = rec
                self.fillFormFromcurrRec()
            # endif rec 
        #endwith session
    # load_record_by_id

    def load_record_by_field(self, field: str | Any, value: Any) -> None:
        """
        field may be either:
          - a string (column name), or
          - an ORM field object (MyModel.name).
        """
        if not self.isit_OKToLeaveRecord():
            return  # Cancel pressed → stay put
        
        if isinstance(field, str):
            orm_field = getattr(self._ORMmodel, field)
        else:
            orm_field = field

        with self._ssnmaker() as session:
            rec = session.query(self._ORMmodel).filter(orm_field == value).first()
            if rec is None:
                self.showError(f"No Record with {orm_field.key} == {value}")
                return
            else:
                # detach rec from session and make it the current record
                session.expunge(rec)
                self.currRec = rec
                self.fillFormFromcurrRec()
            # endif rec 
        #endwith session
    # load_record_by_field

    def fillFormFromcurrRec(self):
        for fldDef in self.fieldDefs.values():
            fld = fldDef.get("widget")
            if fld:
                fld.loadFromRecord(self.currRec)

        self.showNewRecordFlag(self.isNewRecord())
        self.setDirty(self, False)
    # fillFormFromRec

    @Slot()
    def lookup_and_load(self, fld: str, value: Any):
        value = value.get('text', value) if isinstance(value, dict) else (getattr(value, 'text', value) if hasattr(value, 'text') else value)
        self.load_record_by_field(fld, value)
    # lookup_CIMSNum
        
    # TODO: play with positioning of new record flag
    def showNewRecordFlag(self, show: bool) -> None:
        self._newrecFlag.setVisible(show)

    ##########################################
    ########    Update

    @Slot()
    def changeField(self, wdgt, dbField, wdgt_value, force=False):
        """
        Called when a widget changes.
        This no longer writes directly into the ORM object — adapters own that.
        Neither does it Marks the widget/adapter dirty
        Instead, it:
          - Applies optional transforms
          - Updates form-level dirty flag
        """
        # If adapter passed in, grab widget
        widget = wdgt

        if getattr(widget, "property", lambda x: False)("noedit"):
            return

        # Apply transformation hook if subclass defines one
        transform_func = getattr(self, f"_transform_{dbField}", None)
        if callable(transform_func):
            wdgt_value = transform_func(wdgt_value)

        # Update form dirty state
        self.setDirty(widget, True)
        # endif wdgt_value
    # changeField

    @Slot()
    def on_save_clicked(self, *_):
        """
        Collects field values from adapters/subforms, writes them into currRec,
        and persists via a short-lived session.
        """
        if not self.currRec:
            return

        try:
            # Push data from form -> ORM object, except for subforms - they must come after the main record is saved
            for fldName, fldDef in self.fieldDefs.items():
                isSubFormElmnt = "subform_class" in fldDef
                if not isSubFormElmnt:      # subforms handled after main record is saved
                    widget = fldDef.get("widget")
                    if widget:
                        widget.saveToRecord(self.currRec)
            # endfor fldDef in self.fieldDefs

            # Persist using a short-lived session
            with self._ssnmaker(expire_on_commit=False) as session:
                merged = session.merge(self.currRec)
                session.flush()
                session.refresh(merged)
                
                recID = getattr(merged, self._primary_key.key)   # no change for existing record; loads new id for a new one
                # should I copy other fields, too?
                
                # session.expunge(self.currRec) # not needed, since self.currRec not bound to session
                
                session.commit()
            # endwith session

            # now handle subforms
            for fldName, fldDef in self.fieldDefs.items():
                isSubFormElmnt = "subform_class" in fldDef
                if isSubFormElmnt:
                    widget = fldDef.get("widget")
                    if widget:
                        widget.saveToRecord(self.currRec)
            # endfor fldDef in self.fieldDefs
            
            # reload the record (repaints screen, gets db defaults and new id, if any)
            self.repopLookups()
            self._load_record_by_id(recID)

            # all this not needed because of reload
            # # Reset dirty flags (both form and adapters)
            # for fldName, fldDef in self.fieldDefs.items():
            #     widget = fldDef.get("widget")
            #     if widget:
            #         widget.setDirty(False)
            # self.setDirty(self, False)

            # # Clear new record flag
            # assert not self.isNewRecord()
            # self.showNewRecordFlag(False)

        except Exception as e:
            self.showError(str(e), "Error saving record")
    # save_record

    ##########################################
    ########    Delete

    # TODO: confirm delete
    @Slot()
    def on_delete_clicked(self):
        if not self.currRec:
            return
        
        keyID = getattr(self.currRec, self._primary_key.key)

        if not self.isit_OKToLeaveRecord():
            return  # Cancel pressed → stay put

        confirm = QMessageBox.question(
            self,
            "Delete record",
            f"Really delete record {keyID}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        # Actually delete
        with self._ssnmaker() as session:
            rec = session.get(self._ORMmodel, keyID)
            if rec:
                session.delete(rec)
                session.commit()

        self.repopLookups()
        # Navigate to neighbor, or clear form if none
        next_id = self.get_next_record_id(keyID)
        prev_id = self.get_prev_record_id(keyID)
        target_id = next_id or prev_id
        if target_id:
            self._load_record_by_id(target_id)
        else:
            self.make_currRecEmpty()
    # delete_record

    def make_currRecEmpty(self):
        # replace with an empty record
        # assume this is an intentional call - don't check currRec.isDirty
        self.currRec = self._ORMmodel()
        self.setDirty(self, False)
        self.fillFormFromcurrRec()
    # makeCurrecEmpty

    # ##########################################
    # ########    CRUD support

    @Slot()
    def setDirty(self, wdgt, dirty: bool = True):
        # rethink - adapters handle their own dirty state
        # so all that needs to be set here is self.dirty
        # right?
        
        # better yet, self doesn't need to track its dirty state
        # since  isDirty will poll children
        
        # keep an eye on the time the polling takes
        # if it's excessive, find the best way to record child dirty states

        # Enable save button if anything is dirty
        self.btnCommit.setEnabled(self.isDirty())
    # setFormDirty
    
    def isDirty(self) -> bool:
        # poll children; if one is Dirty, form is Dirty
        for FmElement in self.children():
            if not isinstance(FmElement, cSimpRecFmElement_Base):
                continue
            elif FmElement.isDirty():
                return True
            else:
                continue
        #endfor FmElement in self.children():
        
        return False
    # isFormDirty
# cSimpleRecordForm

class cSimpleRecordSubForm(cSimpRecFmElement_Base):
    """
    Generic subform widget to handle a one-to-many relationship.
    Ex: parts_needed for a WorkOrder.

    Args:
        ORMmodel (Type[Any]): ORM model for the subrecords
        parentFK (InstrumentedAttribute): relationship FK field in the parent model
        session_factory (sessionmaker): SQLAlchemy sessionmaker
        parent (QWidget | None): parent widget
    """

    def __init__(self, 
        ORMmodel: Type[Any]|None = None, 
        parentFK: Any = None, 
        session_factory: sessionmaker[Session] | None = None, 
        viewClass: Type[QTableView] = QTableView,
        parent=None
        ):
        super().__init__(parent)

        if not self._ORMmodel:
            if not ORMmodel:
                raise ValueError("A model class must be provided either in the constructor or as a class attribute")
            self._ORMmodel = ORMmodel
        self._primary_key = get_primary_key_column(self._ORMmodel)

        pfk = parentFK if parentFK else getattr(self, '_parentFK', None)
        if not self._parentFK:
            if not parentFK:
                raise ValueError("A parent FK must be provided either in the constructor or as a class attribute")
        self._parentFK = getattr(self._ORMmodel, pfk) if isinstance(pfk, str) else parentFK # type: ignore

        if not self._ssnmaker:
            if not session_factory:
                raise ValueError("A sessionmaker must be provided either in the constructor or as a class attribute")
            self._ssnmaker = session_factory

        self._parentRec = None  # set by parent form when loading
        self._parentRecPK: Any  # set by parent form when loading
        self._childRecs:list = []
        self._deleted_childRecs:list = []

        self.layoutMain = QVBoxLayout(self)
        self.table = viewClass(parent=self)
        self.Tblmodel = SQLAlchemyTableModel(self._ORMmodel, self._ssnmaker, literal(False), parent=self)
        self.table.setModel(self.Tblmodel)
        self.layoutMain.addWidget(self.table)

        # action buttons for add/remove
        btnLayout = QHBoxLayout()
        self.btnAdd = QPushButton("Add")
        self.btnDel = QPushButton("Delete")
        btnLayout.addWidget(self.btnAdd)
        btnLayout.addWidget(self.btnDel)
        self.layoutMain.addLayout(btnLayout)

        self.btnAdd.clicked.connect(self.add_row)
        self.btnDel.clicked.connect(self.del_row)



    # --- Lifecycle hooks ---
    def loadFromRecord(self, rec):
        """Load subrecords for the given parent record."""
        self._parentRec = rec
        self._parentRecPK = get_primary_key_column(rec.__class__)
        self._childRecs.clear()
        self._deleted_childRecs.clear()
        

        with self._ssnmaker() as session:
            rows = session.scalars(
                select(self._ORMmodel)
                .filter(self._parentFK == getattr(rec, self._parentRecPK.key))
                ).all()
            for r in rows:
                session.expunge(r)
            self._childRecs.extend(rows)

            self.Tblmodel.refresh(filter=(self._parentFK == getattr(rec, self._parentRecPK.key)))
        #endwith
    # loadFromRecord

    def saveToRecord(self, rec):
        """Save subrecords back to database."""
        if not self._parentRec:
            return
        if self._parentRec != rec:
            raise ValueError("Parent record mismatch on saveToRecord")

        with self._ssnmaker() as session:
            # reattach new/edited
            for rec in self._childRecs:
                setattr(rec, self._parentFK.key, getattr(self._parentRec, self._parentRecPK.key))
                session.merge(rec)

            # delete removed
            for rec in self._deleted_childRecs:
                if getattr(rec, self._parentRecPK.key, None) is not None:
                    obj = session.merge(rec)
                    session.delete(obj)

            session.commit()
        # endwith
            
        self._deleted_childRecs.clear()
    # saveForParent

    # --- Internal helpers ---

    def add_row(self):
        row = self._ORMmodel()
        setattr(row, self._parentFK.key, getattr(self._parentRec, self._parentRecPK.key, None))
        self.Tblmodel.insertRow(row)
    # add_row

    def del_row(self):
        idxs = self.table.selectionModel().selectedRows()
        for idx in sorted(idxs, key=lambda x: x.row(), reverse=True):
            rec = self.Tblmodel.record(idx.row())
            if rec in self._childRecs:
                self._childRecs.remove(rec)
                self._deleted_childRecs.append(rec)
            self.Tblmodel.removeRow(idx.row())
# cSimpleRecordSubForm

class cSimpRecSbFmRecord(cSimpRecFmElement_Base):
# class cSimpRecSbFmRecord(cSimpRecFmElement_Base, cSimpleRecordForm):
# nope, don't inherit from cSimpleRecordForm - that double-defines layouts, buttons, etc. Copy what we need from it instead.
    # the records contained within the ListWidget
    def __init__(self, rec: Any, parent:"cSimpleRecordSubForm2|None"=None):
        self._model = rec.__class__
        if not self._model:
            raise ValueError(f"{rec} should be a record with an ORM class")
        self._primary_key = get_primary_key_column(self._model)

        self._ssnmaker = getattr(parent, '_ssnmaker', None) # type: ignore
        if not self._ssnmaker:
            raise ValueError(f"A sessionmaker must be provided defined in the parent form {parent}")

        self.fieldDefs = getattr(parent, 'fieldDefs', {})  # type: ignore

        super().__init__(parent=parent)

        # self.setParent(parent) # doesn't super().__init__ do this?

        self.layoutMain = QVBoxLayout(self)
        self.layoutForm = QGridLayout()
        self._statusBar = QStatusBar(self)

        self._newrecFlag = QLabel("New Rec", self)
        fontNewRec = QFont()
        fontNewRec.setBold(True)
        fontNewRec.setPointSize(10)
        fontNewRec.setItalic(True)
        self._newrecFlag.setFont(fontNewRec)
        self._newrecFlag.setStyleSheet("color: red;")
        self.layoutMain.addWidget(self._newrecFlag) # at top for visibility - different from main form
        self._newrecFlag.setVisible(False)

        # Let subclass build its widgets into self.layoutForm
        self._buildForm()

        # Finalize layout
        self.layoutMain.addLayout(self.layoutForm)
        self.layoutMain.addWidget(self._statusBar)      #TODO: more flexibility in where status bar is placed

        self.currRec = rec
        self.loadFromRecord(rec)
        self.showNewRecordFlag(self.isNewRecord())
    # __init__

    #######################################################
    ########    stuff copied from cSimpleRecordForm
    #######################################################

    def statusBar(self) -> QStatusBar|None:
        """Get the status bar."""
        return self.findChild(QStatusBar)

    def showError(self, message: str, title: str = "Error") -> None:
        """Show an error message box."""
        QMessageBox.critical(self, title, message)
        # use status bar to show error message
        SB = self.statusBar()
        SB.showMessage(f"Error: {message}") if SB else None

        # TODO: choose whether to messageBox or status bar or both

    def bindField(self, _fieldName: str, widget: QWidget) -> None:
        """Register field and connect to changeField."""
        fldDef = self.fieldDefs.get(_fieldName)
        if not fldDef:
            raise KeyError(f"Field '{_fieldName}' not found in fieldDefs")
        lookup = (_fieldName[0] == '@')
        fieldName = _fieldName if not lookup else _fieldName[1:]
        subFormElmnt = hasattr(fldDef, 'subform_class')

        fldDef["widget"] = widget

        if isinstance(widget, cQFmFldWidg) and not lookup and not subFormElmnt:
            widget.setModelField(fieldName)

        if isinstance(widget, cQFmFldWidg):
            widget.signalFldChanged.connect(lambda *_: self.changeField(widget, widget.modelField(), widget.Value()))
        # elif isinstance(widget, cQFmLookupWidg):        # lookup widgets not supported in subforms (for now)
        #     widget.signalLookupSelected.connect(lambda *_: self.changeField(widget, widget._lookup_field, widget.Value()))
        #endif isinstance(widget)
    # bindField

    def _buildForm(self) -> None:
        """
        Build widgets and wrap them into _cSimpRecFmElmnt_Base adapters.
        Each fieldDef ends up with:
            - "widget": the actual Qt widget
        """

        def _apply_optional_attrib(widget, attr, value):
            """
            helper function for setting optional attributes

            Args:
                widget (_type_): _description_
                attr (_type_): _description_
                value (_type_): _description_
            """
            if value is None: return
            if hasattr(widget, attr):
                getattr(widget, attr)(value)
            else:
                widget.setProperty(attr, value)
        # _apply_opt_attr

        for _fldName, fldDef in self.fieldDefs.items():
            widget = None

            # _fldName indicates a lookup field if the field name starts with '@'
            # lookup will be the boolean flag
            # fldName is the actual field name
            isLookup = (_fldName[0] == '@')
            fldName = _fldName if not isLookup else _fldName[1:]
            SubFormCls = fldDef.get("subform_class", None)
            isSubFormElmnt = (SubFormCls is not None)

            lookupHandler = fldDef.get('lookupHandler', None)
            lblText = fldDef.get('label', fldName)
            widgType = fldDef.get('widgetType', QLineEdit)
            alignlblText = fldDef.get('align', Qt.AlignmentFlag.AlignLeft)
            choices = fldDef.get('choices', None)
            initval = fldDef.get('initval', '')
            lblChkBxYesNo = fldDef.get('lblChkBxYesNo', None)
            focusPolicy = fldDef.get('focusPolicy', Qt.FocusPolicy.ClickFocus if (isLookup or isSubFormElmnt) else None)
            modlFld = fldName
            pos = fldDef.get('position', None)

            # --- Subform case ---
            if isSubFormElmnt:
                widget = SubFormCls(session_factory=self._ssnmaker, parent=self)
                if not isinstance(widget, cSimpRecFmElement_Base):
                    raise TypeError(f'class {SubFormCls.__name__} must inherit from _cSimpRecFmElement_Base')
            # --- Scalar case ---
            elif isLookup:
                # lookup widgets not supported in subforms (for now)
                pass
                # if widgType not in (cDataList, cComboBoxFromDict):
                #     widgType = cDataList  # force it to be a cDataList
                # widget = cQFmLookupWidg(
                #     session_factory=self._ssnmaker if self._ssnmaker else app_Session,
                #     model=self._model,
                #     lookup_field=modlFld,
                #     lblText=lblText,
                #     alignlblText=alignlblText,
                #     lookupWidgType=widgType,
                #     choices=choices,
                #     parent=self
                # )
                # if lookupHandler:
                #     if isinstance(lookupHandler, str):
                #         if not hasattr(self, lookupHandler):
                #             raise AttributeError(f"lookupHandler method '{lookupHandler}' not found in {self.__class__.__name__}")
                #         lookupHandler = getattr(self, lookupHandler)
                #     if not callable(lookupHandler):
                #         raise TypeError("lookupHandler must be a callable function or a string name of a method")
                #     widget.signalLookupSelected.connect(lookupHandler)
                # self._lookupFrmElements.append(widget)
            else:
                widget = cQFmFldWidg(
                    widgType=widgType,
                    lblText=lblText,
                    lblChkBxYesNo=lblChkBxYesNo,
                    alignlblText=alignlblText,
                    modlFld=modlFld,
                    choices=choices,
                    initval=initval,
                    parent=self
                )
            #endif subform vs scalar
            if widget is None:
                raise ValueError(f"Failed to create widget for field '{fldName}'")
            if focusPolicy:
                widget.setFocusPolicy(focusPolicy)

            # if isinstance(widget, (cQFmFldWidg, cQFmLookupWidg)):   # lookup widgets not supported in subforms (for now)
            if isinstance(widget, (cQFmFldWidg, )):   # lookup widgets not supported in subforms (for now)
                # TODO: convert this to use _apply_opt_attr
                # optional field attributes
                W = widget._wdgt
                optAttributes = [
                    ('noedit', 'setProperty', W.setProperty),                                                                   # type: ignore
                    ('readonly', 'setReadOnly', W.setReadOnly if hasattr(W, 'setReadOnly') else W.setProperty),                 # type: ignore
                    ('frame', 'setFrame', W.setFrame if hasattr(W, 'setFrame') else W.setProperty),                             # type: ignore
                    ('maximumWidth', 'setMaximumWidth', W.setMaximumWidth if hasattr(W, 'setMaximumWidth') else W.setProperty), # type: ignore
                    ('focusPolicy', 'setFocusPolicy', W.setFocusPolicy if hasattr(W, 'setFocusPolicy') else W.setProperty),     # type: ignore
                    ('tooltip', 'setToolTip', W.setToolTip if hasattr(W, 'setToolTip') else W.setProperty),                     # type: ignore
                ]
                for attr, method_name, method in optAttributes:
                    attrVal = fldDef.get(attr, None)
                    if method_name == 'setProperty' or method is W.setProperty:
                        W.setProperty(attr, attrVal) if attrVal is not None else None
                    elif attrVal is not None:
                        method(attrVal) if hasattr(W, method_name) else W.setProperty(attr, attrVal) # type: ignore
                    #endif attrVal
                #endfor attr, method_name, method in optAttributes

                # other optional attributes
                attrVal = fldDef.get('bgColor', None)
                if attrVal is not None:
                    W.setStyleSheet(f"background-color: {attrVal};") if hasattr(W, 'setStyleSheet') else W.setProperty('bgColor', attrVal) # type: ignore
            #endif isinstance(widget, (cQFmFldWidg, cQFmLookupWidg)):

            # Save references
            self.bindField(_fldName, widget)

            # Place in layout
            if isinstance(pos, tuple) and len(pos) >= 2:
                self.layoutForm.addWidget(widget, *pos)

            widget.dirtyChanged.connect(
                lambda dirty: self.setDirty(dirty)
            )
        # endfor fldDef in self.fieldDefs
    # _buildForm

    # TODO: play with positioning of new record flag
    def showNewRecordFlag(self, show: bool) -> None:
        self._newrecFlag.setVisible(show)

    def isNewRecord(self) -> bool:
        return self.currRec is None or getattr(self.currRec, self._primary_key.key) is None

    def fillFormFromcurrRec(self):
        for fldDef in self.fieldDefs.values():
            fld = fldDef.get("widget")
            if fld:
                fld.loadFromRecord(self.currRec)

        self.showNewRecordFlag(self.isNewRecord())
        self.setDirty(False)
    # fillFormFromRec

    def changeField(self, wdgt, dbField, wdgt_value, force=False):
        """
        Called when a widget changes.
        This no longer writes directly into the ORM object — adapters own that.
        Neither does it Marks the widget/adapter dirty
        Instead, it:
          - Applies optional transforms
          - Updates form-level dirty flag
        """
        # If adapter passed in, grab widget
        widget = wdgt

        if getattr(widget, "property", lambda x: False)("noedit"):
            return

        # Apply transformation hook if subclass defines one
        transform_func = getattr(self, f"_transform_{dbField}", None)
        if callable(transform_func):
            wdgt_value = transform_func(wdgt_value)

        # Update form dirty state
        self.setDirty(widget, True)
        # endif wdgt_value
    # changeField

    @Slot()
    def on_save_clicked(self, *_):
        """
        Collects field values from adapters/subforms, writes them into currRec,
        and persists via a short-lived session.
        """
        if not self.currRec:
            return

        try:
            # Push data from form -> ORM object, except for subforms - they must come after the main record is saved
            for fldName, fldDef in self.fieldDefs.items():
                isSubFormElmnt = "subform_class" in fldDef
                if not isSubFormElmnt:      # subforms handled later
                    widget = fldDef.get("widget")
                    if widget:
                        widget.saveToRecord(self.currRec)
            # endfor fldDef in self.fieldDefs

            # Persist using a short-lived session
            assert self._ssnmaker is not None, "_ssnmaker (sessionmaker) is not set"
            with self._ssnmaker(expire_on_commit=False) as session:
                merged = session.merge(self.currRec)
                session.flush()
                session.refresh(merged)

                recID = getattr(merged, self._primary_key.key)   # no change for existing record; loads new id for a new one
                # should I copy other fields, too?

                # session.expunge(self.currRec) # not needed, since self.currRec not bound to session

                session.commit()
            # endwith session

            # doublecheck that self.currRec has the new ID, if it was a new record

            # now handle subforms
            for fldName, fldDef in self.fieldDefs.items():
                isSubFormElmnt = "subform_class" in fldDef
                if isSubFormElmnt:
                    widget = fldDef.get("widget")
                    if widget:
                        widget.saveToRecord(self.currRec)
            # endfor fldDef in self.fieldDefs

            # reload the record (repaints screen, gets db defaults and new id, if any)
            self.fillFormFromcurrRec()

            # all this not needed because of reload
            # # Reset dirty flags (both form and adapters)
            # for fldName, fldDef in self.fieldDefs.items():
            #     widget = fldDef.get("widget")
            #     if widget:
            #         widget.setDirty(False)
            # self.setDirty(self, False)

            # # Clear new record flag
            # assert not self.isNewRecord()
            # self.showNewRecordFlag(False)

        except Exception as e:
            self.showError(str(e), "Error saving record")
    # save_record

    ###########################################
    ###########################################

    def loadFromRecord(self, rec: object) -> None:
        """Fill widget from ORM record."""
        self.fillFormFromcurrRec()
    # loadFromRecord

    def saveToRecord(self, rec: object) -> None:
        """Push widget state into ORM record."""
        self.on_save_clicked()
    # saveToRecord

    # def isDirty(self) -> bool:
    #     """Return True if the widget's value differs from what was loaded."""
    #     return False
    # # isDirty
        

    # def setDirty(self, dirty: bool = True, sendSignal:bool = True) -> None:
    #     """Mark the field/subform as dirty."""
    #     pass
    # # setDirty
# cSimpRecSbFmRecord
class cSimpleRecordSubForm2(cSimpRecFmElement_Base):
    """
    Generic subform widget to handle a one-to-many relationship.
    Ex: parts_needed for a WorkOrder.

    Args:
        ORMmodel (Type[Any]): ORM model for the subrecords
        parentFK (InstrumentedAttribute): relationship FK field in the parent model
        session_factory (sessionmaker): SQLAlchemy sessionmaker
        parent (QWidget | None): parent widget
    """


# NEXT: make viewClass QListWidget (was QTableView)
    def __init__(self,
        ORMmodel: Type[Any]|None = None,
        parentFK: Any = None,
        session_factory: sessionmaker[Session] | None = None,
        viewClass: Type[QListWidget] = QListWidget,
        parent=None
        ):

        super().__init__(parent)

        if not self._model:
            if not ORMmodel:
                raise ValueError("A model class must be provided either in the constructor or as a class attribute")
            self._model = ORMmodel
        self._primary_key = get_primary_key_column(self._model)

        pfk = parentFK if parentFK else getattr(self, '_parentFK', None)
        if not self._parentFK:
            if not parentFK:
                raise ValueError("A parent FK must be provided either in the constructor or as a class attribute")
        self._parentFK = getattr(self._model, pfk) if isinstance(pfk, str) else parentFK # type: ignore

        if not self._ssnmaker:
            if not session_factory:
                raise ValueError("A sessionmaker must be provided either in the constructor or as a class attribute")
            self._ssnmaker = session_factory

        self._parentRec = None  # set by parent form when loading
        self._parentRecPK: Any  # set by parent form when loading
        self._childRecs:list = []
        self._deleted_childRecs:list = []

        self.layoutMain = QVBoxLayout(self)
        self.dispArea = viewClass(parent=self)
        # self.Tblmodel = SQLAlchemyTableModel(self._model, self._ssnmaker, literal(False), parent=self)
        # FIXMEFIXMEFIXME!!!
        # not needed? each record widget handles its own data
        # self.dispArea.setModel(self.Tblmodel)  # yhis shouldn't work - change to handle link table <-> Tblmodel internally - use _childRecs?
        self.layoutMain.addWidget(self.dispArea)

        # action buttons for add/remove
        btnLayout = QHBoxLayout()
        self.btnAdd = QPushButton("Add")
        self.btnDel = QPushButton("Delete")
        btnLayout.addWidget(self.btnAdd)
        btnLayout.addWidget(self.btnDel)
        self.layoutMain.addLayout(btnLayout)

        self.btnAdd.clicked.connect(self.add_row)
        self.btnDel.clicked.connect(self.del_row)
    # __init__

    def statusBar(self) -> QStatusBar|None:
        """Get the status bar."""
        return self.findChild(QStatusBar)

    def showError(self, message: str, title: str = "Error") -> None:
        """Show an error message box."""
        QMessageBox.critical(self, title, message)
        # use status bar to show error message
        SB = self.statusBar()
        SB.showMessage(f"Error: {message}") if SB else None

    # --- Lifecycle hooks ---
    def loadFromRecord(self, rec):
        """Load subrecords for the given parent record."""
        self._parentRec = rec
        self._parentRecPK = get_primary_key_column(rec.__class__)
        self._childRecs.clear()
        self._deleted_childRecs.clear()

        with self._ssnmaker() as session:
            rows = session.scalars(
                select(self._model)
                .filter(self._parentFK == getattr(rec, self._parentRecPK.key))
                ).all()
            for r in rows:
                session.expunge(r)
            self._childRecs.extend(rows)
        #endwith

        # clear _recDisplArea and repopulate from _childRecs
        self.dispArea.clear()
        for rec in self._childRecs:
            self._addDisplayRow(rec)
        # endfor rec in self._childRecs

        # self.Tblmodel.refresh(filter=(self._parentFK == getattr(rec, self._parentRecPK.key)))
    # loadFromRecord
    def _addDisplayRow(self, rec):
        """Add a display row for the given record."""
        # does NOT add to _childRecs - that must be done separately (document why)
        wdgt = cSimpRecSbFmRecord(rec, parent=self)
        QLWitm = QListWidgetItem()
        QLWitm.setSizeHint(wdgt.sizeHint())
        self.dispArea.addItem(QLWitm)
        self.dispArea.setItemWidget(QLWitm, wdgt)
    # _addDisplayRow

    def saveToRecord(self, rec):
        """Save subrecords back to database."""
        if not self._parentRec:
            return
        if self._parentRec != rec:
            raise ValueError("Parent record mismatch on saveToRecord")

        with self._ssnmaker() as session:
            # reattach new/edited
            for rec in self._childRecs:
                setattr(rec, self._parentFK.key, getattr(self._parentRec, self._parentRecPK.key))
                session.merge(rec)

            # delete removed
            for rec in self._deleted_childRecs:
                if getattr(rec, self._parentRecPK.key, None) is not None:
                    obj = session.merge(rec)
                    session.delete(obj)

            session.commit()
        # endwith

        self._deleted_childRecs.clear()

        self.loadFromRecord(self._parentRec)   # reload to refresh display area
    # saveForParent

    # --- Internal helpers ---

    def add_row(self):
        row = self._model()
        setattr(row, self._parentFK.key, getattr(self._parentRec, self._parentRecPK.key, None))

        self._childRecs.append(row)
        self._addDisplayRow(row)
    # add_row

    #TODO: implement del_row
    def del_row(self):
        idxs = self.dispArea.selectionModel().selectedRows()    # does dispArea have selectionModel()?
        # for idx in sorted(idxs, key=lambda x: x.row(), reverse=True):
        #     rec = self.Tblmodel.record(idx.row())
        #     if rec in self._childRecs:
        #         self._childRecs.remove(rec)
        #         self._deleted_childRecs.append(rec)
            # see loadFromRecord for how to add to display area
            # self.Tblmodel.removeRow(idx.row())
    # del_row

    # --- Overrides of cSimpleRecordForm methods ---
    # def _addActionButtons(self, 
    #         layoutHorizontal: bool = True, 
    #         NavActions: list[tuple[str, QIcon]]|None = None,
    #         CRUDActions: list[tuple[str, QIcon]]|None = None,
    #         ) -> None:
    #     """Add action buttons to the form.
    #     """
    #     _iconlib = qtawesome.icon
    #     # dfltNavActions = [
    #     #         ("First", _iconlib("mdi.page-first")),
    #     #         ("Previous", _iconlib("mdi.arrow-left-bold")),
    #     #         ("Next", _iconlib("mdi.arrow-right-bold")),
    #     #         ("Last", _iconlib("mdi.page-last")),
    #     # ]
    #     dfltNavActions = [] # no nav actions for subforms
    #     dfltCRUDActionsMain = [
    #             ("Add", _iconlib("mdi.plus")),
    #             ("Save", _iconlib("mdi.content-save")),
    #             ("Delete", _iconlib("mdi.delete")),
    #             ("Cancel", _iconlib("mdi.cancel")),
    #     ]
    #     dfltCRUDActionsSub = [
    #             ("Add", _iconlib("mdi.plus")),
    #             ("Save", _iconlib("mdi.content-save")),
    #             ("Delete", _iconlib("mdi.delete")),
    #     ]

    #     layoutHorizontal = True  # force horizontal for subforms
    #     NavActns = NavActions if NavActions is not None else dfltNavActions
    #     CRUDActns = CRUDActions if CRUDActions is not None else dfltCRUDActionsSub

    #     if layoutHorizontal:
    #         self.layoutButtons = QHBoxLayout()
    #     else:
    #         self.layoutButtons = QVBoxLayout()

    #     # Navigation
    #     innerNavLayout = QHBoxLayout()
    #     for label, icon in NavActns:
    #         btn = QPushButton(label, self)
    #         btn.setIcon(icon)
    #         btn.clicked.connect(lambda _, l=label: self._handleAction(l))
    #         innerNavLayout.addWidget(btn)

    #         if label == "Save":
    #             self.btnCommit = btn
    #     # CRUD
    #     innerCRUDLayout = QHBoxLayout()
    #     for label, icon in CRUDActns:
    #         btn = QPushButton(label, self)
    #         btn.setIcon(icon)
    #         btn.clicked.connect(lambda _, l=label: self._handleAction(l))
    #         innerCRUDLayout.addWidget(btn)

    #         if label == "Save":
    #             self.btnCommit = btn

    #     self.layoutButtons.addLayout(innerNavLayout)
    #     if layoutHorizontal:
    #         self.layoutButtons.addSpacing(20)
    #     self.layoutButtons.addLayout(innerCRUDLayout)
    # # _addNavButtons
    # # TODO: do structure similar to _addActionButtons to allow custom button sets and define Action handlers
    # def _handleAction(self, action: str) -> None:
    #     # Generic action dispatch — override if needed
    #     ActionHandlers = {
    #             "add": self.on_add_clicked,
    #             "save": self.on_save_clicked,
    #             "delete": self.on_delete_clicked,
    #             'cancel': self.on_cancel_clicked,
    #         }
    #     action = action.lower()
    #     if action in ActionHandlers:
    #         ActionHandlers[action]()
    #     else:
    #         print(f"Unknown action: {action}")
    #         self.showError(f"Unknown action: {action}")
    #     #endif action
    # _handleAction

    # @Slot()
    # def on_cancel_clicked(self):
    #     # subforms don't have a cancel button
    #     return
    # cancel_record

    ##########################################
    ########    Create

    # def on_add_clicked(self):
    #     self.add_row()
    # add_record

    ##########################################
    ########    Read / Navigation

    # don't need these, right?

    ##########################################
    ########    Update

    # @Slot()
    # def on_save_clicked(self, *_):
    #     """
    #     Collects field values from adapters/subforms, writes them into currRec,
    #     and persists via a short-lived session.
    #     """
    #     self.saveToRecord(self._parentRec)
    # save_record

    ##########################################
    ########    Delete

    # @Slot()
    # def on_delete_clicked(self):
    # # override - remove from list, rather than load another record
    #     self.del_row()
    #     return
    # delete_record

    # ##########################################
    # ########    CRUD support

    @Slot()
    def setDirty(self, wdgt, dirty: bool = True):
        # rethink - adapters handle their own dirty state
        # so all that needs to be set here is self.dirty
        # right?

        # better yet, self doesn't need to track its dirty state
        # since  isDirty will poll children

        # keep an eye on the time the polling takes
        # if it's excessive, find the best way to record child dirty states

        return
    # setFormDirty

    def isDirty(self) -> bool:
        # poll children; if one is Dirty, form is Dirty
        # for rec in _rcrdDisplArea.children():
        for FmElement in self.children():
            if not isinstance(FmElement, cSimpRecFmElement_Base):
                continue
            elif FmElement.isDirty():
                return True
            else:
                continue
        #endfor FmElement in self.children():

        return False
    # del_row

    # TODO: implement idDirty, setDirty, etc
        
#endclass cSubRecordForm2
