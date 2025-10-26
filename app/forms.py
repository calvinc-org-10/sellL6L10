from typing import (Dict, Any, )
import re

from PySide6.QtCore import (
    Qt, Slot, qDebug,
)
from PySide6.QtGui import (
    QFont, QColorConstants,
    QPalette, QBrush,
    )
from PySide6.QtWidgets import (
    QStatusBar, QWidget, QScrollArea, QListWidget, QListWidgetItem,
    QHBoxLayout, QVBoxLayout, QGridLayout, QFrame,
    QLabel, QLineEdit, QPushButton,
    QMessageBox,
)
from sqlalchemy import FromClause, func, select
from sqlalchemy.orm import Session, sessionmaker

from cMenu.utils import (cQFmFldWidg, cQFmNameLabel, cDataList, cComboBoxFromDict, clearLayout, areYouSure, )
from cMenu.utils import (cSimpleTableForm, cSimpleRecordForm, cSimpleRecordSubForm1, )

from app.database import app_Session
from app.models import (WorkOrderPartsNeeded, WorkOrders, Parts, Projects, TagPrefixes, Scans, BoxConfigurations, L6L10sellRepositories)
from cMenu.utils.cQdbFormWidgets import cSimpleRecordSubForm2

##########################################################
##########################################################

# choice dictionaries and widgets
# many, many choices for these tables - construct the choice list only once or spend forever waiting

class Kls_sellL6ChoiceList:
    _instance: "Kls_sellL6ChoiceList | None" = None
    _sessionMaker = app_Session
    choices: dict[str, Any]
    widget: dict[str, cDataList|cComboBoxFromDict]
    
    _validLists = [
        'CIMSPKNum',
        'WOMAid',
        'Project',
        'Parts',
    ]

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        # init runs every call, so guard if needed
        # if Kls_sellL6ChoiceList._instance is not None:
        if hasattr(self, "_initialized"):
            raise RuntimeError("Use Kls_sellL6ChoiceList.instance() instead")

        # put your real init code here
        self.choices = {}
        self.widget = {}
        self.regen('*')

        self._initialized = True
    # __init__
    
    def regen(self, choiceList:str):
        if choiceList == '*':
            for lst in self._validLists:
                self.regen(lst) 
            return
        
        tbl = None
        choiceListType = None
        cFld = None
        
        if choiceList == 'CIMSPKNum':
            tbl = WorkOrders
            cFld = WorkOrders.CIMSNum
            choiceListType = cDataList
        if choiceList == 'WOMAid':
            tbl = WorkOrders
            cFld = WorkOrders.WOMAid
            choiceListType = cDataList
        if choiceList == 'Project':
            tbl = Projects
            cFld = Projects.ProjectName
            choiceListType = cComboBoxFromDict
        if choiceList == 'Parts':
            tbl = Parts
            cFld = Parts.GPN
            choiceListType = cDataList

        if tbl is None or cFld is None or choiceListType is None:
            raise ValueError(f'{choiceList} is not a valid choice type')
        
        Nochoice = {'---': None}    # only needed for combo boxes, not datalists
        chdict = {}
        wdgt = cDataList({})
        with self._sessionMaker() as session:
            stmt = select(tbl).order_by(cFld)
            records = session.execute(stmt)
            # retList = list(records.mappings())
            if choiceListType is cDataList:
                chdict = {rec.id: str(getattr(rec, cFld.key)) for rec in records.scalars()}
                wdgt = cDataList(chdict)
            if choiceListType is cComboBoxFromDict:
                chdict = Nochoice | { str(getattr(rec, cFld.key)): rec.id for rec in records.scalars()}
                wdgt = cComboBoxFromDict(chdict)
        
        self.choices[choiceList] = chdict
        self.widget[choiceList] = wdgt
    #regen
# this line actually creates the singleton instance
# it will be created only once, when this module is first imported
# syntactical note: this invocation will fly, since _instance is presently None
# any other call to the class needs to be via Kls_sellL6ChoiceList.instance()   
sellL6ChoiceList = Kls_sellL6ChoiceList()
    

##########################################################
##########################################################

class WOTable(cSimpleTableForm):
    _tbl = WorkOrders
    _ssnmaker = app_Session
    _formname = 'Work Orders'

class ProjectsTable(cSimpleTableForm):
    _tbl = Projects
    _ssnmaker = app_Session
    _formname = 'Projects'

class PartsTable(cSimpleTableForm):
    _tbl = Parts
    _ssnmaker = app_Session
    _formname = 'Parts'

class WOPartsNeededTable(cSimpleTableForm):
    _tbl = WorkOrderPartsNeeded
    _ssnmaker = app_Session
    _formname = 'WorkOrder Parts Needed'

class TagPrefixesTable(cSimpleTableForm):
    _tbl = TagPrefixes
    _ssnmaker = app_Session
    _formname = 'Tag Prefixes'

class ScansTable(cSimpleTableForm):
    _tbl = Scans
    _ssnmaker = app_Session
    _formname = 'Scans'

