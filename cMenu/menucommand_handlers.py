from typing import (Dict, List, Mapping, Tuple, Any, )
import copy

from PySide6.QtCore import (Qt, QObject,
    Signal, Slot, 
    QAbstractTableModel, QModelIndex, )
# from PySide6.QtSql import (QSqlRecord, QSqlQuery, QSqlQueryModel, QSqlDatabase, )
# from PySide6.QtSql import (QSqlQueryModel, )
from PySide6.QtGui import (QFont, QIcon, )
from PySide6.QtWidgets import ( QBoxLayout, QLayout, QStyle, QTabWidget, 
    QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, QFormLayout, QFrame, 
    QTableView, QHeaderView, QScrollArea,
    QDialog, QMessageBox, QFileDialog, QDialogButtonBox,
    QLabel, QLCDNumber, QLineEdit, QTextEdit, QPlainTextEdit, QPushButton, QCheckBox, QComboBox, 
    QRadioButton, QGroupBox, QButtonGroup, 
    QSizePolicy, 
    )

from openpyxl import Workbook
from sqlalchemy import (inspect, select, Engine, ) 
from sqlalchemy.orm import (make_transient, sessionmaker, )
from sqlalchemy.orm.session import make_transient


# there's no need to import cMenu, plus it's a circular ref - cMenu depends heavily on this module
# from .kls_cMenu import cMenu 

from _newcode import _NUM_menuBUTTONS, Nochoice
from cMenu.utils import areYouSure, cComboBoxFromDict, cSimpleRecordForm_Base, cstdTabWidget
from menuformname_viewMap import FormNameToURL_Map

from .database import cMenu_Session
from .dbmenulist import (MenuRecords, newgroupnewmenu_menulist, newmenu_menulist, )
from sysver import sysver
from .menucommand_constants import MENUCOMMANDS, COMMANDNUMBER
from .models import (menuItems, menuGroups, )
from .utils import (cComboBoxFromDict, cQFmFldWidg, cQFmNameLabel, cQFmNameLabel,
    SQLAlchemyTableModel, SQLAlchemySQLQueryModel,
    UnderConstruction_Dialog, areYouSure,
    Excelfile_fromqs, ExcelWorkbook_fileext,
    pleaseWriteMe,  
    )


# copied from cMenu - if you change it here, change it there
_NUM_menuBUTTONS:int = 20
_NUM_menuBUTNCOLS:int = 2
_NUM_menuBTNperCOL: int = int(_NUM_menuBUTTONS/_NUM_menuBUTNCOLS)

Nochoice = {'---': None}    # only needed for combo boxes, not datalists

# fontFormTitle = QFont()
# fontFormTitle.setFamilies([u"Copperplate Gothic"])
# fontFormTitle.setPointSize(24)


def FormBrowse(parntWind, formname, *args, **kwargs) -> Any|None:
    urlIndex = 0
    viewIndex = 1

    # theForm = 'Form ' + formname + ' is not built yet.  Calvin needs more coffee.'
    theForm = None
    # formname = formname.lower()
    if formname in FormNameToURL_Map:
        if FormNameToURL_Map[formname][urlIndex]:
            # figure out how to repurpose this later
            # url = FormNameToURL_Map[formname][urlIndex]
            # try:
            #     theView = resolve(reverse(url)).func
            #     urlExists = True
            # except (Resolver404, NoReverseMatch):
            #     urlExists = False
            # # end try
            # if urlExists:
            #     theForm = theView(req)
            # else:
            #     formname = f'{formname} exists but url {url} '
            # #endif
            pass
        elif FormNameToURL_Map[formname][viewIndex]:
            fn = None
            try:
                fn = FormNameToURL_Map[formname][viewIndex]
                theForm = fn(*args, **kwargs)
            except NameError:
                # fn = None
                formname = f'{formname} exists but view {FormNameToURL_Map[formname][viewIndex]}'
            #end try
    if not theForm:
        formname = f'Form {formname} is not built yet.  Calvin needs more coffee.'
        # print(formname)
        UnderConstruction_Dialog(parntWind, formname).show()
    else:
        # print(f'about to show {theForm}')
        # theForm.show()
        # print(f'done showing')
        return theForm
    # endif

    # must be rendered if theForm came from a class-based-view
    # if hasattr(theForm,'render'): theForm = theForm.render()
    # return theForm

def ShowTable(parntWind, tblname):
    # showing a table is nothing more than another form
    return FormBrowse(parntWind,tblname)

#####################################################
#####################################################

class QWGetSQL(QWidget):
    runSQL = Signal(str)    # Emitted with the SQL string when run is clicked
    cancel = Signal()       # Emitted when cancel is clicked    
    
    def __init__(self, parent = None):
        super().__init__(parent)

        font = QFont()
        font.setPointSize(12)
        self.setFont(font)
        
        self.layoutForm = QVBoxLayout(self)
        
        # Form Header Layout
        self.layoutFormHdr = QVBoxLayout()
        
        self.lblFormName = cQFmNameLabel()
        self.lblFormName.setText(self.tr('Enter SQL'))
        self.setWindowTitle(self.tr('Enter SQL'))
        self.layoutFormHdr.addWidget(self.lblFormName)
        self.layoutFormHdr.addSpacing(20)
        
        # main area for entering SQL
        self.layoutFormMain = QFormLayout()
        self.txtedSQL = QTextEdit()
        self.layoutFormMain.addRow(self.tr('SQL statement'), self.txtedSQL)
        
        # run/Cancel buttons
        self.layoutFormActionButtons = QHBoxLayout()
        self.buttonRunSQL = QPushButton( QIcon.fromTheme(QIcon.ThemeIcon.Computer), self.tr('Run SQL') ) 
        self.buttonRunSQL.clicked.connect(self._on_run_sql_clicked)
        self.layoutFormActionButtons.addWidget(self.buttonRunSQL, alignment=Qt.AlignmentFlag.AlignRight)
        self.buttonCancel = QPushButton( QIcon.fromTheme(QIcon.ThemeIcon.WindowClose), self.tr('Cancel') ) 
        self.buttonCancel.clicked.connect(self._on_cancel_clicked)
        self.layoutFormActionButtons.addWidget(self.buttonCancel, alignment=Qt.AlignmentFlag.AlignRight)
        
        # generic horizontal lines
        horzline = QFrame()
        horzline.setFrameShape(QFrame.Shape.HLine)
        horzline.setFrameShadow(QFrame.Shadow.Sunken)
        horzline2 = QFrame()
        horzline2.setFrameShape(QFrame.Shape.HLine)
        horzline2.setFrameShadow(QFrame.Shadow.Sunken)
        
        # status message
        self.lblStatusMsg = QLabel()
        self.lblStatusMsg.setText('\n\n')
        
        # Hints
        self.lblHints = QPlainTextEdit()
        self.lblHints.setReadOnly(True)

        # read txtHints from file
        hintFile = 'assets/SQLHints.txt'
        try:
            with open(hintFile, 'r', encoding='utf-8') as f:
                txtHints = f.read()
        except Exception:
            txtHints = 'PRAGMA table_list;\nPRAGMA table_xinfo(tablname);'
        self.lblHints.setPlainText(txtHints)
        
        self.layoutForm.addLayout(self.layoutFormHdr)
        self.layoutForm.addLayout(self.layoutFormMain)
        self.layoutForm.addLayout(self.layoutFormActionButtons)
        self.layoutForm.addWidget(horzline)
        self.layoutForm.addWidget(self.lblStatusMsg)
        self.layoutForm.addWidget(horzline2)
        self.layoutForm.addWidget(self.lblHints)
        
    def _on_run_sql_clicked(self):
        # Emit the runSQL signal with the text from the editor.
        sql_text = self.txtedSQL.toPlainText()
        self.runSQL.emit(sql_text)

    def _on_cancel_clicked(self):
        # Emit the cancel signal.
        self.cancel.emit()        

    def closeEvent(self, event):
        self.cancel.emit()  # Emit the signal
        event.accept()  # Accept the close event (allows the window to close)

