
from PySide6.QtCore import (
    Qt, QMetaObject, 
    QRect, QSize, 
    )
from PySide6.QtGui import (
    QFont, 
    )
from PySide6.QtWidgets import (
    QWidget, 
    QLabel, 
    QMessageBox, QDialog, QDialogButtonBox, 
    )
from PySide6.QtSvgWidgets import QSvgWidget


# standard window and related sizes
# copied from main app's forms module
std_windowsize = QSize(1120,720)
std_popdialogsize=QSize(400,300)


def pleaseWriteMe(parent, addlmessage):
    """Display a message box indicating that a feature needs to be implemented.
    
    Args:
        parent: Parent widget for the message box.
        addlmessage: Additional message to display to the user.
    """
    msg = QMessageBox(parent)
    msg.setWindowTitle('Please Write Me')
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.setText(f'Calvin needs to get up off his butt and write some code\n{addlmessage}')
    msg.open()

# TODO: pass in YesAction, NoAction
def areYouSure(parent:QWidget, title:str, 
        areYouSureQuestion:str, 
        answerChoices:QMessageBox.StandardButton = QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,
        dfltAnswer:QMessageBox.StandardButton = QMessageBox.StandardButton.No,
        ) -> QMessageBox.StandardButton:
    """Display a confirmation dialog and return the user's choice.
    
    Args:
        parent (QWidget): Parent widget for the message box.
        title (str): Title of the message box.
        areYouSureQuestion (str): Question to ask the user.
        answerChoices (QMessageBox.StandardButton, optional): Available answer buttons.
            Defaults to Yes|No.
        dfltAnswer (QMessageBox.StandardButton, optional): Default button.
            Defaults to No.
    
    Returns:
        QMessageBox.StandardButton: The button that was clicked.
    """
    ret = QMessageBox.question(parent, title,
        areYouSureQuestion, answerChoices, dfltAnswer)
    return ret

class UnderConstruction_Dialog(QDialog):
    """A dialog that displays an 'under construction' message with a barrier icon.
    
    Attributes:
        _svg_constr_barrier (str): Path to the construction barrier SVG icon.
    """
    _svg_constr_barrier = 'assets/svg/under-construction-barrier-icon.svg'
    
    def __init__(self, parent:QWidget|None = None, constructionMsg:str = '', f:Qt.WindowType = Qt.WindowType.Dialog):
        """Initialize the under construction dialog.
        
        Args:
            parent (QWidget | None, optional): Parent widget. Defaults to None.
            constructionMsg (str, optional): Message to display. Defaults to ''.
            f (Qt.WindowType, optional): Window type flags. Defaults to Qt.WindowType.Dialog.
        """
        super().__init__(parent, f)

        if not self.objectName():
            self.setObjectName(u"Dialog")
        self.resize(std_popdialogsize)
        self.setWindowTitle('Not Built Yet')
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(30, 260, 341, 32))
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setCenterButtons(True)
        self.constrsign = QSvgWidget(self._svg_constr_barrier,self)
        self.constrsign.setObjectName(u"constrwidget")
        self.constrsign.setGeometry(QRect(10, 60, 381, 191))
        self.label = QLabel(self)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 10, 381, 51))
        font = QFont()
        font.setPointSize(12)
        font.setKerning(False)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.label.setWordWrap(True)
        self.label.setText(constructionMsg)

        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.accepted.connect(self.accept)

        QMetaObject.connectSlotsByName(self)
    # __init__

