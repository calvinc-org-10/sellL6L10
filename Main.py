import sys
from PySide6.QtWidgets import QApplication



if __name__ == "__main__":
    app = QApplication(sys.argv)

    from MainScreen import MainScreen   # QApplication must exist before this import (qt.sql.qsqldatabase: QSqlDatabase requires a QCoreApplication)
    topscreen = MainScreen()
    topscreen.show()

    sys.exit(app.exec())
