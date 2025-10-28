from typing import (Dict, List, Any, Type, )
from collections.abc import (Callable, )
from functools import (partial, )

from PySide6.QtCore import (
    Qt, Slot, Signal, 
    QRect, 
    QStringListModel, 
    )
from PySide6.QtGui import (
    QFont, 
    )
from PySide6.QtWidgets import (
    QWidget,
    QCompleter, 
    QScrollArea, QFrame, QLayout,  QVBoxLayout, QHBoxLayout, QGridLayout, QLayoutItem, 
    QTabWidget,
    QTableView, QHeaderView, 
    QLabel, QLineEdit,  QComboBox, QPushButton, QCheckBox, QTextEdit, QPlainTextEdit, QDateEdit, 
    )

from sqlalchemy import (select, )
from sqlalchemy.orm import (Session, sessionmaker, )

from .cQModels import (SQLAlchemyTableModel, )

from app.database import app_Session


class cDataList(QLineEdit):
    """
    A LineEdit box that acts like an HTML DataList
    Choice matches are choices which contain the input string, case-insensitive
    
    caller should connect the editingFinished signal to a slot which is aware of the cDataList
        and is in scope to call cDataList.selectedItem
    ex: self.testdatalist.editingFinished.connect(self.showHBLChosen)

    Args:
        choices:Dict[Any, str], {key: 'value to display/lookup'}
        initval:str = '', (not currently implemented)
        parent:QWidget=None

    def selectedItem(self):
        returns the following dictionary: 
        return {'keys': [key for key, t in self.choices.items() if t==self.text()], 'text': self.text()}
        (all keys matching the text input)
    """
    def __init__(self, choices:Dict[Any, str], initval:str = '', parent:QWidget|None = None):
        super().__init__(initval, parent)

        self.choices = choices
        
        self.setClearButtonEnabled(True)
        
        choices_to_present = list(choices.values())
        qCompleterObj = QCompleter(QStringListModel(choices_to_present, self), self)
        qCompleterObj.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        qCompleterObj.setFilterMode(Qt.MatchFlag.MatchContains)
        qCompleterObj.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        
        self.setCompleter(qCompleterObj)
    # __ init__
    
    def selectedItem(self):
        """
        def selectedItem(self):
            returns the following dictionary: 
            return {'keys': [key for key, t in self.choices.items() if t==self.text()], 'text': self.text()}
            (all keys matching the text input)
        """
        return {'keys': [key for key, t in self.choices.items() if t==self.text()], 'text': self.text()}
    # selectedItem
    
    def addChoices(self, choices:Dict[Any, str]):
        self.choices.update(choices)
        
        choices_to_present = list(self.choices.values())
        newmodel = QStringListModel(choices_to_present, self)
        self.completer().setModel(newmodel)
    # addChoices
    
    def setChoice(self, choiceKey:Any):
        if choiceKey in self.choices:
            self.setText(self.choices[choiceKey])
        else:
            self.setText('')
    # setChoice

class cComboBoxFromDict(QComboBox):
    """
    Generates QComboBox from dictionary

    Args:
        dict (Dict): The input dictionary. The values will be the data returned by currentData, and
            the keys will be the values shown in the QComboBox
        parent (QWidget) default None
    
    """
    _combolist:List = []
    
    def __init__(self, dict:Dict|None, parent:QWidget|None = None):
        super().__init__(parent)
        
        # don't do completers - assume underlying QComboBox is non-editable
        # choices_to_present = list(dict)
        # qCompleterObj = QCompleter(QStringListModel(choices_to_present, self), self)
        # qCompleterObj.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        # qCompleterObj.setFilterMode(Qt.MatchFlag.MatchContains)
        # qCompleterObj.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        # self.setCompleter(qCompleterObj)
        
        if dict is None:
            dict = {}
        self.replaceDict(dict)

    def replaceDict(self, dict:Dict[str, Any]):
        self.clear()
        self._combolist.clear()
        if isinstance(dict,Dict):
            for key, val in dict.items():
                self.addItem(key,val)
                self._combolist.append({key:val})

#########################################        