class QWShowSQL(QWidget):
    ReturnToSQL = Signal()
    closeMe = Signal()
    closeBoth = Signal()
    
    def __init__(self, qmodel:SQLAlchemySQLQueryModel, parent:QWidget|QObject|None = None):
        if isinstance(parent, QWidget) or parent is None:
            super().__init__(parent)

        # save incoming for future use if needed
        self._qmodel = qmodel
        origSQL = qmodel.query()
        # # rowCount will not return true count if not all rows fetched
        # # no longer true?
        # while qmodel.canFetchMore():
        #     qmodel.fetchMore()
        numrows = qmodel.rowCount()
        colNames = [qmodel.headerData(x,Qt.Orientation.Horizontal) for x in range(qmodel.columnCount())]

        font = QFont()
        font.setPointSize(12)
        self.setFont(font)
        
        self.layoutForm = QVBoxLayout(self)
        
        # Form Header Layout
        self.layoutFormHdr = QVBoxLayout()
        
        self.lblFormName = cQFmNameLabel()
        self.lblFormName.setText(self.tr('SQL Results'))
        self.setWindowTitle(self.tr('SQL Results'))
        self.layoutFormHdr.addWidget(self.lblFormName)
        
        self.layoutFormSQLDescription = QFormLayout()
        lblOrigSQL = QLabel()
        lblOrigSQL.setText(origSQL)
        lblnRecs = QLabel()
        lblnRecs.setText(f'{numrows}')
        lblcolNames = QLabel()
        lblcolNames.setText(str(colNames))
        self.layoutFormSQLDescription.addRow('SQL Entered:', lblOrigSQL)
        self.layoutFormSQLDescription.addRow('rows affctd:', lblnRecs)
        self.layoutFormSQLDescription.addRow('cols:', lblcolNames)
        

        # main area for displaying SQL
        self.layoutFormMain = QVBoxLayout()
        
        resultTable = QTableView()
        # resultTable.verticalHeader().setHidden(True)
        header = resultTable.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        # Apply stylesheet to control text wrapping
        resultTable.setStyleSheet("""
        QHeaderView::section {
            padding: 5px;
            font-size: 12px;
            text-align: center;
            white-space: normal;  /* Allow text to wrap */
        }
        """)
        resultTable.setModel(qmodel)
        self.layoutFormMain.addWidget(resultTable)
        
        #  buttons
        self.layoutFormActionButtons = QHBoxLayout()
        self.buttonGetSQL = QPushButton( QIcon.fromTheme(QIcon.ThemeIcon.GoPrevious), self.tr('Back to SQL') ) 
        self.buttonGetSQL.clicked.connect(self._return_to_sql)
        self.layoutFormActionButtons.addWidget(self.buttonGetSQL, alignment=Qt.AlignmentFlag.AlignRight)
        self.buttonDLResults = QPushButton( QIcon.fromTheme(QIcon.ThemeIcon.DocumentSave), self.tr('D/L Results') ) 
        self.buttonDLResults.clicked.connect(self.DLResults)
        self.layoutFormActionButtons.addWidget(self.buttonDLResults, alignment=Qt.AlignmentFlag.AlignRight)
        self.buttonCancel = QPushButton( QIcon.fromTheme(QIcon.ThemeIcon.WindowClose), self.tr('Close') ) 
        self.buttonCancel.clicked.connect(self._on_cancel_clicked)
        self.layoutFormActionButtons.addWidget(self.buttonCancel, alignment=Qt.AlignmentFlag.AlignRight)
        
        # generic horizontal lines
        horzline = QFrame()
        horzline.setFrameShape(QFrame.Shape.HLine)
        horzline.setFrameShadow(QFrame.Shadow.Sunken)
        
        self.layoutForm.addLayout(self.layoutFormHdr)
        self.layoutForm.addLayout(self.layoutFormSQLDescription)
        self.layoutForm.addLayout(self.layoutFormMain)
        self.layoutForm.addWidget(horzline)
        self.layoutForm.addLayout(self.layoutFormActionButtons)
        
        colfctr = 90
        self.setMinimumWidth(colfctr*len(colNames))
        
    @Slot()
    def DLResults(self):
        ExcelFileNamePrefix = "SQLresults"
        # Create a dictionary of records from the model
        row_count = self._qmodel.rowCount()
        col_count = self._qmodel.columnCount()
        column_names = [self._qmodel.headerData(i, Qt.Orientation.Horizontal) for i in range(col_count)]

        Excel_qdict = []
        for row in range(row_count):
            record = {}
            for col in range(col_count):
                value = self._qmodel.data(self._qmodel.index(row, col))
                record[column_names[col]] = value
            Excel_qdict.append(record)

        # Create an Excel workbook and save it
        xlws = Excelfile_fromqs(Excel_qdict)
        filName, _ = QFileDialog.getSaveFileName(self, 
            caption="Enter Spreadsheet File Name",
            filter=f'{ExcelFileNamePrefix}*{ExcelWorkbook_fileext}',
            selectedFilter=f'*{ExcelWorkbook_fileext}'
        )
        if filName and isinstance(xlws, Workbook):
            xlws.save(filName)     
        
    def _return_to_sql(self):
        self.ReturnToSQL.emit()

    def _on_cancel_clicked(self):
        # Emit the cancel signal.
        self.closeBoth.emit()        

    def closeEvent(self, event):
        self.closeMe.emit()  # Emit the signal
        event.accept()  # Accept the close event (allows the window to close)
    
