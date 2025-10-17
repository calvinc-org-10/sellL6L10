# the Main Screen must be in a separate file because it has to be loaded AFTER django support

from PySide6.QtCore import (QCoreApplication, QMetaObject, )
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, )

from cMenu.cMenu import cMenu
from sysver import _appname, sysver, sysver_key

class MainScreen(QWidget):
    def __init__(self, parent:QWidget = None):
        super().__init__(parent)
        if not self.objectName():
            self.setObjectName(u"MainWindow")
        
        scrollarea = QScrollArea()
        scrollarea.setWidgetResizable(True)
        # scrollarea.setWidget(self)

        theMenu = cMenu(self)

        llayout = QVBoxLayout(self)        # self.setLayout(llayout)
        llayout.addWidget(theMenu)

        self.retranslateUi()

        # QMetaObject.connectSlotsByName(self)
    # __init__

    def retranslateUi(self):
        self.setWindowTitle(QCoreApplication.translate("MainWindow", _appname, None))
    # retranslateUi

