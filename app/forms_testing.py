from typing import (Dict, Any, )

from PySide6.QtCore import (
    Qt, Slot, qDebug,
)
from PySide6.QtGui import (
    QFont, QColorConstants,
    QPalette, QBrush,
    QTextOption, 
    )
from PySide6.QtSql import (QSqlTableModel, QSqlRecord, QSqlQuery, QSqlQueryModel, )
from PySide6.QtWidgets import (
    QWidget, QScrollArea, QListWidget, QListWidgetItem,
    QHBoxLayout, QVBoxLayout, QGridLayout, 
    QTableView, 
    QLabel, QLineEdit, QPushButton, QTextEdit
)

from cMenu.utils import (cQFmFldWidg, cQFmNameLabel, cDataList, cComboBoxFromDict, clearLayout, )

from app.database import app_Session
from app.models import (WorkOrderPartsNeeded, WorkOrders, Parts, Projects, L6L10sellRepositories, )




class PickListReport(QWidget):
    _formname = 'Pick List Report'

    def __init__(self, includeNegativePicks:bool = False, parent:QWidget|None = None):
        super().__init__(parent)
        self._includeNegativePicks = includeNegativePicks
        
        # Layout
        layoutForm = QVBoxLayout(self)

        layoutFormHdr = QHBoxLayout()
        lblFormName = cQFmNameLabel(parent=self)
        lblFormName.setText(self.tr(self._formname))
        layoutFormHdr.addWidget(lblFormName)
        self.setWindowTitle(self.tr(self._formname))
        layoutForm.addLayout(layoutFormHdr)

        self.txtedtPickList = QTextEdit(lineWrapMode=QTextEdit.LineWrapMode.NoWrap)
        font = QFont()
        font.setFamily('Courier New')
        # font.setFixedPitch(True)
        font.setPointSize(12)
        self.setFont(font)
        layoutForm.addWidget(self.txtedtPickList)

        self.presentPicklist()

    # utility?
    def spaceoutchars(self, strInput:str) -> str:
        return '   '.join(' '.join(word) for word in strInput.split())

    def presentPicklist(self):
        # lists are faster than constantly querying the db
        lstWO = L6L10sellRepositories.WorkOrders.get_all()  # fields=['id','CIMSNum','WOMAid','Project_id','ProjectName']   
        # and convert it to a Dict -- generalize this and move to utils
        dictWO = { WO.id: WO for WO in lstWO }

        # and do the same with projects so we get the project color
        lstProj = L6L10sellRepositories.Projects.get_all()  # fields=['id','ProjectName','Color']
        # and convert it to a Dict -- generalize this and move to utils
        dictProj = { Proj.id: Proj for Proj in lstProj }
        
        tblallParts = L6L10sellRepositories.Parts.get_all(order_by='GPN')
        
        # tblWONeedingPart = L6L10sellRepositories.WorkOrderPartsNeeded.get_all()
        
        txtPickList = \
""" PICKING LIST
/\\/\\/\\/\\/\\/\\/\\

"""

        # for each Part
        for part in tblallParts:
            # collect List of WOs needing Part
            listWONeedingPart = part.workorders_needing_part

            # go through the WOList to 1) build a list and 2) get total to be picked
            totalneeded = sum(item.targetQty for item in listWONeedingPart)

            if not self._includeNegativePicks and totalneeded <= 0:
                continue
            
            # Print header
            txtPickList += \
f"""
{self.spaceoutchars(part.GPN)},  Σ = {totalneeded}
------------------------------------
"""
            # for each WO in WOList
            for rec in listWONeedingPart:
                # Print line
                tblWOid = rec.WorkOrders_id
                tblProjid = rec.workorder.Project_id
                qty = rec.targetQty
                notes = rec.notes
                txtPickList += \
f"""{rec.workorder.WOMAid} ({rec.workorder.CIMSNum}), {rec.workorder.project.ProjectName} ({rec.workorder.project.Color}), {qty}
"""
                if notes:
                    txtPickList += \
f"""    {notes}
"""
                #endif notes
                txtPickList += \
f"""
***************************************************
"""
            #endfor each WO in WOList
        #endfor each Part
        
        self.txtedtPickList.setText(txtPickList)
    # presentPicklist