class cMRunSQL(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.inputSQL:str|None = None
        # self.qmodel:QSqlQueryModel|None = None
        self.colNames:str|List[str]|None = None
        self.wndwAlive:Dict[str,bool] = {}
        
        self.wndwGetSQL = QWGetSQL(parent)
        self.wndwGetSQL.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.wndwGetSQL.runSQL.connect(self.rawSQLexec)
        self.wndwGetSQL.cancel.connect(self._on_cancel)
        self.wndwAlive['Get'] = True
        self.wndwGetSQL.destroyed.connect(lambda: self.wndwDest('Get'))
        
        # self.wndwShowSQL = None        # will be redefined later

    def wndwDest(self, whichone:str):
        self.wndwAlive[whichone] = False
        
    def show(self):
        self.wndwGetSQL.show()
        
    @Slot(str)
    def rawSQLexec(self, inputSQL:str):
        #TODO: choose session - put in user control
        engine = app_Session.kw["bind"]

        self.qmodel = SQLAlchemySQLQueryModel(inputSQL, engine)

        self.rawSQLshow()
            
    def rawSQLshow(self):
        self.wndwShowSQL = QWShowSQL(self.qmodel, self.parent())
        self.wndwShowSQL.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.wndwShowSQL.ReturnToSQL.connect(self._ShowToGetSQL)
        self.wndwShowSQL.closeBoth.connect(self._on_cancel)

        self.wndwAlive['Show'] = True
        self.wndwShowSQL.destroyed.connect(lambda: self.wndwDest('Show'))


        self.wndwGetSQL.hide()
        self.wndwShowSQL.show()

    @Slot()
    def _ShowToGetSQL(self):
        if self.wndwAlive.get('Show'):
            self.wndwShowSQL.close()
        self.wndwGetSQL.show()
        
    @Slot()
    def _on_cancel(self):
        # Handle the cancellation by closing both windows.
        self._close_all()

    def _close_all(self):
        # Close the child widget if it exists.
        if self.wndwAlive.get('Get'):
            self.wndwGetSQL.close()
        if self.wndwAlive.get('Show'):
            self.wndwShowSQL.close()
        # Close this widget (cMRunSQL) as well.
        self.close()

#############################################
#############################################
#############################################

class cWidgetMenuItem(cSimpleRecordForm_Base):
    """
    cWidgetMenuItem_tst
    -------------------
    A specialized form widget for viewing and editing a single menu item record (menuItems).
    This widget is intended to be used inside a QWidget-based application using PyQt/PySide
    and SQLAlchemy for persistence. It builds a compact edit form from the `fieldDefs`
    mapping and provides common CRUD-related actions appropriate for a menu item:
    - Save changes (commit)
    - Remove the current option
    - Copy or Move the current option to another menu/position
    Notes
    -----
    - This widget expects an SQLAlchemy mapped ORM model `menuItems` and a sessionmaker
        callable `cMenu_Session` to be available and assigned to the class attributes
        `_ORMmodel` and `_ssnmaker` respectively.
    - The widget does not create brand-new menu items in the sense of offering a primary
        "new" flow; it operates on an existing `menuItems` instance supplied at construction.
    - Copy semantics use `copy.deepcopy` followed by `sqlalchemy.orm.session.make_transient`
        to detach the copy before inserting it as a new row. Move semantics create a copy
        and then remove the original row from the database.
    - The widget emits the `requestMenuReload` Signal() whenever a change is made that
        requires other components to refresh their cached menu structures.
    Public attributes (class-level)
    -------------------------------
    - _ORMmodel: ORM model class for menu items (expected: menuItems)
    - _ssnmaker: sessionmaker factory for database transactions (expected: cMenu_Session)
    - fieldDefs: dict mapping field names to widget configuration for form construction
    - requestMenuReload: Qt Signal emitted when a menu reload is required by listeners
    Inner class: cEdtMnuItmDlg_CopyMove_MenuItm
    ------------------------------------------
    A modal QDialog used to prompt the user for a destination Menu Group, Menu ID,
    and Option Number when copying or moving a menu option. It encapsulates all UI and
    validation required to choose a valid destination (e.g., preventing collisions with
    already-defined option numbers):
    Key behaviors / API:
    - __init__(menuGrp:int, menuID:int, optionNumber:int, parent:QWidget|None)
        Constructs the dialog initializing comboboxes for menu groups, menus, and options.
    - dictmenuGroup() -> Dict[str,int]
        Returns mapping of menu group names to ids using the cMenu_Session.
    - dictmenus(mnuGrp:int) -> Mapping[str, int|None]
        Returns mapping of main-menu OptionText -> MenuID for menus in the supplied group.
    - dictmenuOptions(mnuID:int) -> Mapping[str, int|None]
        Returns the set of available option numbers (as strings) for a target menu id,
        excluding option numbers already defined in that menu.
    - loadMenuIDs(idx:int), loadMenuOptions(idx:int), menuOptionChosen(idx:int)
        Slots used to cascade the combobox population and enable/disable the Ok button.
    - enableOKButton()
        Enables the Ok button only when a Group, Menu and Option are all selected.
    - exec_CM_MItm() -> Tuple[int|bool, bool, Tuple[int,int,int]]
        Executes the dialog (modal) and returns a tuple:
            (exec_result, is_copy_bool, (chosenGroup, chosenMenu, chosenOption))
        where exec_result is the QDialog exec() return, and is_copy_bool is True for Copy,
        False for Move.
    Public instance methods (high-level)
    ------------------------------------
    - __init__(menuitmRec: menuItems, parent: QWidget|None = None)
        Initialize the widget to operate on the provided menu item ORM instance. The
        supplied record is considered the "current record" for subsequent operations.
    - _buildFormLayout() -> tuple[QBoxLayout, QTabWidget, QBoxLayout|None]
        Internal layout builder that returns tuple of left tab widget and right layout
        containers used by the base form assembly.
    - _addActionButtons()
        Constructs and wires action buttons (Save Changes, Copy / Move, Remove) and places
        them into the widget's button layout. Buttons are connected to on_save_clicked,
        copyMenuOption, and on_delete_clicked respectively.
    - _handleActionButton(action: str) -> None
        Overridden no-op; action routing is handled locally.
    - _finalizeMainLayout()
        Assembles form, action buttons, and other parts into the main layout.
    - fillFormFromcurrRec()
        Populate the form widgets from the currently-bound record. Also updates button
        enablement: Copy/Move and Remove are disabled for new (unsaved) records.
    - initialdisplay()
        Convenience method that calls fillFormFromcurrRec() to prime the UI.
    - on_delete_clicked() -> None
        Slot executed when the Remove button is clicked. Behavior:
            - Confirms deletion with the user (via areYouSure).
            - Loads the persistent record by primary key and deletes it in a session, then commits.
            - Reinitializes the current record object kept by the widget and restores the
                MenuGroup/MenuID/OptionNumber values so the user can create or reassign a new
                option in the same slot if desired.
            - Emits requestMenuReload to inform listeners that menu data changed.
        Preconditions:
            - self._ssnmaker (class attribute) must be available.
            - self._ORMmodel must refer to the mapped ORM model.
    - copyMenuOption() -> None
        Slot launched by the Copy / Move button. Behavior:
            - Opens the inner cEdtMnuItmDlg_CopyMove_MenuItm dialog to request a destination.
            - If the user accepts:
                    * Creates a deep-copy of the in-memory record, detaches it (make_transient),
                        resets primary keys and target MenuGroup/MenuID/OptionNumber, and inserts it
                        into the database (session.add + commit).
                    * If the Move option was selected, deletes the original persistent record and
                        refreshes the widget's current record to a fresh, unpersisted instance bound
                        to the same original MenuGroup/MenuID/OptionNumber (so the UI remains stable).
            - Emits requestMenuReload when a move occurs (or when appropriate after copy).
        Implementation details:
            - The copy preserves relationships where deepcopy copies them; using make_transient
                is necessary to convert the copy into a state suitable for insertion.
            - The code ensures the sessionmaker and ORMmodel exist before performing DB actions.
    Signals
    -------
    - requestMenuReload: emitted after operations that require other UI components to
        reload/rebuild menus (e.g., delete, move).
    Error handling and assumptions
    ------------------------------
    - The widget assumes a working SQLAlchemy environment and valid ORM mappings for
        menuGroups and menuItems.
    - Database operations are transactional and use the provided cMenu_Session context.
    - UI routines assume typical Qt widget behavior and that combobox widgets expose
        .currentData(), .currentIndex(), .replaceDict(), .setCurrentIndex(), .clear() etc.
        (cComboBoxFromDict is expected to implement replaceDict and to use the data role
        for stored ids).
    - The widget will do nothing (no exception) if invoked when there is no current record,
        or if required class attributes (sessionmaker/ORM model) are not set; assertions are
        used in some code paths to surface incorrect configuration early.
    Example use
    -----------
    Create an instance of the widget bound to a loaded menuItems ORM instance and add it
    to a parent container. Wire to requestMenuReload to update surrounding UI:
            w = cWidgetMenuItem_tst(my_menuitem_record, parent=some_parent_widget)
            w.requestMenuReload.connect(on_reload_needed)
    This docstring documents the public behaviors and expectations of cWidgetMenuItem_tst.
    """
    _ORMmodel = menuItems
    _ssnmaker = cMenu_Session
    fieldDefs = {
        'OptionNumber': {'label': 'Option Number', 'widgetType': QLineEdit, 'position': (0,0), 'noedit': True, 'readonly': True, 'frame': False, 'maximumWidth': 25, 'focusPolicy': Qt.FocusPolicy.NoFocus, 'focusable': Qt.FocusPolicy.NoFocus, },
        'OptionText': {'label': 'OptionText', 'widgetType': QLineEdit, 'position': (0,1,1,2)},
        'TopLine': {'label': 'Top Line', 'widgetType': QCheckBox, 'position': (0,3,1,2), 'lblChkBxYesNo': {True:'YES', False:'NO'}, },
        'BottomLine': {'label': 'Btm Line', 'widgetType': QCheckBox, 'position': (0,5), 'lblChkBxYesNo': {True:'YES', False:'NO'}, },
        'Command': {'label': 'Command', 'widgetType': cComboBoxFromDict, 'choices': vars(COMMANDNUMBER), 'position': (1,0,1,2)},
        'Argument': {'label': 'Argument', 'widgetType': QLineEdit, 'position': (1,2,1,2), },
        'PWord': {'label': 'Password', 'widgetType': QLineEdit, 'position': (1,4,1,2), },
    }

    # formFields:Dict[str, QWidget] = {}

    requestMenuReload:Signal = Signal()

    class cEdtMnuItmDlg_CopyMove_MenuItm(QDialog):
        intCMChoiceCopy:int = 10
        intCMChoiceMove:int = 20

        def __init__(self, menuGrp:int, menuID:int, optionNumber:int, parent = None):   # parent:QWidget = None
            super().__init__(parent)

            self.setWindowModality(Qt.WindowModality.WindowModal)
            self.setWindowTitle(parent.windowTitle() if parent else 'Copy/Move Menu Item')

            self.dlgButtons = None # self.dlgButtons:QDialogButtonBoxto be defined later, but must exist now

            lblDlgTitle = QLabel(self.tr(f' Copy or Move Menu Item {menuID}, {optionNumber}'))

            ##################################################
            # set up menuGroup, menuID, menuOption comboboxes
            layoutNewItemID = QGridLayout()

            lblMenuGroupID = QLabel(self.tr('Menu Group'))
            self.combobxMenuGroupID = cComboBoxFromDict(self.dictmenuGroup(), parent=self)
            self.combobxMenuGroupID.activated.connect(self.loadMenuIDs)

            lblMenuID = QLabel(self.tr('Menu'))
            self.combobxMenuID = cComboBoxFromDict(dict(self.dictmenus(menuGrp)), parent=self)
            # self.loadMenuIDs(menuGrp) - not necessary - done with initialization
            self.combobxMenuID.activated.connect(self.loadMenuOptions)

            lblMenuOption = QLabel(self.tr('Option'))
            self.combobxMenuOption = cComboBoxFromDict({}, parent=self)
            self.combobxMenuOption.activated.connect(self.menuOptionChosen)

            layoutNewItemID.addWidget(lblMenuGroupID,0,0)
            layoutNewItemID.addWidget(self.combobxMenuGroupID,1,0)
            layoutNewItemID.addWidget(lblMenuID,0,1)
            layoutNewItemID.addWidget(self.combobxMenuID,1,1)
            layoutNewItemID.addWidget(lblMenuOption,0,2)
            layoutNewItemID.addWidget(self.combobxMenuOption,1,2)

            self.combobxMenuGroupID.setCurrentIndex(self.combobxMenuGroupID.findData(menuGrp))
            self.loadMenuIDs(menuGrp)
            ##################################################            

            visualgrpboxCopyMove = QGroupBox(self.tr("Copy / Move"))
            layoutgrpCopyMove = QHBoxLayout()
            # Create radio buttons
            radioCopy = QRadioButton(self.tr("Copy"))
            radioMove = QRadioButton(self.tr("Move"))
            # Add radio buttons to the layout
            layoutgrpCopyMove.addWidget(radioCopy)
            layoutgrpCopyMove.addWidget(radioMove)
            visualgrpboxCopyMove.setLayout(layoutgrpCopyMove)
            # Create a QButtonGroup for logical grouping
            self.lgclbtngrpCopyMove = QButtonGroup()
            self.lgclbtngrpCopyMove.addButton(radioCopy, id=self.intCMChoiceCopy)
            self.lgclbtngrpCopyMove.addButton(radioMove, id=self.intCMChoiceMove)
            # Add the QGroupBox to the main layout

            self.dlgButtons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel,
                Qt.Orientation.Horizontal,
                )
            self.dlgButtons.accepted.connect(self.accept)
            self.dlgButtons.rejected.connect(self.reject)
            self.dlgButtons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

            layoutMine = QVBoxLayout()
            layoutMine.addWidget(lblDlgTitle)
            layoutMine.addWidget(visualgrpboxCopyMove)
            layoutMine.addLayout(layoutNewItemID)
            layoutMine.addWidget(self.dlgButtons)

            self.setLayout(layoutMine)

        def dictmenuGroup(self) -> Dict[str, int]:
            # TODO: generalize this to work with any table (return a dict of {id:record})
            stmt = select(menuGroups.GroupName, menuGroups.id).select_from(menuGroups).order_by(menuGroups.GroupName)
            with cMenu_Session() as session:
                retDict = {row.GroupName: row.id for row in session.execute(stmt).all()}
            return retDict
        def dictmenus(self, mnuGrp:int) -> Mapping[str, int|None]:
            stmt = select(menuItems.OptionText, menuItems.MenuID).select_from(menuItems).where(
                menuItems.MenuGroup_id == mnuGrp,
                menuItems.OptionNumber == 0,  # only return the main menu items
            ).order_by(menuItems.OptionText)
            with cMenu_Session() as session:
                rs = session.execute(stmt).all()
                # Nochoice = {'---': None}  # only needed for combo boxes, not datalists
                retDict = Nochoice | {row.OptionText: row.MenuID for row in rs}
            return retDict      # type: ignore
        def dictmenuOptions(self, mnuID:int) -> Mapping[str, int|None]:
            mnuGrp:int = self.combobxMenuGroupID.currentData()
            stmt = select(menuItems.OptionNumber).select_from(menuItems).where(
                menuItems.MenuID == mnuID,
                menuItems.MenuGroup_id == mnuGrp,
            )
            with cMenu_Session() as session:
                rs = session.execute(stmt).all()
                definedOptions = [rec.OptionNumber for rec in rs]
            # Nochoice = {'---': None}  # only needed for combo boxes, not datalists
            return Nochoice | { str(n+1): n+1 for n in range(_NUM_menuBUTTONS) if n+1 not in definedOptions }

        @Slot()
        def loadMenuIDs(self, idx:int):
            mnuGrp:int = self.combobxMenuGroupID.currentData()
            # if self.combobxMenuGroupID.currentIndex() != -1:
            if mnuGrp is not None:
                self.combobxMenuID.replaceDict(dict(self.dictmenus(mnuGrp)))
            self.combobxMenuID.setCurrentIndex(-1)
            self.combobxMenuOption.clear()
            self.enableOKButton()
        @Slot()
        def loadMenuOptions(self, idx:int):
            mnuID:int = self.combobxMenuID.currentData()
            #if self.combobxMenuID.currentIndex() != -1:
            if mnuID is not None:
                self.combobxMenuOption.replaceDict(dict(self.dictmenuOptions(mnuID)))
            self.combobxMenuOption.setCurrentIndex(-1)
            self.enableOKButton()
        @Slot()
        def menuOptionChosen(self, idx:int):
            self.enableOKButton()
        def enableOKButton(self):
            if not self.dlgButtons:
                return
            all_GrpIdOption_chosen = all([
                self.combobxMenuGroupID.currentIndex() != -1,
                self.combobxMenuID.currentIndex() != -1,
                self.combobxMenuOption.currentIndex() != -1,
            ])
            self.dlgButtons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(all_GrpIdOption_chosen)

        def exec_CM_MItm(self) -> Tuple[int|bool, bool, Tuple[int, int, int]]:
            ret = super().exec()
            copymove = self.lgclbtngrpCopyMove.checkedId()
            chosenMenuGroup = self.combobxMenuGroupID.currentData()
            chosenMenuID = self.combobxMenuID.currentData()
            chosenMenuOption = self.combobxMenuOption.currentData()
            return (
                ret,
                copymove != self.intCMChoiceMove,   # True unless Move checked
                # return (Group, Menu, OptrNum) tuple
                (chosenMenuGroup, chosenMenuID, chosenMenuOption),
                )


    def __init__(self, menuitmRec:menuItems, parent:QWidget = None):   # type: ignore

        self.setcurrRec(menuitmRec)
        super().__init__(parent=parent)

        font = QFont()
        font.setPointSize(7)
        self.setFont(font)

        self.setObjectName('cWidgetMenuItem')

    # __init__

    ##########################################
    ########    Layout

    def _buildFormLayout(self) -> tuple[QBoxLayout, QTabWidget, QBoxLayout | None]:
        layoutFormMain = QHBoxLayout(self)
        layoutFormMain.setContentsMargins(0,0,0,0)
        layoutFormMain.setSpacing(0)

        layoutFormMainLeft = cstdTabWidget()
        layoutFormMainLeft.setContentsMargins(0,0,0,0)

        layoutFormMainRight = QVBoxLayout()
        layoutFormMainRight.setContentsMargins(0,0,0,0)
        layoutFormMainRight.setSpacing(0)

        return layoutFormMain, layoutFormMainLeft, layoutFormMainRight
    # _buildFormLayout

    def _addActionButtons(self):
        self.btnCommit = QPushButton(self.tr('Save\nChanges'), self)
        self.btnCommit.clicked.connect(self.on_save_clicked)
        # self.btnCommit.setFixedSize(60, 30)  # Adjust width and height
        self.btnCommit.setStyleSheet("padding: 2px; margin: 0;")  # Remove extra padding

        self.btnMoveCopy = QPushButton(self.tr('Copy / Move'), self)
        self.btnMoveCopy.clicked.connect(self.copyMenuOption)
        # self.btnMoveCopy.setFixedSize(60, 30)  # Adjust width and height
        self.btnMoveCopy.setStyleSheet("padding: 2px; margin: 0;")  # Remove extra padding

        self.btnRemove = QPushButton(self.tr('Remove'), self)
        self.btnRemove.clicked.connect(self.on_delete_clicked)
        # self.btnRemove.setFixedSize(60, 30)  # Adjust width and height
        self.btnRemove.setStyleSheet("padding: 2px; margin: 0;")  # Remove extra padding

        assert isinstance(self.layoutButtons, QBoxLayout), 'layoutButtons must be a Box Layout'
        self.layoutButtons.addWidget(self.btnMoveCopy)
        self.layoutButtons.addWidget(self.btnRemove)
        self.layoutButtons.addWidget(self.btnCommit)
    def _handleActionButton(self, action: str) -> None:
        # we have our own handlers, so no need to handle anything here
        return
    # _addActionButtons, _handleActionButton    

    def _finalizeMainLayout(self):
        assert isinstance(self.layoutMain, QBoxLayout), 'layoutMain must be a Box Layout'

        # lyout = getattr(self, 'layoutFormHdr', None)
        # if isinstance(lyout, QLayout):
        #     self.layoutMain.addLayout(lyout)
        lyout = getattr(self, 'layoutForm', None)
        if isinstance(lyout, QWidget):
            self.layoutMain.addWidget(lyout)
        lyout = getattr(self, 'layoutButtons', None)
        if isinstance(lyout, QLayout):
            self.layoutMain.addLayout(lyout)
        # lyout = getattr(self, '_statusBar', None)
        # if isinstance(lyout, QLayout):
        #     self.layoutMain.addLayout(lyout)            #TODO: more flexibility in where status bar is placed
    # _finalizeMainLayout


    ######################################################
    ########    Display 

    def fillFormFromcurrRec(self):
        super().fillFormFromcurrRec()

        self.btnMoveCopy.setEnabled(not self.isNewRecord())
        self.btnRemove.setEnabled(not self.isNewRecord())
    # fillFormFromRec

    def initialdisplay(self):
        self.fillFormFromcurrRec()
    # initialdisplay()



    ##########################################
    ########    Create

    # this widget doesn't create new records

    ##########################################
    ########    Read


    ##########################################
    ########    Update


    ##########################################
    ########    Delete

    @Slot()
    def on_delete_clicked(self):
        currRec = self.currRec()
        if not currRec:
            return

        mGrp, mnu, mOpt = (currRec.MenuGroup_id, currRec.MenuID, currRec.OptionNumber)

        pKey = self.primary_key()
        keyID = getattr(currRec, pKey.key)

        really = areYouSure(self,
            title="Remove Menu Option?",
            areYouSureQuestion=f'Really remove menu option {mGrp}, {mnu}, {mOpt} ({currRec.OptionText}) ?'
            )
        if really != QMessageBox.StandardButton.Yes:
            return

        # Actually delete
        ssnmkr = self.ssnmaker()
        assert ssnmkr is not None, "Sessionmaker must be set before touching the database"
        modl = self.ORMmodel()
        assert modl is not None, "ORMmodel must be set before deleting record"
        with ssnmkr() as session:
            rec = session.get(modl, keyID)
            if rec:
                session.delete(rec)
                session.commit()

        self.initializeRec()
        # preserve MenuGroup, MenuID, OptionNumber
        currRec = self.currRec()
        currRec.MenuGroup_id, currRec.MenuID, currRec.OptionNumber = mGrp, mnu, mOpt

        self.fillFormFromcurrRec()

        self.requestMenuReload.emit()   # let listeners know we need a menu reload
    # delete_record

    ##########################################
    ########    Widget-responding procs

    def copyMenuOption(self):
        cRec = self.currRec()
        mnuGrp, mnuID, optNum = (cRec.MenuGroup_id, cRec.MenuID, cRec.OptionNumber)

        dlg = self.cEdtMnuItmDlg_CopyMove_MenuItm(mnuGrp, mnuID, optNum, self)
        retval, CMChoiceCopy, newMnuID = dlg.exec_CM_MItm()
        if retval:
            # Create a copy (including relationships)
            new_rec = copy.deepcopy(cRec)

            # Detach the copy from the session
            make_transient(new_rec)

            # Reset primary keys
            new_rec.id = None                       # type: ignore
            new_rec.MenuGroup_id = newMnuID[0]      # type: ignore
            new_rec.MenuID = newMnuID[1]            # type: ignore
            new_rec.OptionNumber = newMnuID[2]      # type: ignore

            with cMenu_Session() as session:
                session.add(new_rec)
                session.commit()

            if CMChoiceCopy:
                ... # we've done everything we need to do
            else:
                pk = cRec.id
                rslt = "No record to delete"
                if pk:
                    with cMenu_Session() as session:
                        session.delete(cRec)
                        session.commit()
                #endif pk

                self.initializeRec()
                # preserve MenuGroup, MenuID, OptionNumber
                currRec = self.currRec()
                currRec.MenuGroup_id, currRec.MenuID, currRec.OptionNumber = mnuGrp, mnuID, optNum

                self.fillFormFromcurrRec()

                self.requestMenuReload.emit()   # let listeners know we need a menu reload
            #endif CMChoiceCopy
        # #endif retval

        return
    # copyMenuOption