class BoxConfigsTable(cSimpleTableForm):
    _tbl = BoxConfigurations
    _ssnmaker = app_Session
    _formname = 'Box Configurations'

##########################################################
##########################################################

# DONE: handle foreign keys properly - make them cComboBoxFromDict or cDataList

std_id_def = {'label': 'ID', 'widgetType': QLabel, 'noedit': True, 'readonly': True, 'position': (0,0)}

class PartsRecord(cSimpleRecordForm):
    _tbl = Parts
    _ssnmaker = app_Session
    _formname = 'Parts'
    fieldDefs = {
        'id': std_id_def,
        'GPN': {'label': 'GPN', 'widgetType': QLineEdit, 'position': (1,0)},
        '@GPN': {'label': 'lookup GPN', 'position': (1,1), 'widgetType': cDataList, 'choices': sellL6ChoiceList.choices['Parts'], 'lookupHandler': 'lookup_GPN'},
        'Description': {'label': 'Description', 'widgetType': QLineEdit, 'position': (2,0)},
        'notes': {'label': 'Notes', 'widgetType': QLineEdit, 'position': (4,0)},
        
        # subform - 'workorders_needing_part': {'label': 'Work Orders', 'widgetType': QLineEdit, 'noedit': True, 'readonly': True, 'position': (5,0)},
        # subform - 'tag_prefixes': {'label': 'Tag Prefixes', 'widgetType': QLineEdit, 'noedit': True, 'readonly': True, 'position': (6,0)},
        # subform - 'box_configurations': {'label': 'Box Configs', 'widgetType': QLineEdit, 'noedit': True, 'readonly': True, 'position': (8,0)},
    }

class ProjectsRecord(cSimpleRecordForm):
    _tbl = Projects
    _ssnmaker = app_Session
    _formname = 'Projects'
    fieldDefs = {
        'id': std_id_def,
        'ProjectName': {'label': 'Project Name', 'widgetType': QLineEdit, 'position': (1,0)},
        '@ProjectName': {'label': 'lookup Project Name', 'position': (1,1), 'widgetType': cComboBoxFromDict, 'lookupHandler': 'lookup_ProjectName'},
        'Color': {'label': 'Color', 'widgetType': QLineEdit, 'position': (2,0)},
    }
    
# class WorkOrderPartsNeededSubForm(cSimpleRecordSubForm):
#     _ORMmodel = WorkOrderPartsNeeded
#     #TODO: make the line below work
#     # _parentFK = WorkOrderPartsNeeded.WorkOrders_id   # field in this table that is the FK to main table
#     _parentFK = 'WorkOrders_id'   # field in this table that is the FK to main table
#     _ssnmaker = app_Session

class WorkOrderPartsNeededSubForm(cSimpleRecordSubForm2):
    _ORMmodel = WorkOrderPartsNeeded
    #TODO: make the line below work
    # _parentFK = WorkOrderPartsNeeded.WorkOrders_id   # field in this table that is the FK to main table
    _parentFK = 'WorkOrders_id'   # field in this table that is the FK to main table
    _ssnmaker = app_Session
    # _colDef = [
    #     {'field': 'id', 'readonly': True, },
    #     {'field': 'WorkOrders_id', 'readonly': True, 'hidden': True, },
    #     {'field': 'Parts_id', 'widgetType': cDataList , 'choices': sellL6ChoiceList.choices['Parts'], },
    #     {'field': 'targetQty', },
    #     {'field': 'status', },
    #     {'field': 'priority', },       # suggestions from PickPriorities
    #     {'field': 'notes', },
    #     {'colmn': 'Delete', 'widgetType': QPushButton, 'btnText': 'Delete', 'btnSlot': 'deleteCurrentRecord', },
    # ]
    fieldDefs = {
        'id': {'label': 'ID', 'widgetType': QLabel, 'noedit': True, 'readonly': True, 'position': (0,0)},
        'WorkOrders_id': {'label': 'Work Order', 'widgetType': cDataList, 'choices': sellL6ChoiceList.choices['WOMAid'], 'noedit': True, 'position': (0,1)},
        'Parts_id': {'label': 'GPN', 'widgetType': cDataList, 'choices': sellL6ChoiceList.choices['Parts'], 'position': (0,2)},
        'targetQty': {'label': 'Target Qty', 'widgetType': QLineEdit, 'position': (1,0)},
        'status': {'label': 'Status', 'widgetType': QLineEdit, 'position': (1,1)},
        'priority': {'label': 'Priority', 'widgetType': QLineEdit, 'position': (1,2)},
        'notes': {'label': 'Notes', 'widgetType': QLineEdit, 'position': (2,0)},
        #     {'colmn': 'Delete', 'widgetType': QPushButton, 'btnText': 'Delete', 'btnSlot': 'deleteCurrentRecord', },
    }

    # widget = SubFormCls(session_factory=self._ssnmaker, parent=self)
    def __init__(self,
        session_factory: sessionmaker[Session] | None = None,
        parent=None
        ):

        super().__init__(self._ORMmodel, self._parentFK, session_factory or self._ssnmaker, QListWidget, parent)

        # self.table.setItemDelegate(cColDefOmniDelegate(self._colDef, self))

    @Slot()
    def deleteCurrentRecord(self, row):
        print(f"Delete row {row}")  # Replace with actual delete logic