# cQRecordsetView - Scrollable layout of records
class cQRecordsetView(QWidget):
    _newdgt_fn:Callable[[], QWidget]|None = None
    _btnAdd:QPushButton|None = None
    def __init__(self, newwidget_fn:Callable[[], QWidget]|None = None, parent=None):
        """
        Widget which displays a set of records

        Args:
            newwidget_fn (Callable, optional): . Defaults to None. newwidget_fn() should return a new record 
                in a widget suitable for adding to this layout
            parent (_type_, optional): _description_. Defaults to None.
        """
        super().__init__(parent)
        self._newdgt_fn = newwidget_fn
        self.init_ui()

    def init_ui(self):
        self.mainLayout = QVBoxLayout(self)

        # set up scroll area
        self.scrollarea = QScrollArea(self)
        self.scrollarea.setWidgetResizable(True)
        self.scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.mainLayout.addWidget(self.scrollarea)
    
        # Container widget for the layout
        self.scrollwidget = QWidget()
        # layout for the scrollwidget
        self.scrolllayout = QVBoxLayout(self.scrollwidget)
        # # Set container as the scroll area widget
        self.scrollarea.setWidget(self.scrollwidget)

        if self._newdgt_fn:
            self._btnAdd = QPushButton(self.scrollwidget)
            self._btnAdd.setObjectName('AddBtnQRS')
            self._btnAdd.setText('\nAdd\n')
            self._btnAdd.clicked.connect(self.addBtnClicked)
            self.scrolllayout.addWidget(self._btnAdd)

        self.init_recSet()
    # init_ui

    def setAddText(self, addText:str = '\nAdd\n'):
        ...
    # setAddText

    def addWidget(self, wdgt:QWidget):
        insAt = self.scrolllayout.count()-1 if self._newdgt_fn else -1
        self.scrolllayout.insertWidget(insAt, wdgt)
        line = QFrame(self)
        myWidth = self.geometry().width()
        line.setGeometry(QRect(0, 0, myWidth, 3))
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self.scrolllayout.insertWidget(insAt+1, line)
    # addWidget

    # addLayout needed?

    def init_recSet(self):
        # remove all widgets from scrolllayout
        # for wdgt in self.scrolllayout:
        idx = 0
        child = self.scrolllayout.itemAt(idx)
        while child != None:
            if child.widget() == self._btnAdd:   # don't removew the Add Button!
                idx += 1
            else:
                widg = self.scrolllayout.takeAt(idx)
                widg.widget().deleteLater() # del the widget
            # endif child == self._btnAdd
            child = self.scrolllayout.itemAt(idx)
    # init_recSet
    
    @Slot()
    def addBtnClicked(self):
        if callable(self._newdgt_fn):
            self.addWidget(self._newdgt_fn())
    # addBtnClicked

############################################################
############################################################

def clearLayout(layout: QLayout, keepItems: List[QLayoutItem|QWidget|QLayout]|None = None) -> None:
    """
    Remove all items from `layout` except those explicitly listed in `keepItems`.
    - Widgets are detached and scheduled for deletion via deleteLater().
    - Nested layouts are cleared recursively and deleted.
    - Spacer items are simply discarded.
    """
    keep = set(keepItems or [])

    i = 0
    while i < layout.count():
        item = layout.itemAt(i)

        # Keep this item in the layout—skip over it.
        if item in keep:
            i += 1
            continue

        # Remove from layout (do NOT increment i here; items shift left)
        item = layout.takeAt(i)

        w = item.widget()
        if w is not None:
            # Detach and delete the widget
            w.setParent(None)
            w.deleteLater()
            del item
            continue

        child_layout = item.layout()
        if child_layout is not None:
            # Recursively clear and delete the child layout
            clearLayout(child_layout, keepItems)
            child_layout.setParent(None)
            child_layout.deleteLater()
            del item
            continue

        # Spacer or other non-widget item: just drop the reference
        del item
        
def cstdTabWidget() -> QTabWidget:
    """Return a standard QTabWidget for use in the form layout."""
    tabwidget = QTabWidget()
    # tabwidget.setTabPosition(QTabWidget.TabPosition.North)
    tabwidget.setMovable(False)
    tabwidget.setTabsClosable(False)
    tabwidget.setDocumentMode(True)
    tabwidget.setTabBarAutoHide(True)
    return tabwidget
# _cSRF_stdTabWidget

class cGridWidget(QWidget):
    """
    A QWidget containing a grid layout, optionally scrollable.
    Adds convenience methods to interact directly with the internal grid.
    """
    def __init__(self, scrollable: bool = False, parent: QWidget|None = None):
        super().__init__(parent)
        
        self._scrollable = scrollable
        
        # Always create the grid, as it's the core content
        thegrid = QGridLayout()
        
        if self._scrollable:
            # 1. Container for the grid
            container = QWidget()
            container.setLayout(thegrid)
            
            # 2. Scroller widget
            thescroller = QScrollArea()
            thescroller.setWidgetResizable(True)
            thescroller.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            thescroller.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            thescroller.setWidget(container)
            
            # 3. Main layout for the cGridWidget itself
            mainlayout = QVBoxLayout(self)
            mainlayout.setContentsMargins(0, 0, 0, 0) # Often useful when nesting containers
            mainlayout.addWidget(thescroller)
        else:
            # If not scrollable, the grid is the main layout
            mainlayout = thegrid
        # endif scrollable
            
        self.setLayout(mainlayout)

        # Store the grid for external access
        self._grid: QGridLayout = thegrid
        
        # --- API Redirection ---
        # Note: You can also use a property or __getattr__ for a cleaner redirection,
        # but direct assignment is simple and effective.
        self.addWidget = self._grid.addWidget
        self.addLayout = self._grid.addLayout
        self.columnCount = self._grid.columnCount
        self.rowCount = self._grid.rowCount
        self.itemAt = self._grid.itemAt
        self.itemAtPosition = self._grid.itemAtPosition    
    # __ init__
    
    def grid(self) -> QGridLayout:
        """Return the internal QGridLayout."""
        return self._grid    
    # grid
# cGridWidget