# class cWidgetMenuItem

class cEditMenu(QWidget):
    # more class constants
    _DFLT_menuGroup: int = -1
    _DFLT_menuID: int = -1
    intmenuGroup:int = _DFLT_menuGroup
    intmenuID:int = _DFLT_menuID
    formFields:Dict[str, QWidget] = {}
    

    class wdgtmenuITEM(cWidgetMenuItem):
        def __init__(self, menuitmRec, parent = None):
            super().__init__(menuitmRec, parent)
            
    class cEdtMnuDlgGetNewMenuGroupInfo(QDialog):
        def __init__(self, parent:QWidget|None = None):
            super().__init__(parent)
            
            self.setWindowModality(Qt.WindowModality.WindowModal)
            self.setWindowTitle(parent.windowTitle() if parent else 'New Menu Group')

            layoutGroupName = QHBoxLayout()
            lblGroupName = QLabel(self.tr('Group Name'))
            self.lnedtGroupName = QLineEdit('New Group', self)
            layoutGroupName.addWidget(lblGroupName)
            layoutGroupName.addWidget(self.lnedtGroupName)

            layoutGroupInfo = QHBoxLayout()
            lblGroupInfo = QLabel(self.tr('Group Info'))
            self.txtedtGroupInfo = QTextEdit(self)
            layoutGroupInfo.addWidget(lblGroupInfo)
            layoutGroupInfo.addWidget(self.txtedtGroupInfo)

            dlgButtons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel,
                Qt.Orientation.Horizontal,
                )
            dlgButtons.accepted.connect(self.accept)
            dlgButtons.rejected.connect(self.reject)            

            layoutMine = QVBoxLayout()
            layoutMine.addLayout(layoutGroupName)
            layoutMine.addLayout(layoutGroupInfo)
            layoutMine.addWidget(dlgButtons)
            
            self.setLayout(layoutMine)
            
        def exec_NewMGInfo(self):
            ret = super().exec()
            # later - prevent lvng if lnedtGroupName blank
            return (
                ret, 
                self.lnedtGroupName.text()         if ret==self.DialogCode.Accepted else None,
                self.txtedtGroupInfo.toPlainText() if ret==self.DialogCode.Accepted else None,
                )
    
    class cEdtMnuDlgCopyMoveMenu(QDialog):
        intCMChoiceCopy:int = 10
        intCMChoiceMove:int = 20
        
        def __init__(self, mnuGrp:int, menuID:int, parent:QWidget|None = None):
            super().__init__(parent)
            
            self.setWindowModality(Qt.WindowModality.WindowModal)
            self.setWindowTitle(parent.windowTitle() if parent else 'Copy/Move Menu')

            lblDlgTitle = QLabel(self.tr(f' Copy or Move Menu {menuID}'))
            
            layoutMenuID = QHBoxLayout()
            lblMenuID = QLabel(self.tr('Menu ID'))
            self.combobxMenuID = QComboBox(self)
            #  definedMenus = menuItems.objects.filter(MenuGroup=mnuGrp, OptionNumber=0).values_list('MenuID', flat=True)
            
            dictDefinedMenus = MenuRecords().recordsetList(['MenuID'], filter=f'MenuGroup_id={mnuGrp} AND OptionNumber=0')   # .objects.filter(MenuGroup=mnuGrp, OptionNumber=0).values_list('MenuID', flat=True)
            definedMenus = [mDict['MenuID'] for mDict in dictDefinedMenus]
            self.combobxMenuID.addItems([str(n) for n in range(256) if n not in definedMenus])
            layoutMenuID.addWidget(lblMenuID)
            layoutMenuID.addWidget(self.combobxMenuID)
            
            visualgrpboxCopyMove = QGroupBox(self.tr("Copy / Move"))
            layoutgrpCopyMove = QHBoxLayout()
            # Create radio buttons
            radioCopy = QRadioButton(self.tr("Copy"))
            radioMove = QRadioButton(self.tr("Move"))
            # Add radio buttons to the layout
            layoutgrpCopyMove.addWidget(radioCopy)
            layoutgrpCopyMove.addWidget(radioMove)
            visualgrpboxCopyMove.setLayout(layoutgrpCopyMove)
            # Create a QButtonGroup for logical grouping
            self.lgclbtngrpCopyMove = QButtonGroup()
            self.lgclbtngrpCopyMove.addButton(radioCopy, id=self.intCMChoiceCopy)
            self.lgclbtngrpCopyMove.addButton(radioMove, id=self.intCMChoiceMove)
            # Add the QGroupBox to the main layout

            dlgButtons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel,
                Qt.Orientation.Horizontal,
                )
            dlgButtons.accepted.connect(self.accept)
            dlgButtons.rejected.connect(self.reject)            

            layoutMine = QVBoxLayout()
            layoutMine.addWidget(lblDlgTitle)
            layoutMine.addWidget(visualgrpboxCopyMove)
            layoutMine.addLayout(layoutMenuID)
            layoutMine.addWidget(dlgButtons)
            
            self.setLayout(layoutMine)
            
        def exec_CMMnu(self):
            ret = super().exec()
            copymove = self.lgclbtngrpCopyMove.checkedId()
            return (
                ret, 
                copymove != self.intCMChoiceMove,   # True unless Move checked
                int(self.combobxMenuID.currentText()) if ret==self.DialogCode.Accepted else None,
                )

    def __init__(self, parent:QWidget|None = None):
        super().__init__(parent)

        self.layoutMain: QBoxLayout = QVBoxLayout(self)
        # self.layoutMain.setContentsMargins(5,5,5,5)        
        self.layoutmainMenu: QGridLayout = QGridLayout()
        self.WmenuItm: Dict[int, cEditMenu.wdgtmenuITEM] = {}
        self.layoutmenuHdr: QHBoxLayout = QHBoxLayout()
        self.layoutmenuHdrLeft: QVBoxLayout = QVBoxLayout()
        self.layoutmenuHdrRight: QVBoxLayout = QVBoxLayout()
        self._menuSOURCE = MenuRecords()
        # self.currentMenu:cQSqlTableModel = None
        self.currentMenu:Dict[int, menuItems] = {}
        self.currRec:menuItems|None = None
        
        self.layoutmainMenu.setColumnStretch(0,1)
        self.layoutmainMenu.setColumnStretch(1,0)
        self.layoutmainMenu.setColumnStretch(2,1)
        
        self.layoutMenuHdrLn1 = QHBoxLayout()
        self.layoutMenuHdrLn2 = QHBoxLayout()

        modlFld='MenuGroup'
        wdgt:cQFmFldWidg = cQFmFldWidg(cComboBoxFromDict, lblText='Menu Group', modlFld=modlFld, 
            choices=self.dictmenuGroup(), parent= self)
        self.formFields[modlFld] = wdgt
        self.fldmenuGroup:cQFmFldWidg = wdgt
        wdgt.signalFldChanged.connect(lambda idx: self.loadMenu(menuGroup=self.fldmenuGroup.Value()))  # type: ignore

        modlFld='GroupName'
        wdgt:cQFmFldWidg = cQFmFldWidg(QLineEdit, lblText='Group Name', modlFld=modlFld, parent=self)
        self.formFields[modlFld] = wdgt
        self.fldmenuGroupName:cQFmFldWidg = wdgt
        wdgt.signalFldChanged.connect(lambda: self.changeField(self.fldmenuGroupName))

        self.btnNewMenuGroup:QPushButton = QPushButton(self.tr('New Menu\nGroup'), self)
        self.btnNewMenuGroup.clicked.connect(self.createNewMenuGroup)

        modlFld='MenuID'
        wdgt:cQFmFldWidg = cQFmFldWidg(cComboBoxFromDict, lblText='menu', modlFld=modlFld, 
            parent=self)
        self.formFields[modlFld] = wdgt
        self.fldmenuID:cQFmFldWidg = wdgt
        wdgt.signalFldChanged.connect(lambda idx: self.loadMenu(menuGroup=self.intmenuGroup, menuID=self.fldmenuID.Value())) # type: ignore

        modlFld='OptionText'
        wdgt:cQFmFldWidg = cQFmFldWidg(QLineEdit, lblText='Menu Name', modlFld='OptionText', parent=self)
        self.formFields[modlFld] = wdgt
        self.fldmenuName:cQFmFldWidg = wdgt
        self.fldmenuName.signalFldChanged.connect(lambda: self.changeField(self.fldmenuName))
        
        self.lblnummenuGroupID:  QLCDNumber = QLCDNumber(3)
        self.lblnummenuGroupID.setMaximumSize(20,20)
        self.lblnummenuID:  QLCDNumber = QLCDNumber(3)
        self.lblnummenuID.setMaximumSize(20,20)

        self.btnRmvMenu:QPushButton = QPushButton(self.tr('Remove Menu'), self)
        self.btnRmvMenu.clicked.connect(self.rmvMenu)
        self.btnCopyMenu:QPushButton = QPushButton(self.tr('Copy/Move\nMenu'), self)
        self.btnCopyMenu.clicked.connect(self.copyMenu)
        
        self.layoutMenuHdrLn1.addWidget(self.fldmenuGroup)
        self.layoutMenuHdrLn1.addWidget(self.lblnummenuGroupID)
        self.layoutMenuHdrLn1.addWidget(self.fldmenuGroupName)
        self.layoutMenuHdrLn1.addWidget(self.btnNewMenuGroup)
        
        self.layoutMenuHdrLn2.addWidget(self.fldmenuID)
        self.layoutMenuHdrLn2.addWidget(self.lblnummenuID)
        self.layoutMenuHdrLn2.addWidget(self.fldmenuName)
        self.layoutMenuHdrLn2.addWidget(self.btnRmvMenu)
        self.layoutMenuHdrLn2.addWidget(self.btnCopyMenu)
        
        self.btnCommit:QPushButton = QPushButton(self.tr('\nSave\nChanges\n'), self)
        self.btnCommit.clicked.connect(self.writeRecord)

        self.layoutmenuHdrLeft.addLayout(self.layoutMenuHdrLn1)
        self.layoutmenuHdrLeft.addLayout(self.layoutMenuHdrLn2)
        self.layoutmenuHdrRight.addWidget(self.btnCommit)
        self.layoutmenuHdrRight.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.layoutmenuHdr.addLayout(self.layoutmenuHdrLeft)
        self.layoutmenuHdr.addLayout(self.layoutmenuHdrRight)
        
        self.layoutMain.addLayout(self.layoutmenuHdr)
    ####
        self.bxFrame:List[QFrame] = [QFrame() for _ in range(_NUM_menuBUTTONS)]
        for bNum in range(_NUM_menuBUTTONS):
            self.bxFrame[bNum].setLineWidth(1)
            self.bxFrame[bNum].setFrameStyle(QFrame.Shape.Box|QFrame.Shadow.Plain)
            y, x = ((bNum % _NUM_menuBTNperCOL), 0 if bNum < _NUM_menuBTNperCOL else 2)
            self.layoutmainMenu.addWidget(self.bxFrame[bNum],y,x)
            
            self.WmenuItm[bNum] = None      # type: ignore  # later - build WmenuItm before this loop?

        layoutManinMenu_wrapperWidget = QWidget()
        layoutManinMenu_wrapperWidget.setLayout(self.layoutmainMenu)
        self.layoutManinMenu_scrollerWidget = QScrollArea()
        self.layoutManinMenu_scrollerWidget.setWidget(layoutManinMenu_wrapperWidget)
        self.layoutManinMenu_scrollerWidget.setWidgetResizable(True)
        self.layoutMain.addWidget(self.layoutManinMenu_scrollerWidget)
        
        self.setWindowTitle(self.tr('Edit Menu'))
                    
        # self.setLayout(self.layoutmainMenu)
        self.loadMenu()
    # __init__

    def dictmenuGroup(self) -> Dict[str, int]:
        rs = MenuRecords().recordsetList(['id', 'GroupName'])
        retDict = {d['GroupName']:d['id'] for d in rs}
        return retDict
    def dictmenus(self, mnuGrp:int) -> Mapping[str, int|None]:
        tbl = MenuRecords()
        rs = tbl.recordsetList(['MenuID', 'OptionText'], f'MenuGroup_id = {mnuGrp} AND OptionNumber = 0')
        retDict = Nochoice | {f"{d['OptionText']} ({d['MenuID']})":d['MenuID'] for d in rs}
        return retDict

    ##########################################
    ########    Create

    def createNewMenuGroup(self):
        dlg = self.cEdtMnuDlgGetNewMenuGroupInfo(self)
        retval, grpName, grpInfo = dlg.exec_NewMGInfo()
        if retval:
            # new menuGroups record
            # create a new menu group
            newrec = menuGroups(
                GroupName=grpName,
                GroupInfo=grpInfo,
            )
            with cMenu_Session() as session:
                session.add(newrec)
                session.commit()
                # get the primary key of the new record
                grppk = newrec.id            

            # create a default menu
            # newgroupnewmenu_menulist to menuItems
            for rec in newgroupnewmenu_menulist:
                # rec is a dict with keys: OptionNumber, OptionText, Command, Argument, PWord, TopLine, BottomLine
                # create a new record in menuItems
                newmenurec = menuItems(
                    MenuGroup_id=grppk,
                    MenuID=0,  # default menu ID
                    OptionNumber=rec['OptionNumber'],
                    OptionText=rec['OptionText'],
                    Command=rec['Command'],
                    Argument=rec['Argument'],
                    PWord=rec['PWord'],
                    TopLine=rec['TopLine'],
                    BottomLine=rec['BottomLine'],
                )
                # save the new record
                with cMenu_Session() as session:
                    session.add(newmenurec)
                    session.commit()
                # add the new record to the menuItems table

            self.loadMenu(grppk, 0)
        return

    def copyMenu(self):
        mnuGrp = self.intmenuGroup
        mnuID = self.intmenuID

        dlg = self.cEdtMnuDlgCopyMoveMenu(mnuGrp, mnuID, self)
        retval, CMChoiceCopy, newMnuID = dlg.exec_CMMnu()
        if retval:
            assert isinstance(newMnuID, int) and newMnuID >= 0, "New Menu ID must be a non-negative integer"
            qsFrom = self.currentMenu
            with cMenu_Session() as session:         
                if CMChoiceCopy:
                    qsTo: Dict[int, menuItems] = {}     # qsTo is technically not used, but being built JIC its needed later
                    for i, orig_rec in qsFrom.items():
                        new_rec = menuItems()
                        for col in menuItems.__table__.columns:
                            name = col.name
                            if name != "id":
                                setattr(new_rec, name, getattr(orig_rec, name))
                        #endfor col in menuItems.__table__.columns

                        new_rec.MenuID = newMnuID
                        session.add(new_rec)
                        qsTo[i] = new_rec     # qsTo is technically not used, but being built JIC its needed later
                    #endfor i, orig_rec in qsFrom.items()
                else:
                    # Move the menu items to the new menu ID
                    for i, orig_rec in qsFrom.items():
                        # Update the MenuID of the original record
                        orig_rec.MenuID = newMnuID
                        session.merge(orig_rec)
                    #endfor i, orig_rec in qsFrom.items()
                #endif CMChoiceCopy
                
                session.commit()                # commit the changes
                
                self.loadMenu(mnuGrp, newMnuID)
                
            #endwith cMenu_Session() as session:
        #endif retval

        return

        
    ##########################################
    ########    Read

    def movetoutil_findrecwithvalue(self, tblModel:Dict[int, menuItems], fld:str, trgtValue) -> menuItems | None:
        # for n in range(tblModel.rowCount()):
        for testrec in tblModel.values():
            # testrec = tblModel.record(n)
            if getattr(testrec, fld) == trgtValue:
                return testrec
            #endif testrec.value(fld) == trgtValue:
        #endwhile not testrec.isEmpty():
        
        return None
    def displayMenu(self):
        menuGroup = self.intmenuGroup
        menuID = self.intmenuID
        menuItemRecs = self.currentMenu
        # menuItemRecs.setFilter('OptionNumber=0')
        # menuHdrRec:QSqlRecord = self.movetoutil_findrecwithvalue(menuItemRecs,'OptionNumber',0)
        menuHdrRec:menuItems = menuItemRecs[0]
        
        # set header elements
        self.lblnummenuGroupID.display(menuGroup)
        self.fldmenuGroup.setValue(str(menuGroup)) # type: ignore

        stmt = select(menuGroups.GroupName).where(menuGroups.id == menuGroup)
        with cMenu_Session() as session:
            result = session.execute(stmt)
            group_name = result.scalar_one_or_none()
        GpName = group_name if group_name else ""

        self.fldmenuGroupName.setValue(GpName) # type: ignore
        self.lblnummenuID.display(menuID)
        d = self.dictmenus(menuGroup)
        self.fldmenuID.replaceDict(dict(d))
        self.fldmenuID.setValue(menuID) # type: ignore
        self.fldmenuName.setValue(menuHdrRec.OptionText) # type: ignore

        for bNum in range(_NUM_menuBUTTONS):
            y, x = ((bNum % _NUM_menuBTNperCOL)+1, 0 if bNum < _NUM_menuBTNperCOL else 2)
            bIndx = bNum+1
            mnuItmRc = self.movetoutil_findrecwithvalue(menuItemRecs, 'OptionNumber', bIndx)
            if not mnuItmRc:
                mnuItmRc = menuItems(
                    MenuGroup_id=menuGroup,
                    MenuID=menuID,
                    OptionNumber=bIndx,
                )
            oldWdg = self.WmenuItm[bNum]
            if oldWdg:
                # remove old widget
                self.layoutmainMenu.removeWidget(oldWdg)
                oldWdg.hide()
                del oldWdg

            self.WmenuItm[bNum] = self.wdgtmenuITEM(mnuItmRc)
            self.WmenuItm[bNum].requestMenuReload.connect(lambda: self.loadMenu(self.intmenuGroup, self.intmenuID))
            self.layoutmainMenu.addWidget(self.WmenuItm[bNum],y,x) 
        # endfor

        mItmH = self.WmenuItm[0].height()
        mItmW = self.WmenuItm[0].width()
        self.layoutManinMenu_scrollerWidget.setMinimumSize(mItmW*2+10, mItmH)
        
     
    # displayMenu

    def loadMenu(self, menuGroup: int = _DFLT_menuGroup, menuID: int = _DFLT_menuID):
        SRC = self._menuSOURCE
        if menuGroup==self._DFLT_menuGroup:
            dfltMenuGroup = SRC.dfltMenuGroup()
            if dfltMenuGroup is None:
                raise ValueError("Default menu group not found.")
            menuGroup = dfltMenuGroup
        if menuID==self._DFLT_menuID:
            dfltMenuID = SRC.dfltMenuID_forGroup(menuGroup)
            if dfltMenuID is None:
                raise ValueError(f"Default menu ID for group {menuGroup} not found.")
            menuID = dfltMenuID

        self.intmenuGroup = menuGroup
        self.intmenuID = menuID
        
        if SRC.menuExist(menuGroup, menuID):
            self.currentMenu = SRC.menuDBRecs(menuGroup, menuID)
            # self.currRec = self.movetoutil_findrecwithvalue(self.currentMenu, 'OptionNumber', 0)
            self.currRec = self.currentMenu[0]  # am I safe in assuming existence?
            self.setFormDirty(self, False)       # should this be in displayMenu ?
            self.displayMenu()
        else:
            # menu doesn't exist; say so
            msg = QMessageBox(self)
            msg.setWindowTitle('Menu Doesn\'t Exist')
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.setText(f'Menu {menuID} doesn\'t exist!')
            msg.open()
    # loadMenu


    ##########################################
    ########    Update

    @Slot()
    def changeField(self, wdgt:cQFmFldWidg) -> bool:
        # move to class var?
        forgnKeys = {   
            'MenuGroup',
            }
        # move to class var?
        valu_transform_flds = {
            'GroupName',
            }
        cRec = self.currRec
        dbField = wdgt.modelField()

        wdgt_value = wdgt.Value()

        if dbField in forgnKeys:
            dbField += '_id'
        if dbField in valu_transform_flds:
            # wdgt_value = valu_transform_flds[dbField][1](wdgt_value)
            pass

        if wdgt_value or isinstance(wdgt_value,bool):
            if dbField != 'GroupName':  # GroupName belongs to cRec.MenuGroup; persist only at final write
                assert cRec is not None, "Current record is None"
                cRec.setValue(str(dbField), wdgt_value)
            self.setFormDirty(wdgt, True)
        
            return True
        else:
            return False
        # endif wdgt_value
    # changeField
    
    @Slot()
    def writeRecord(self):
        if not self.isFormDirty():
            return
        
        cRec = self.currRec
        
        # check other traps later
        
        if self.isWdgtDirty(self.fldmenuGroupName):
            grpstmt = select(menuGroups).where(menuGroups.id == self.intmenuGroup)
            with cMenu_Session() as session:
                groupRec = session.execute(grpstmt).scalar_one_or_none()
                if groupRec is None:
                    print("Menu group not found:", self.intmenuGroup)
                    return
                # update the group name
                groupRec.GroupName = str(self.fldmenuGroupName.Value())
                session.merge(groupRec)
                session.commit()
            #endwith cMenu_Session() as session:
        #endif self.isWdgtDirty(self.fldmenuGroupName)

        if cRec is not None:
            with cMenu_Session() as session:
                session.merge(cRec)
                session.commit()

        self.setFormDirty(self, False)
    # writeRecord


    ##########################################
    ########    Delete

    @Slot()
    def rmvMenu(self):
        
        pleaseWriteMe(self, 'Remove Menu')
        return
        
        (mGrp, mnu, mOpt) = (self.currRec.MenuGroup, self.currRec.MenuID, self.currRec.OptionNumber)
        
        # verify delete
        
        # remove from db
        if self.currRec.pk:
            self.currRec.delete()
        
        # replace with an "next" record
        self.currRec = menuItems_QT(
            MenuGroup = mGrp,
            MenuID = mnu,
            OptionNumber = mOpt,
            )


    ##########################################
    ########    CRUD support

    @Slot()
    def setFormDirty(self, wdgt:QWidget, dirty:bool = True):
        if wdgt.property('noedit'):
            return
        
        wdgt.setProperty('dirty', dirty)
        # if wdgt === self, set all children dirty
        if wdgt is not self:
            if dirty: self.setProperty('dirty',True)
        else:
            for W in self.children():
                if any([W.inherits(tp) for tp in ['QLineEdit', 'QTextEdit', 'QCheckBox', 'QComboBox', 'QDateEdit', ]]):
                    W.setProperty('dirty', dirty)
        
        # enable btnCommit if anything dirty
        self.btnCommit.setEnabled(self.property('dirty'))
    
    def isFormDirty(self) -> bool:
        return self.property('dirty')

    def isWdgtDirty(self, wdgt:QWidget) -> bool:
        return wdgt.property('dirty')


    ##########################################
    ########    Widget-responding procs