class WorkOrdersRecord(cSimpleRecordForm):
    _ORMmodel = WorkOrders
    _ssnmaker = app_Session
    _formname = 'Work Orders'
    fieldDefs = {
        'id': std_id_def,
        '@id': {'label': 'lookup ID', 'position': (0,1), 'lookupHandler': 'lookup_pk', 'widgetType': cComboBoxFromDict},
        'CIMSNum': {'label': 'CIMS Number', 'widgetType': QLineEdit, 'position': (2,0)},
        '@CIMSNum': {'label': 'lookup CIMS Number', 'position': (2,1), 'lookupHandler': 'lookup_CIMSNum', 'widgetType': cDataList},
        'WOMAid': {'label': 'WO/MA id', 'widgetType': QLineEdit, 'position': (3,0)},
        '@WOMAid': {'label': 'lookup WO/MA id', 'position': (3,1), 'lookupHandler': 'lookup_WOMAid'},
        'MRRequestor': {'label': 'MR Requestor', 'widgetType': QLineEdit, 'position': (4,0)},
        'Project_id': {'label': 'Project', 'widgetType': cComboBoxFromDict, 'choices': sellL6ChoiceList.choices['Project'], 'position': (5,0)},
        'notes': {'label': 'Notes', 'widgetType': QLineEdit, 'position': (6,0)},
        'parts_needed': {'subform_class': WorkOrderPartsNeededSubForm, 'position': (8,0,1,3)},

        # subform - 'parts_needed': {'label': 'Parts Needed', 'widgetType': QLineEdit, 'position': (8,0)},
    }

    # see cSimpleRecordForm for details, methods, etc.
    
    def _finalizeMainLayout(self):
        super()._finalizeMainLayout()    
        
        # after form is built, set up other widgets
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)   # or Raised, Plain
        lyout = self.FormPage(0)
        if lyout is not None:
            lyout.addWidget(line, 7, 0, 1, 3)  # row, col, rowspan, colspan
    # _finalizeMainLayout
     
    @Slot()
    def lookup_CIMSNum(self, value):
        self.lookup_and_load('CIMSNum', value)
    @Slot()
    def lookup_WOMAid(self, value):
        self.lookup_and_load('WOMAid', value)
    @Slot()
    def lookup_pk(self, value):
        self.lookup_and_load('id', value)
# WorkOrdersRecord
class WorkOrdersRecord_multipage(cSimpleRecordForm):
    _ORMmodel = WorkOrders
    _ssnmaker = app_Session
    _formname = 'Work Orders'
    pages = ['Main', 'pg 2', 'Parts']
    fieldDefs = {
        'id': std_id_def,
        '@id': {'label': 'lookup ID', 'position': (0,1), 'lookupHandler': 'lookup_pk', 'widgetType': cComboBoxFromDict},
        'CIMSNum': {'label': 'CIMS Number', 'widgetType': QLineEdit, 'position': (2,0)},
        '@CIMSNum': {'label': 'lookup CIMS Number', 'position': (2,1), 'lookupHandler': 'lookup_CIMSNum', 'widgetType': cDataList},
        'WOMAid': {'label': 'WO/MA id', 'widgetType': QLineEdit, 'position': (3,0)},
        '@WOMAid': {'label': 'lookup WO/MA id', 'position': (3,1), 'lookupHandler': 'lookup_WOMAid'},
        'MRRequestor': {'label': 'MR Requestor', 'widgetType': QLineEdit, 'page': 'pg 2', 'position': (1,0,1,2)},
        'Project_id': {'label': 'Project', 'widgetType': cComboBoxFromDict, 'choices': sellL6ChoiceList.choices['Project'], 'page': 'pg 2', 'position': (1,3)},
        'notes': {'label': 'Notes', 'widgetType': QLineEdit, 'page': 'pg 2', 'position': (2,0,1,3)},
        'parts_needed': {'subform_class': WorkOrderPartsNeededSubForm, 'page': 'Parts', 'position': (1,0,1,3)},

        # subform - 'parts_needed': {'label': 'Parts Needed', 'widgetType': QLineEdit, 'position': (8,0)},
    }

    @Slot()
    def lookup_CIMSNum(self, value):
        self.lookup_and_load('CIMSNum', value)
    @Slot()
    def lookup_WOMAid(self, value):
        self.lookup_and_load('WOMAid', value)
    @Slot()
    def lookup_pk(self, value):
        self.lookup_and_load('id', value)
# WorkOrdersRecord_multipage
    

