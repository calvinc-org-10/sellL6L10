from typing import Dict, List

from PySide6.QtCore import (QCoreApplication, 
    QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt,
    Signal, Slot, )
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout,
    QDialog, QMessageBox, QDialogButtonBox, 
    QLabel, QLCDNumber, QPushButton, QLineEdit, QCheckBox, QComboBox, QTextEdit, 
        QSpinBox, QButtonGroup, QRadioButton, QGroupBox, 
    QFrame, QSizePolicy, 
    )
from PySide6.QtSvgWidgets import QSvgWidget

from .dbmenulist import MenuRecords
from sysver import sysver
from .menucommand_constants import MENUCOMMANDS, COMMANDNUMBER
from . import menucommand_handlers
from .utils import (cComboBoxFromDict, pleaseWriteMe, )

# TODO: put in class?
# cMenu-related constants
_SCRN_menuBTNWIDTH:int = 250
_SCRN_menuDIVWIDTH:int = 40
_NUM_menuBUTTONS:int = 20
_NUM_menuBUTNCOLS:int = 2
_NUM_menuBTNperCOL: int = int(_NUM_menuBUTTONS/_NUM_menuBUTNCOLS)

#############################################
#############################################
#############################################

class cMenu(QWidget):
    # more class constants
    _DFLT_menuGroup: int = -1
    _DFLT_menuID: int = -1
    menuGroup:int = _DFLT_menuGroup
    intmenuID:int = _DFLT_menuID
    
    # don't try to do this here - QWidgets cannot be created before QApplication
    # menuScreen: QWidget = QWidget()
    # menuLayout: QGridLayout = QGridLayout()
    # menuButton: Dict[int, QPushButton] = {}
    class menuBUTTON(QPushButton):
        btnNumber:int = 0
        def __init__(self, btnNumber:int):
            super().__init__()
            self.btnNumber = btnNumber
            self.setText("\n\n")
            self.setObjectName(f'cMenuBTN-{btnNumber}')
            
    def __init__(self, parent:QWidget|None, initMenu=(0,0)): # , mWidth=None, mHeight=None):
        super().__init__(parent)
        
        self.menuLayout: QGridLayout = QGridLayout()
        self.menuButton: Dict[int, cMenu.menuBUTTON] = {}
        self.menuHdrLayout: QHBoxLayout = QHBoxLayout()
        self.lblmenuGroupID:  QLCDNumber = QLCDNumber(3)
        self.lblmenuID:  QLCDNumber = QLCDNumber(3)
        self.lblVersion: QLabel = QLabel('')
        self.layoutMenuID:QGridLayout = QGridLayout()
        self.lblmenuName: QLabel = QLabel("")
        self._menuSOURCE = MenuRecords()
        self.currentMenu: Dict[int,Dict] = {}
        
        self.childScreens: Dict[str,QWidget] = {}

        self.menuLayout.setColumnMinimumWidth(0,40)
        self.menuLayout.setColumnStretch(1,1)
        self.menuLayout.setColumnStretch(2,0)
        self.menuLayout.setColumnStretch(3,1)
        self.menuLayout.setColumnMinimumWidth(1,_SCRN_menuBTNWIDTH)
        self.menuLayout.setColumnMinimumWidth(2,_SCRN_menuDIVWIDTH)
        self.menuLayout.setColumnMinimumWidth(3,_SCRN_menuBTNWIDTH)
        self.menuLayout.setColumnMinimumWidth(4,40)
        
        self.lblVersion.setFont(QFont("Arial",8))
        # self.lblmenuID.setMargin(10)
        self.lblmenuName.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        self.lblmenuName.setFont(QFont("Century Gothic", 24))
        self.lblmenuName.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        # self.menuName.setMargin(20)
        self.lblmenuName.setWordWrap(False)
        
        self.layoutMenuID.addWidget(self.lblmenuGroupID,0,0)
        self.layoutMenuID.addWidget(self.lblmenuID,0,1)
        self.layoutMenuID.addWidget(self.lblVersion,1,0,1,2)
        
        self.menuHdrLayout.addLayout(self.layoutMenuID, stretch=0)
        self.menuHdrLayout.addSpacing(30)
        self.menuHdrLayout.addWidget(self.lblmenuName, stretch=1)
        self.menuLayout.addLayout(self.menuHdrLayout,0,0,1,5)
        
        for bNum in range(_NUM_menuBTNperCOL):
            self.menuButton[bNum] = self.menuBUTTON(bNum+1)
            self.menuButton[bNum+_NUM_menuBTNperCOL] = self.menuBUTTON(bNum+1+_NUM_menuBTNperCOL)
            
            self.menuLayout.addWidget(self.menuButton[bNum],bNum+2,1)
            self.menuLayout.addWidget(self.menuButton[bNum+_NUM_menuBTNperCOL],bNum+2,3)
            
            self.menuButton[bNum].clicked.connect(self.handleMenuButtonClick)
            self.menuButton[bNum+_NUM_menuBTNperCOL].clicked.connect(self.handleMenuButtonClick)
        # endfor

        self.setLayout(self.menuLayout)

        self.loadMenu()
    # __init__

    def open_childScreen(self, window_id:str, childScreen: QWidget):
        if window_id not in self.childScreens:
            childScreen.setProperty('id', window_id)
            childScreen.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            childScreen.destroyed.connect(lambda scrn: self.childScreens.pop(scrn.property('id')))
            self.childScreens[window_id] = childScreen
            childScreen.show()

    def clearoutMenu(self):
        self.lblmenuID.display("")
        self.lblmenuName.setText("")
        for bNum in range(_NUM_menuBTNperCOL):
            self.menuButton[bNum].setText("\n\n")
            self.menuButton[bNum].setEnabled(False)
            self.menuButton[bNum+_NUM_menuBTNperCOL].setText("\n\n")
            self.menuButton[bNum+_NUM_menuBTNperCOL].setEnabled(False)
    
    def displayMenu(self, menuGroup:int, menuID:int, menuItems:Dict[int,Dict]):
        # self.lblmenuID.setText(f'{menuGroup},{menuID}\n{sysver["DEV"]}')
        self.lblmenuGroupID.display(menuGroup)
        self.lblmenuID.display(menuID)
        self.lblVersion.setText(sysver["DEV"])
        self.lblmenuName.setText(str(menuItems[0]['OptionText']))
        for n in range(_NUM_menuBUTTONS):
            if n+1 in menuItems:
                self.menuButton[n].setText(f'\n{menuItems[n+1]["OptionText"]}\n')
                self.menuButton[n].setEnabled(True)
            else:
                self.menuButton[n].setText(f'\n\n')
                self.menuButton[n].setEnabled(False)
                pass
     
    def loadMenu(self, menuGroup: int = menuGroup, menuID: int = _DFLT_menuID):
        SRC = self._menuSOURCE
        if menuGroup==self._DFLT_menuGroup:
            _menuGroup = SRC.dfltMenuGroup()
            if _menuGroup is None:
                # no default menu group; say so
                msg = QMessageBox(self)
                msg.setWindowTitle('No Default Menu Group')
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.setText('No default menu group defined!')
                msg.open()
                return
            menuGroup = _menuGroup
        if menuID==self._DFLT_menuID:
            _menuID = SRC.dfltMenuID_forGroup(menuGroup)
            if _menuID is None:
                # no default menu ID for this group; say so
                msg = QMessageBox(self)
                msg.setWindowTitle('No Default Menu ID')
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.setText(f'No default menu ID defined for group {menuGroup}!')
                msg.open()
                return
            menuID = _menuID
    
        self.intmenuGroup = menuGroup
        self.intmenuID = menuID
        
        if SRC.menuExist(menuGroup, menuID):
            self.currentMenu = SRC.menuDict(menuGroup, menuID)
            self.displayMenu(menuGroup, menuID, self.currentMenu)
        else:
            # menu doesn't exist; say so
            msg = QMessageBox(self)
            msg.setWindowTitle('Menu Doesn\'t Exist')
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.setText(f'Menu {menuID} does\'t exist!')
            msg.open()
    
    @Slot()
    def handleMenuButtonClick(self):
        pressedBtn = self.sender()  # sender() should be a menuBUTTON
        if not isinstance(pressedBtn, cMenu.menuBUTTON):
            # not a menu button, so ignore
            return
        pressedBtnNum = pressedBtn.btnNumber
        menuItem = self.currentMenu[pressedBtnNum]
        # print(f'{menuItem}')
        # return
        CommandNum = menuItem['Command']
        CommandArg = menuItem['Argument']

        if MENUCOMMANDS.get(CommandNum) == 'LoadMenu' :
            CommandArg = int(CommandArg)
            self.loadMenu(self.menuGroup, CommandArg)
        elif MENUCOMMANDS.get(CommandNum) == 'FormBrowse':
            frm = menucommand_handlers.FormBrowse(self, CommandArg.lower())
            if frm is not None: 
                self.open_childScreen(CommandArg, frm)
        elif MENUCOMMANDS.get(CommandNum) == 'OpenTable' :
            CmdFm = menucommand_handlers._internalForms.OpenTable
            frm = menucommand_handlers.FormBrowse(self, CmdFm, CommandArg)
            if frm is not None: 
                self.open_childScreen(CmdFm, frm)
        elif MENUCOMMANDS.get(CommandNum) == 'RunSQLStatement':
            CmdFm = menucommand_handlers._internalForms.RunSQLStatement
            frm = menucommand_handlers.FormBrowse(self, CmdFm)
            if frm is not None: 
                self.open_childScreen(CmdFm, frm)
        # elif MENUCOMMANDS.get(CommandNum) == 'ConstructSQLStatement':
        #    pass
        # elif MENUCOMMANDS.get(CommandNum)  == 'LoadExtWebPage':
        #     return
            # retHTTP = fn_LoadExtWebPage(req, CommandArg)
        # elif MENUCOMMANDS.get(CommandNum) == 'ChangePW':
        #     return
            # return redirect('change_password')
        elif MENUCOMMANDS.get(CommandNum) == 'EditMenu':
            CmdFm = menucommand_handlers._internalForms.EditMenu
            frm = menucommand_handlers.FormBrowse(self, CmdFm)
            if frm: 
                self.open_childScreen(CmdFm, frm)
        # elif MENUCOMMANDS.get(CommandNum) == 'EditParameters':
        #     return
            # return redirect('EditParms')
        # elif MENUCOMMANDS.get(CommandNum) == 'EditGreetings':
        #     return
            # return redirect('Greetings')
        elif MENUCOMMANDS.get(CommandNum) == 'ExitApplication':
            # exit the application
            appinst = QApplication.instance()
            if appinst is not None:
                appinst.quit()
        elif CommandNum in MENUCOMMANDS:
            msg = QMessageBox(self)
            msg.setWindowTitle('Command Not Implemented')
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.setText(f'Command {MENUCOMMANDS.get(CommandNum)} will be implemented later')
            msg.open()
        else:
            # invalid Command Number
            msg = QMessageBox(self)
            msg.setWindowTitle('Invalid Command')
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.setText(f'{CommandNum} is an invalid Command Number!')
            msg.open()
        # case MENUCOMMANDS.get(CommandNum)
    # handleMenuButtonClick

###############################################################
###############################################################


###############################################################
###############################################################
###############################################################