# class EditMenu


#############################################
#############################################
#############################################


from app.database import app_Session
class OpenTable(QWidget):
    
    class cOpnTblDlgGetTable(QDialog):
        _tableListSQL:str = 'PRAGMA table_list;'
        
        def __init__(self, db:Engine = app_Session.kw["bind"], parent:QWidget|None = None):
            super().__init__(parent)
            
            self.setWindowModality(Qt.WindowModality.WindowModal)
            self.setWindowTitle(parent.windowTitle() if parent else 'Choose Tablew')

            layoutTableName = QHBoxLayout()
            lblTableName = QLabel(self.tr('Table to Show'))
            self.combobxTableName = QComboBox(self)
            self.combobxTableName.addItems(self.TableList())
            layoutTableName.addWidget(lblTableName)
            layoutTableName.addWidget(self.combobxTableName)

            dlgButtons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel,
                Qt.Orientation.Horizontal,
                )
            dlgButtons.accepted.connect(self.accept)
            dlgButtons.rejected.connect(self.reject)            

            layoutMine = QVBoxLayout()
            layoutMine.addLayout(layoutTableName)
            layoutMine.addWidget(dlgButtons)
            
            self.setLayout(layoutMine)

        def TableList(self, db:Engine = app_Session.kw["bind"]) -> List:
            qmodel = SQLAlchemySQLQueryModel(self._tableListSQL, db)
            
            colIdx = qmodel.colIndex('name')
            if colIdx < 0:
                # no 'name' column found
                # raise ValueError("No 'name' column found in the table list query result.")
                return []

            # retList = [qmodel.record(n)[colIdx] for n in range(qmodel.rowCount())]
            retList = [qmodel.data(qmodel.index(n, colIdx)) for n in range(qmodel.rowCount())]
            return retList

        def exec_DlgGetTbl(self):
            ret = super().exec()
            # later - prevent lvng if lnedtGroupName blank
            return (
                ret, 
                self.combobxTableName.currentText()    if ret==self.DialogCode.Accepted else None,
                )
    
    def __init__(self, tbl:str|None = None, db:Engine=app_Session.kw["bind"], parent:QWidget|None = None):
        super().__init__(parent)
        
        # font = QFont()
        # font.setPointSize(12)
        # self.setFont(font)
        
        if not tbl:
            # get tbl name
                # use self._tableListSQL
            # read all table names
            # present and select
            tbl = self.chooseTable(db)
        
        # for testing ...
        # tbl = 'incShip_hbl'
        
        # read into model
        # verify tbl exists
        # error, rows, colNames = (None, [], [])
        # error, rows, colNames = self.getTable(tbl)
        # if error:
        #     raise error
        
        # tblWidget = self.tableWidget(rows, colNames)
        tblWidget = self.tableWidget(tbl, db)
        self.model = tblWidget.model()
        # bring all rows in so rowCount will be correct
        # while tblWidget.model().canFetchMore():
        #     tblWidget.model().fetchMore()
        rows = tblWidget.model().rowCount()
        colNames = [tblWidget.model().headerData(n, Qt.Orientation.Horizontal) for n in range(tblWidget.model().columnCount())]
        # present TableView

        # save incoming for future use if needed
        self.rows = rows
        self.colNames = colNames

        self.layoutForm = QVBoxLayout(self)

        #TODO: make Title the name of the table        
        #TODO: note on screen that this form is RO        
        # Form Header Layout
        self.layoutFormHdr = QVBoxLayout()
        self.lblFormName = cQFmNameLabel()
        self.lblFormName.setText(self.tr('Table'))
        self.setWindowTitle(self.tr('Table'))
        self.layoutFormHdr.addWidget(self.lblFormName)
        
        self.layoutFormTableDescription = QFormLayout()
        lblnRecs = QLabel()
        lblnRecs.setText(f'{rows}')
        lblcolNames = QLabel()
        lblcolNames.setText(str(colNames))
        self.layoutFormTableDescription.addRow('rows:', lblnRecs)
        self.layoutFormTableDescription.addRow('cols:', lblcolNames)

        # main area for displaying SQL
        self.layoutFormMain = QVBoxLayout()
        self.layoutFormMain.addWidget(tblWidget)
        
        # nope - this is RO
        # # Add a add row button
        # addrow_button = QPushButton("Add Row")
        # addrow_button.clicked.connect(lambda: self.addRow())
        
        # # Add a save button
        # save_button = QPushButton("Save Changes")
        # save_button.clicked.connect(lambda: self.model.save_changes() or print("Saved!"))    # type: ignore
        
        # layoutButtons = QHBoxLayout()
        # layoutButtons.addWidget(addrow_button)
        # layoutButtons.addWidget(save_button)
        
        self.layoutForm.addLayout(self.layoutFormHdr)
        self.layoutForm.addLayout(self.layoutFormTableDescription)
        self.layoutForm.addLayout(self.layoutFormMain)
        # self.layoutForm.addLayout(layoutButtons)
        
    def chooseTable(self, db:Engine = app_Session.kw["bind"]) -> str|None:
        dlg = self.cOpnTblDlgGetTable(db, self)
        retval, tblName = dlg.exec_DlgGetTbl()
        return tblName if retval == QDialog.DialogCode.Accepted else None
            

    def getTable(self, tblName:str): # -> Tuple[Exception|None, List[Dict[str, Any]], List[str]|str]:
        pleaseWriteMe(self, 'fix getTable in class OpenTable')
        # inputSQL:str = f'SELECT * FROM {tblName}'
        # # inputSQL:str = f'SELECT * FROM %(tblName)s'
        # sqlerr = None
        # with db.connection.cursor() as djngocursor:
        #     try:
        #         djngocursor.execute(inputSQL)
        #         # djngocursor.execute(inputSQL, [tblName])
        #     except Exception as err:
        #         sqlerr = err
        #     colNames = []
        #     rows = []
        #     if not sqlerr:
        #         if djngocursor.description:
        #             colNames = [col[0] for col in djngocursor.description]
        #             rows = dictfetchall(djngocursor)
        #         else:
        #             colNames = 'NO RECORDS RETURNED; ' + str(djngocursor.rowcount) + ' records affected'
        #             rows = []
        #         #endif cursor.description
        #     else:  
        #         # nothing to do
        #         ...
        #     #endif not sqlerr
        # #end with
        
        # return (sqlerr, rows, colNames)

    # def tableWidget(self, rows:List[Dict[str, Any]], colNames:str|List[str]) -> QTableView:
    def tableWidget(self, tbl:str|None, db:Engine) -> QTableView:
        sqlstat = f"SELECT * FROM {tbl}" if tbl else "SELECT * FROM sqlite_master WHERE type='table';"
        resultModel = SQLAlchemySQLQueryModel(sqlstat, db, self.parent())
        resultTable = QTableView()
        # resultTable.verticalHeader().setHidden(True)
        header = resultTable.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        # Apply stylesheet to control text wrapping
        resultTable.setStyleSheet("""
        QHeaderView::section {
            padding: 5px;
            font-size: 12px;
            text-align: center;
            white-space: normal;  /* Allow text to wrap */
        }
        """)
        resultTable.setModel(resultModel)
        
        return resultTable
        
    def addRow(self):
        self.model.insertRow(self.model.rowCount())

#############################################
#############################################
#############################################


class _internalForms:
    EditMenu = '.-EDT-menu.-'
    OpenTable = '-.OPN-tbL.-'
    # RunCode = ''
    RunSQLStatement = '.-ruN-sql.-'
    # ConstructSQLStatement = ''
    # LoadExtWebPage = ''
    # ChangePW = ''
    # EditParameters = ''
    # EditGreetings = ''
    IconThemeViewer = '.-icn-thm-vwr.-'
# FormNameToURL_Maps for internal use only
# FormNameToURL_Map['menu Argument'.lower()] = (url, view)
FormNameToURL_Map[_internalForms.EditMenu] = (None, cEditMenu)
FormNameToURL_Map[_internalForms.OpenTable] = (None, OpenTable)
FormNameToURL_Map[_internalForms.RunSQLStatement] = (None, cMRunSQL)