class WorkOrderPartsNeededRecord(cSimpleRecordForm):
    _tbl = WorkOrderPartsNeeded
    _ssnmaker = app_Session
    _formname = 'Work Order Parts Needed'
    fieldDefs = {
        'id': std_id_def,
        'WorkOrders_id': {'label': 'Work Order', 'widgetType': cComboBoxFromDict, 'choices': sellL6ChoiceList.choices['WOMAid'], 'position': (1,0)},
        'Parts_id': {'label': 'GPN', 'widgetType': cDataList, 'choices': sellL6ChoiceList.choices['Parts'], 'position': (2,0)},
        'targetQty': {'label': 'Target Qty', 'widgetType': QLineEdit, 'position': (3,0)},
        'status': {'label': 'Status', 'widgetType': QLineEdit, 'position': (3,1)},
        'priority': {'label': 'Priority', 'widgetType': QLineEdit, 'position': (3,2)},
        'notes': {'label': 'Notes', 'widgetType': QLineEdit, 'position': (4,0)},
    }

class TagPrefixesRecord(cSimpleRecordForm):
    _tbl = TagPrefixes
    _ssnmaker = app_Session
    _formname = 'Tag Prefixes'
    fieldDefs = {
        'id': std_id_def,
        'Prefix': {'label': 'Prefix', 'widgetType': QLineEdit, 'position': (1,0)},
        'Parts_id': {'label': 'GPN', 'widgetType': cDataList, 'choices': sellL6ChoiceList.choices['Parts'], 'position': (2,0)},
        'boxqty': {'label': 'Box Qty', 'widgetType': QLineEdit, 'position': (3,0)},
        'Notes': {'label': 'Notes', 'widgetType': QLineEdit, 'position': (4,0)},
    }
    
class ScansRecord(cSimpleRecordForm):
    # nope - do a custom form
    # group by pickDate, wave
    _tbl = Scans
    _ssnmaker = app_Session
    _formname = 'Scans'
    fieldDefs = {
        'id': std_id_def,
        'pickDate': {'label': 'Pick Date', 'widgetType': QLineEdit, 'position': (1,0)},
        'wave': {'label': 'Wave', 'widgetType': QLineEdit, 'position': (1,1)},
        'TagID': {'label': 'Tag ID', 'widgetType': QLineEdit, 'position': (2,0)},
        'Parts_id': {'label': 'GPN', 'widgetType': cDataList, 'choices': sellL6ChoiceList.choices['Parts'], 'position': (3,0)},
        'WO_id': {'label': 'Work Order', 'widgetType': cComboBoxFromDict, 'choices': sellL6ChoiceList.choices['WOMAid'], 'position': (3,1)},
        'qty': {'label': 'Qty', 'widgetType': QLineEdit, 'position': (4,0)},
        'splitQtyToLeave': {'label': 'Split Qty To Leave', 'widgetType': QLineEdit, 'position': (4,1)},
        'palletMark': {'label': 'Pallet Mark', 'widgetType': QLineEdit, 'position': (4,2)},
        'staged_at': {'label': 'Staged At', 'widgetType': QLineEdit, 'position': (4,3)},
        'Notes': {'label': 'Notes', 'widgetType': QLineEdit, 'position': (5,0)},
    }   

# AI generated - fixmefixme!!
class BoxConfigsRecord(cSimpleRecordForm):
    _tbl = BoxConfigurations
    _ssnmaker = app_Session
    _formname = 'Box Configurations'
    fieldDefs = {
        'id': std_id_def,
        'Parts_id': {'label': 'GPN', 'widgetType': cDataList, 'choices': sellL6ChoiceList.choices['Parts'], 'position': (1,0)},
        'palletqty': {'label': 'Pallet Qty', 'widgetType': QLineEdit, 'position': (2,0)},
        'boxqty': {'label': 'Qty In Box', 'widgetType': QLineEdit, 'position': (3,0)},
        'unitqty': {'label': 'Qty Per Unit', 'widgetType': QLineEdit, 'position': (4,0)},
        'notes': {'label': 'Notes', 'widgetType': QLineEdit, 'position': (6,0)},
    }

####################################################################
####################################################################
####################################################################

# TODO: Look at who calls who - eliminate double calls!!!

