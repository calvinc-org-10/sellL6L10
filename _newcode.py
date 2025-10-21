# import sys

# from functools import partial
from typing import (Callable, List, Dict, Type, Any, )

from PySide6.QtCore import (
    Slot, Signal,
    Qt, QModelIndex,
    )
from PySide6.QtGui import (
    QIcon,
    )
from PySide6.QtWidgets import (
    QWidget,
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QDateEdit, QCheckBox, QLabel, 
    QPushButton,
    QStatusBar, QMessageBox,
    QTableView, QStyledItemDelegate, QItemDelegate,
    QLayout, QBoxLayout, QVBoxLayout, QHBoxLayout, QGridLayout,
    )
import qtawesome

from sqlalchemy import (
    literal, func,
    )
from sqlalchemy.orm import (
    sessionmaker, Session,
    )

from cMenu.utils import (
    SQLAlchemyTableModel,
    cSimpleRecordForm, 
    cSimpRecFmElement_Base,
    cQFmFldWidg, cQFmLookupWidg,
    cDataList,
    cComboBoxFromDict,
    get_primary_key_column,
    areYouSure, 
    )
from app.database import app_Session
# from cMenu.utils.cQdbFormWidgets import cSimpleRecordSubForm2

class cSimpleFormBase(QWidget):
    _ORMmodel:Type[Any]|None = None
    _primary_key: Any
    _ssnmaker:sessionmaker[Session]|None = None
    currRec: Any
    _newrecFlag: QLabel
    pages: List = []
    fieldDefs: Dict[str, Dict[str, Any]] = {}
    _lookupFrmElements: List[cQFmLookupWidg] = []

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

        self.layoutMain, self.layoutForm, self.layoutButtons = self._buildFormLayout()

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
        
    def _buildFormLayout(self) -> tuple[QBoxLayout, QGridLayout, QBoxLayout|None]:
        # returns tuple (layoutMain, layoutForm, layoutButtons)
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
    
    def _bindField(self, _fieldName: str, widget: QWidget) -> None:
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
        elif isinstance(widget, cQFmLookupWidg):        # lookup widgets not supported in subforms (for now)
            widget.signalLookupSelected.connect(lambda *_: self.changeField(widget, widget._lookup_field, widget.Value()))
        #endif isinstance(widget)
    # bindField
    def _placeFields(self, lookupsAllowed: bool = True) -> None:
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

        ssnmkr = self.ssnmaker()
        ssnmkr = ssnmkr if ssnmkr else app_Session
        mdl = self.ORMmodel()
        assert mdl is not None, "ORMmodel must be set before placing fields"
    
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
                widget = SubFormCls(session_factory=ssnmkr, parent=self)
                if not isinstance(widget, cSimpRecFmElement_Base):
                    raise TypeError(f'class {SubFormCls.__name__} must inherit from cSimpRecFmElement_Base')
            # --- Scalar case ---
            elif isLookup:
                if lookupsAllowed:
                    if widgType not in (cDataList, cComboBoxFromDict):
                        widgType = cDataList  # force it to be a cDataList
                    widget = cQFmLookupWidg(
                        session_factory=ssnmkr,
                        model=mdl,
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
                    # endif lookupHandler
                # endif lookupsAllowed
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
            self._bindField(_fldName, widget)

            # Place in layout
            if isinstance(pos, tuple) and len(pos) >= 2:
                self.layoutForm.addWidget(widget, *pos)

            widget.dirtyChanged.connect(
                lambda dirty, w=widget: self.setDirty(w, dirty)
            )
        # endfor fldDef in self.fieldDefs
    # _placeFields

    def _addActionButtons(self):
        raise NotImplementedError
    # _addActionButtons
    def _handleActionButton(self, action: str) -> None:
        raise NotImplementedError
    # _handleActionButton

        
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
        
        self.showNewRecordFlag()
    # initialdisplay()

    def statusBar(self) -> QStatusBar|None:
        """Get the status bar."""
        return self.findChild(QStatusBar)
    # statusBar

    def showError(self, message: str, title: str = "Error") -> None:
        """Show an error message box."""
        QMessageBox.critical(self, title, message)
        # use status bar to show error message
        SB = self.statusBar()
        SB.showMessage(f"Error: {message}") if SB else None

        # TODO: choose whether to messageBox or status bar or both
    # showError

    def isit_OKToLeaveRecord(self) -> bool:
        """
        Check if the form is dirty. If so, prompt user.
        Returns True if it is safe to proceed with navigation, False otherwise.
        """
        if not self.isDirty():
            return True

        choice = areYouSure(
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

    def fillFormFromcurrRec(self):
        for fldDef in self.fieldDefs.values():
            fld = fldDef.get("widget")
            if fld:
                fld.loadFromRecord(self.currRec)

        self.showNewRecordFlag()
        self.setDirty(False)
    # fillFormFromRec

    # TODO: wrap with fillFormFromcurrRec
    # TODO: play with positioning of new record flag
    def showNewRecordFlag(self) -> None:
        self._newrecFlag.setVisible(self.isNewRecord())

    def isNewRecord(self) -> bool:
        return self.currRec is None or getattr(self.currRec, self._primary_key.key) is None
            
    def repopLookups(self) -> None:
        """Repopulate all lookup widgets (e.g., after a save)."""
        return
        for lookupWidget in self._lookupFrmElements:
            lookupWidget.repopulateChoices()

    ##########################################
    ########    Create

    def initializeRec(self):
        """
        Initialize a new record with default values.

        implementation should call fillFormFromcurrRec() after setting default values in self.currRec
        """
        modlType = self.ORMmodel()
        assert modlType is not None, "ORMmodel must be set before initializing record"
        self.currRec = modlType()
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
    # add_record
    
    ##########################################
    ########    Read / Navigation

    # # --- Lookup navigation ---
    def _load_record_by_id(self, pk_val):
        """Low-level load (assumes it's safe to replace current record)."""
        ssnmkr = self.ssnmaker()
        assert ssnmkr is not None, "Sessionmaker must be set before touching the database"
        with ssnmkr() as session:
            modl = self.ORMmodel()
            assert modl is not None, "ORMmodel must be set before loading record"
            rec = session.get(modl, pk_val)
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

    def load_record(self, recindex: int):
        """
        Load a record from the database.
        NOTE: For this class, recindex is the id of the record to load, not the index.

        Args:
            recindex (int): The ID of the record to load.
        """
        self._load_record_by_id(recindex)
    # load_record

    def _navigate_to(self, rec_id: int):
        """Navigate safely to a record (with save/discard prompt if dirty)."""
        if not self.isit_OKToLeaveRecord():
            return  # Cancel pressed → stay put

        self._load_record_by_id(rec_id)
    # _navigate_to

    def get_prev_record_id(self, recID:int) -> int:
        ssnmkr = self.ssnmaker()
        assert ssnmkr is not None, "Sessionmaker must be set before touching the database"
        with ssnmkr() as session:
            prev_id = session.query(func.max(self._primary_key)).where(self._primary_key < recID).scalar()
        return prev_id
    def get_next_record_id(self, recID:int) -> int:
        ssnmkr = self.ssnmaker()
        assert ssnmkr is not None, "Sessionmaker must be set before touching the database"
        with ssnmkr() as session:
            next_id = session.query(func.min(self._primary_key)).where(self._primary_key > recID).scalar()
        return next_id
        
    def on_loadfirst_clicked(self):
        # determine minimum id in database and load it
        ssnmkr = self.ssnmaker()
        assert ssnmkr is not None, "Sessionmaker must be set before touching the database"
        with ssnmkr() as session:
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
        ssnmkr = self.ssnmaker()
        assert ssnmkr is not None, "Sessionmaker must be set before touching the database"
        with ssnmkr() as session:
            max_id = session.query(func.max(self._primary_key)).scalar()
            if max_id:
                self._navigate_to(max_id)

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

        ssnmkr = self.ssnmaker()
        assert ssnmkr is not None, "Sessionmaker must be set before touching the database"
        with ssnmkr() as session:
            modl = self.ORMmodel()
            assert modl is not None, "ORMmodel must be set before loading record"
            rec = session.query(modl).filter(orm_field == value).first()
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

    @Slot()
    def lookup_and_load(self, fld: str, value: Any):
        value = value.get('text', value) if isinstance(value, dict) else (getattr(value, 'text', value) if hasattr(value, 'text') else value)
        self.load_record_by_field(fld, value)
    # lookup_CIMSNum
   
    ##########################################
    ########    Update

    @Slot()
    # REVIEW THIS!!!
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
            ssnmkr = self.ssnmaker()
            assert ssnmkr is not None, "Sessionmaker must be set before touching the database"
            with ssnmkr(expire_on_commit=False) as session:
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
    # on_save_clicked
    
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

        confirm = areYouSure(
            self,
            "Delete record",
            f"Really delete record {keyID}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
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

        self.repopLookups()
        # Navigate to neighbor, or clear form if none
        next_id = self.get_next_record_id(keyID)
        prev_id = self.get_prev_record_id(keyID)
        target_id = next_id or prev_id
        if target_id:
            self._load_record_by_id(target_id)
        else:
            self.initializeRec()
            self.fillFormFromcurrRec()
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

        # Enable save button if anything is dirty
        btnCommit = getattr(self, 'btnCommit', None)
        if isinstance(btnCommit, QPushButton):
            btnCommit.setEnabled(self.isDirty())
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
    



