import sys
from PyQt5.QtWidgets import QApplication
from core.window import Ui

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = Ui()
    sys.exit(app.exec_())