class WOPartsNeeded_LineItem(QWidget):
    _GPN:str = ""
    _Parts_id: int = 0
    _WorkOrders_id: int = 0
    formFields:Dict[str, cQFmFldWidg|QWidget] = {}

    def __init__(self, WOPartsNeededRec:WorkOrderPartsNeeded, parent = None):
        super().__init__(parent)
        
        self.currRec = WOPartsNeededRec
        self._GPN = WOPartsNeededRec.part.GPN if WOPartsNeededRec.part else ""
        self._Parts_id = WOPartsNeededRec.Parts_id
        self._WorkOrders_id = WOPartsNeededRec.WorkOrders_id
        
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)

        layoutForm = QHBoxLayout(self)
        layoutForm.setContentsMargins(0, 0, 0, 0)
        
        self.lblRecID = QLabel()
        layoutForm.addWidget(self.lblRecID)
        
        modlFld='GPN'
        self.lblGPN = QLabel()
        # raise?
        wdgt = self.lblGPN
        self.formFields[modlFld] = wdgt
        layoutForm.addWidget(wdgt)
        
        self.btnDelete = QPushButton('Remove')
        font = QFont()
        font.setPointSize(8)
        self.btnDelete.setFont(font)
        self.btnDelete.clicked.connect(self.deleteRec)
        layoutForm.addWidget(self.btnDelete)
        
        modlFld='qty'
        self.lnedtqty = cQFmFldWidg(QLineEdit, modlFld=modlFld, parent=self)
        wdgt = self.lnedtqty
        wdgt.setMaximumWidth(150)
        self.formFields[modlFld] = wdgt
        wdgt.signalFldChanged.connect(lambda: self.changeField(self.lnedtqty))
        layoutForm.addWidget(wdgt)

        modlFld = 'notes'
        self.lnedtnotes = cQFmFldWidg(QLineEdit, modlFld=modlFld, parent=self)
        wdgt = self.lnedtnotes
        self.formFields[modlFld] = wdgt
        wdgt.signalFldChanged.connect(lambda: self.changeField(self.lnedtnotes))
        layoutForm.addWidget(wdgt)

        # set tab order
        
        self.fillFormFromcurrRec()
    # setupUi

    ##########################################
    ########    Create

    def initializeRec(self):
        # set all fields null except GPN, WO
        self.currRec.setValue('id', None)
        self.currRec.setValue('qty', None)
        self.currRec.setValue('notes', '')
        
        self.fillFormFromcurrRec()

    ##########################################
    ########    Read

    def fillFormFromcurrRec(self):
        # review this
        cRec = self.currRec
        
        # set pk display
        self.lblRecID.setText(str(cRec.id))

        # move to class var?
        forgnKeys = {
            'Parts_id': cRec.part.GPN if cRec.part else '',
            'WorkOrders_id': cRec.workorder.WOMAid if cRec.workorder else '',
        }
        # move to class var?
        valu_transform_flds = {
            'GPN': lambda wdgt, field_valueStr: wdgt.setText(field_valueStr),
        }

        for fieldname in cRec.__table__.columns.keys():
            field_value = getattr(cRec, fieldname)
            field_valueStr = str(field_value)
            if fieldname in forgnKeys:
                field_valueStr = str(forgnKeys[fieldname])
            
            if fieldname in self.formFields:
                wdgt = self.formFields[fieldname]
                if fieldname in valu_transform_flds:
                    valu_transform_flds[fieldname](wdgt, field_valueStr)
                else:
                    if isinstance(wdgt, cQFmFldWidg):
                        wdgt.setValue(field_valueStr) # type: ignore

        self.setFormDirty(self, False)
    # fillFormFromRec


    ##########################################
    ########    Update

    @Slot()
    def changeField(self, wdgt:cQFmFldWidg) -> bool:
        # move to class var?
        forgnKeys = {
            'WorkOrders': 'WOMAid',
            'Parts': 'GPN',
            }
        # move to class var?
        valu_transform_flds = {
            'qty': int
        }
        cRec = self.currRec
        dbField = wdgt.modelField()

        wdgt_value = wdgt.Value()

        if dbField in forgnKeys:
            dbField += '_id'
        #TODO: CLEAN THIS!!!!!
        if dbField in valu_transform_flds:
            if isinstance(wdgt_value, str):
                if re.match(r'-?[0-9]+', wdgt_value):
                    wdgt_value = valu_transform_flds[dbField](wdgt_value)
                else:
                    wdgt_value = 0
                #endif wdgt_value.isnumeric()

        retval = False
        if dbField is not None:
            if wdgt_value is not None:
                setattr(cRec, dbField, wdgt_value)
                self.setFormDirty(wdgt, True)

                retval = True
            else:
                setattr(cRec, dbField, None)

                retval = False
            # endif wdgt_value
        #endif dbField

        self.writeRecord()
        
        return retval
    # changeField
    
    def writeRecord(self):
        if not self.isFormDirty():
            return
        
        cRec = self.currRec
        newrec = cRec.id is None
        hasavalue = any([
            cRec.targetQty is not None,
            cRec.notes is not None,
        ])

        pk = -1
        if newrec:
            if hasavalue:
                insRow = WorkOrderPartsNeeded(
                    WorkOrders_id=cRec.WorkOrders_id,
                    Parts_id=cRec.Parts_id,
                    targetQty=cRec.targetQty,
                    notes=cRec.notes
                )
                with app_Session() as session:
                    session.add(insRow)
                    session.commit()
                    pk = insRow.id
            else:
                pass
            #endif hasavalue
        else:
            if hasavalue:
                with app_Session() as session:
                    session.merge(cRec)
                    session.commit()
                    pk = cRec.id
            else:
                self.deleteRec()
                return
            #endif hasavalue
        #endif newrec

        # self.lblRecID.setText(str(pk))
        self.fillFormFromcurrRec()
                    
        self.setFormDirty(self, False)
    # writeRecord


    ##########################################
    ########    Delete

    @Slot()
    def deleteRec(self):
        cRec = self.currRec

        if cRec.id is not None:
            with app_Session() as session:
                session.delete(cRec)
                session.commit()
        #endif cRec.id is not None
        
        self.initializeRec()
    #deleteRec


    ##########################################
    ########    CRUD support

    @Slot()
    def setFormDirty(self, wdgt:QWidget, dirty:bool = True):
        wdgt.setProperty('dirty', dirty)
        # if wdgt === self, set all children dirty
        if wdgt is not self:
            if dirty: self.setProperty('dirty',True)
        else:
            for W in self.children():
                if any([W.inherits(tp) for tp in ['QLineEdit', 'QTextEdit', 'QCheckBox', 'QComboBox', 'QDateEdit', ]]):
                    W.setProperty('dirty', dirty)
        
        # enable btnCommit if anything dirty
        # self.btnCommit.setEnabled(self.property('dirty'))
    
    def isFormDirty(self) -> bool:
        return self.property('dirty')


    ##########################################
    ########    Widget-responding procs


class WOPartsNeededForm(QWidget):
    currRec = None
    formFields:Dict[str, QWidget] = {}
    requiredFlds = [
            'Project_id',
            'CIMSNum',
            'WOMAid',
        ]
        
    class HdrGPNList(QWidget):
        def __init__(self, parent:QWidget|None = None):
            super().__init__(parent)

            layout = QHBoxLayout(self)
            layout.addSpacing(10)       # for id field
            
            modlFld='GPN'
            wdgt = QLabel(modlFld)
            layout.addWidget(wdgt)
            layout.addSpacing(10)            
            
            modlFld='qty'
            wdgt = QLabel(modlFld)
            layout.addWidget(wdgt)
            layout.addSpacing(10)            

            modlFld = 'notes'
            wdgt = QLabel(modlFld)
            layout.addWidget(wdgt)
            layout.addSpacing(10)            

    def __init__(self, parent:QWidget|None = None):
        super().__init__(parent)

        font = QFont()
        font.setPointSize(12)
        self.setFont(font)
        
        self.layoutForm = QVBoxLayout(self)
        
        self.layoutFormHdr = QGridLayout()
        
        wndwTitle = self.tr('Work Order Parts Needed')
        self.lblFormName = cQFmNameLabel(parent=self)
        wdgt = self.lblFormName
        wdgt.setText(wndwTitle)
        self.layoutFormHdr.addWidget(wdgt,0,3,1,17)
        self.setWindowTitle(wndwTitle)
        
        # self.lblRecID = QLabel()
        modlFld, modlLbl = 'id', ''
        self.lblRecID = cQFmFldWidg(QLabel, lblText=modlLbl, modlFld=modlFld)
        self.layoutFormHdr.addWidget(self.lblRecID,0,0,1,1)
        
        modlFld, modlLbl = 'CIMSNum', 'CIMS PK/RP Num'

        choices_WO = {WO.id:WO.CIMSNum  for WO in L6L10sellRepositories.WorkOrders.get_all()}
        self.wdgtCIMSNum = cQFmFldWidg(cDataList, lblText=modlLbl, choices=choices_WO, modlFld=modlFld,parent=self)
        wdgt = self.wdgtCIMSNum
        self.formFields[modlFld] = wdgt
        wdgt.signalFldChanged.connect(self.getRecordFromGoto)
        self.lblNewCIMSNum = QLabel(self)
        wdgtNwWkOrd = self.lblNewCIMSNum
        palette = QPalette()
        brush = QBrush(QColorConstants.Red)
        brush.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText, brush)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.WindowText, brush)
        wdgtNwWkOrd.setPalette(palette)
        self.layoutFormHdr.addWidget(wdgt,1,1,1,6)
        self.layoutFormHdr.addWidget(wdgtNwWkOrd,1,7,1,6)

        layoutBtnGrp1 = QVBoxLayout()        
        self.btnCommit = QPushButton()
        wdgt = self.btnCommit
        wdgt.setText('Commit\nChanges')
        wdgt.clicked.connect(self.writeRecord)
        layoutBtnGrp1.addWidget(wdgt)

        self.btnDelete = QPushButton()
        wdgt = self.btnDelete
        wdgt.setText('Delete\nRecord')
        wdgt.clicked.connect(self.deleteRecord)
        layoutBtnGrp1.addWidget(wdgt)
        self.layoutFormHdr.addLayout(layoutBtnGrp1,1,18,1,2)

        modlFld, modlLbl = 'WOMAid', 'SAP WO/MAdj Num'
        self.wdgtWOMAid = cQFmFldWidg(QLineEdit, lblText=modlLbl, modlFld=modlFld, parent=self)
        wdgt = self.wdgtWOMAid
        wdgt._wdgt.setMaximumWidth(150)
        self.formFields[modlFld] = wdgt
        wdgt.signalFldChanged.connect(lambda: self.changeField(self.wdgtWOMAid))
        self.layoutFormHdr.addWidget(wdgt,2,1,1,6)

        modlFld, modlLbl = 'Project', 'Prj/Bldg/Testr'
        choices = {rec.ProjectName:rec.id for rec in L6L10sellRepositories.Projects.get_all()}
        self.wdgtProject = cQFmFldWidg(cComboBoxFromDict, lblText=modlLbl, modlFld=modlFld, choices=choices, parent=self)
        wdgt = self.wdgtProject
        self.formFields[modlFld] = wdgt
        wdgt.signalFldChanged.connect(lambda: self.changeField(self.wdgtProject))
        self.layoutFormHdr.addWidget(wdgt,2,7,1,6)

        modlFld, modlLbl = 'WOType', 'CIMS WO Type'
        self.wdgtWOType = cQFmFldWidg(QLineEdit, lblText=modlLbl, modlFld=modlFld, parent=self)
        wdgt = self.wdgtWOType
        wdgt._wdgt.setMaximumWidth(150)
        self.formFields[modlFld] = wdgt
        wdgt.signalFldChanged.connect(lambda: self.changeField(self.wdgtWOType))
        self.layoutFormHdr.addWidget(wdgt,2,13,1,6)

        self.layoutForm.addLayout(self.layoutFormHdr)
        self.layoutForm.addSpacing(10)

        self.layoutFormMain = QHBoxLayout()
        self.wdgtFormMainNav = QListWidget()
        self.wdgtFormMainNav.setMaximumWidth(150)
        self.wdgtFormMainNav.itemActivated.connect(self.getRecordFromNav)
        self.layoutFormMainMain = QVBoxLayout()

        self.layoutFormMain.addWidget(self.wdgtFormMainNav)
        self.layoutFormMain.addLayout(self.layoutFormMainMain)
        
        # label: Parts Needed
        
        scrollarea = QScrollArea()
        scrollarea.setWidgetResizable(True)
        GPNList_containerWdgt = QWidget()
        scrollarea.setWidget(GPNList_containerWdgt)
        self.layoutGPNList = QVBoxLayout(GPNList_containerWdgt)
        self.layoutGPNList.setSpacing(0)
        self.layoutGPNList.setContentsMargins(0, 0, 0, 0)
        
        self.layoutFormMainMain.addWidget(self.HdrGPNList())
        self.layoutFormMainMain.addWidget(scrollarea)
        
        self.layoutForm.addLayout(self.layoutFormMain)

        # make this a new record
        self.currRec = WorkOrders()
        self.fillWONavList()
        self.fillFormFromcurrRec()
        
    # __init__

    def fillWONavList(self):
        self.WOList_items = {}      # dictionary to store {id: QListWidgetItem}

        # T = L6L10sellRepositories.WorkOrders.get_all(order_by='CIMSNum')
        T = L6L10sellRepositories.WorkOrders.get_all(order_by=WorkOrders.CIMSNum)

        self.wdgtFormMainNav.clear()
        
        for row in T:
            CIMSNum = str(row.CIMSNum)
            tblid = row.id
            itm = QListWidgetItem()
            itm.setText(CIMSNum)
            itm.setData(Qt.ItemDataRole.UserRole, tblid)
            self.wdgtFormMainNav.addItem(itm)
            self.WOList_items[tblid] = itm      # store ref to item for later lookup and ref
        #endfor each row
    # fillWONavList

    @Slot()
    def getRecordFromGoto(self) -> None:
        #TODO: check if dirty

        slctd = self.wdgtCIMSNum.Value()
        assert isinstance(slctd, dict), "Expected a dictionary from cDataList"
        CIMSNumber = slctd['text']
        id = slctd['keys'][0] if len(slctd['keys']) else None
        self.lblNewCIMSNum.setText('')
        if not id and CIMSNumber:
            self.currRec = self.createNewWORec(CIMSNumber)

            self.setFormDirty(self.wdgtCIMSNum, True)
        # endif not id
        
        if id:
            self.getRecordfromdb(id)
        else:
            self.fillFormFromcurrRec()
        #endif id
    # getRecordFromGoto

    @Slot()
    def getRecordFromNav(self, listitm:QListWidgetItem) -> None:
        #TODO: check if dirty

        CIMSNumber = listitm.text()
        id = listitm.data(Qt.ItemDataRole.UserRole)
        self.lblNewCIMSNum.setText('')
        if not id and CIMSNumber:
            self.currRec = self.createNewWORec(CIMSNumber)

            self.setFormDirty(self.wdgtCIMSNum, True)
        # endif not id
        
        if id:
            self.getRecordfromdb(id)
        else:
            self.fillFormFromcurrRec()
        #endif id
    # getRecordFromGoto


    ##########################################
    ########    Create

    def createNewWORec(self, CIMSNumber:str|None = None) -> WorkOrders:
        # create new HBL record
        newrec:WorkOrders = WorkOrders()
        # newrec.setNull('id')  # no longer necessary??
        if CIMSNumber:
            newrec.CIMSNum = CIMSNumber
        newrec.WOType = 'WO'     # consider dumping this fld

        return newrec


    ##########################################
    ########    Read

    def getRecordfromdb(self, recid:int, createFlag:bool = False) -> int:
        T = L6L10sellRepositories.WorkOrders.get_by_id(recid, newifnotfound=createFlag)
        self.currRec = T
        self.fillFormFromcurrRec()
        
        if recid in self.WOList_items:
            self.wdgtFormMainNav.setCurrentItem(self.WOList_items[recid])
        else:
            qDebug(f'no Nav List item found with {recid}')

        return self.currRec.id if self.currRec else 0

    # getRecordfromdb

    def fillFormFromcurrRec(self):
        cRec = self.currRec
        assert isinstance(cRec, WorkOrders), "Current record must be a WorkOrders instance"
        forgnKeys = {
            'Project': cRec.project.ProjectName if cRec.project else '' ,
            }
    
        # set pk display
        self.lblRecID.setText(str(cRec.id))

        for fieldname in cRec.__table__.columns.keys():
            if fieldname[-3:]=='_id':
                fieldname = fieldname[:-3]

            field_value = getattr(cRec, fieldname, None)
            field_valueStr = str(field_value)
            # transform values for foreign keys and lookups
            if fieldname in forgnKeys:
                field_valueStr = str(forgnKeys[fieldname])
            
            if fieldname in self.formFields:
                wdgt = self.formFields[fieldname]
                if hasattr(wdgt, 'setValue'):
                    wdgt.setValue(field_valueStr)   # type: ignore
            # endif fieldname in self.formFields
        #endfor field in cRec

        
        self.lblNewCIMSNum.setText(
            f'New Work Order' if cRec.id is None and not cRec.CIMSNum is None
            else ''
            )

        self.btnDelete.setEnabled(not cRec.id is None)

        self.fillPartsNeededSubForm()
        self.setFormDirty(self, False)
    # fillFormFromcurrRec

    def fillPartsNeededSubForm(self):
        cRec = self.currRec

        # clear self.layoutGPNList
        clearLayout(self.layoutGPNList)

        PartsNeededRecordset = cRec.parts_needed if cRec and cRec.id else []
        if not PartsNeededRecordset:
            PartsNeededRecordset = []

        for rec in PartsNeededRecordset:
            # add WOPartsNeeded_LineItem to self.layoutGPNList
            self.layoutGPNList.addWidget(WOPartsNeeded_LineItem(rec))
    # fillPartsNeededSubForm
    
    
    ##########################################
    ########    Update

    @Slot()
    def changeField(self, wdgt:cQFmFldWidg) -> bool:
        cRec = self.currRec
        assert isinstance(cRec, WorkOrders), "Current record must be a WorkOrders instance"
        dbField = wdgt.modelField()
        assert dbField, "Widget must have a model field defined"
        wdgt_value = wdgt.Value()
        
        forgnKeys = {
            'Project': None,
        }
        
        if dbField in forgnKeys:
            dbField += '_id'
        
        if wdgt_value or isinstance(wdgt_value,bool):
            cRec.setValue(dbField, wdgt_value)
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
        assert isinstance(cRec, WorkOrders), "Current record must be a WorkOrders instance"
        newrec = (cRec.id is None)

        # check required fields - done in isFormDirty -  btnCommit only enabled when all required present
        
        pk = -1
        if newrec:
            with app_Session() as session:
                session.add(cRec)
                session.commit()
                pk = cRec.id

            self.fillWONavList()
        else:
            with app_Session() as session:
                session.merge(cRec)
                session.commit()
                pk = cRec.id
        #endif newrec

        if newrec:
            # add this record to self.gotoHBL.completer().model()
            self.wdgtCIMSNum.addChoices({pk: str(cRec.CIMSNum)})
            self.getRecordfromdb(pk)    # refresh the form
        #endif newrec
        
        self.setFormDirty(self, False)


    ##########################################
    ########    Delete

    @Slot()
    def deleteRecord(self):
        cRec = self.currRec
        assert isinstance(cRec, WorkOrders), "Current record must be a WorkOrders instance"

        with app_Session() as session:
            session.delete(cRec)
            session.commit()
        
        # clear the form
        self.currRec = self.createNewWORec()
        self.fillFormFromcurrRec()
        self.fillWONavList()
    # deleteRecord


    ##########################################
    ########    CRUD support

    @Slot()
    def setFormDirty(self, wdgt:QWidget, dirty:bool = True):
        wdgt.setProperty('dirty', dirty)
        # if wdgt === self, set all children dirty
        if wdgt is not self:
            if dirty: self.setProperty('dirty',True)
        else:
            for W in self.children():
                if any([W.inherits(tp) for tp in ['QLineEdit', 'QTextEdit', 'QCheckBox', 'QComboBox', 'QDateEdit']]):
                    W.setProperty('dirty', dirty)
        
        allRequiredFldsGiven = all([(getattr(self.currRec, fld, None) is not None) for fld in self.requiredFlds])

        # enable btnCommit if all required fields dirty
        self.btnCommit.setEnabled(self.isFormDirty() and allRequiredFldsGiven)
    
    def isFormDirty(self) -> bool:
        return self.property('dirty')



####################################################################
####################################################################
####################################################################

