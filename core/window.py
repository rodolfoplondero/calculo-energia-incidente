import math
import os, sys
import pathlib
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
from PyQt5 import uic
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QLineEdit, QToolButton, QComboBox, QCheckBox, QListWidget, QRadioButton, QFileDialog
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QMainWindow, QPushButton, QApplication, QAbstractItemView, QSizePolicy
from plotly.subplots import make_subplots

from .calc_ei import calc_by_ASTM, calc_by_energia_interna

pathdir = pathlib.Path(__file__).parent.absolute()


class Ui(QMainWindow):
    colunas_temp = list()
    colunas_ei   = list()
    EIs    = list()
    max_EI = 0
    max_EI_name = ''
    min_EI = 1000
    min_EI_name = ''

    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi(f'{pathdir}/window.ui', self)

        self.initUI()

    def initUI(self):
        """ Initializes the window """

        self.setWindowTitle("Calculo de Energia Incidente")

        self.getComponents()
        self.setCommands()

        self.show()
        self.openFileNameDialog()

    def getComponents(self):
        """ Find components in window.ui and set to self variables """
        self.lineEdit        = self.findChild(QLineEdit,   'lineEdit')        # type: QLineEdit
        self.btnFile         = self.findChild(QToolButton, 'toolButton')      # type: QToolButton
        self.btnCalcular     = self.findChild(QPushButton, 'btnCalcular')     # type: QToolButton
        self.btnAtualizar    = self.findChild(QPushButton, 'btnAtualizar')    # type: QToolButton
        self.comboBoxSep     = self.findChild(QComboBox,   'comboBoxSep')     # type: QComboBox
        self.comboBoxDecimal = self.findChild(QComboBox,   'comboBoxDecimal') # type: QComboBox
        self.checkBoxHTML    = self.findChild(QCheckBox,   'checkBoxHTML')    # type: QCheckBox
        self.checkBoxCSV     = self.findChild(QCheckBox,   'checkBoxCSV')     # type: QCheckBox       
        self.checkBoxPDF     = self.findChild(QCheckBox,   'checkBoxPDF')     # type: QCheckBox
        self.checkBoxSVG     = self.findChild(QCheckBox,   'checkBoxSVG')     # type: QCheckBox
        self.checkBoxPlotar  = self.findChild(QCheckBox,   'checkBoxPlotar')  # type: QCheckBox
        self.listFiles       = self.findChild(QListWidget, 'listFiles')       # type: QListWidget
        self.listColunas     = self.findChild(QListWidget, 'listColunas')     # type: QListWidget

        self.listFiles.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def setCommands(self):
        """ Set actions to window elements """
        self.btnFile.clicked.connect(self.openFileNameDialog)
        self.btnCalcular.clicked.connect(self.calcular_ei)
        self.btnAtualizar.clicked.connect(self.abrirArquivos)
        self.comboBoxSep.currentTextChanged.connect(self.abrirArquivos)
        self.comboBoxDecimal.currentTextChanged.connect(self.abrirArquivos)
        self.lineEdit.textChanged.connect(self.abrirArquivos)

    def openFileNameDialog(self):
        """ Open FileDialog and get the full path of a file """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self, 
                                                 "Select a report file", 
                                                 "",
                                                 "Report Files (*.csv *.out);; All Files (*)", 
                                                 options=options)
        if fileName:
            self.lineEdit.setText(fileName)

    def abrirArquivos(self):
        """ Open the selected file and get it columns """
        try:
            fileName = self.lineEdit.text()

            # Check if the file is selected
            if fileName == "":
                raise Exception("Selecione um arquivo para abrir")

            # Set the separator and decimal mark
            separador = " " if str(self.comboBoxSep.currentText()) == "Espaço" else str(self.comboBoxSep.currentText())
            decimal = str(self.comboBoxDecimal.currentText())

            # Get the file extension
            _, file_extension = os.path.splitext(fileName)

            # Open the file
            if file_extension == ".csv":
                self.df = pd.read_csv(fileName, sep=separador, decimal=decimal)  # type: pd.DataFrame
            elif file_extension == ".out":
                self.df = self.readOutFile(fileName)

            # Clear the list with the columns
            self.listFiles.clear()

            # Get the columns from file
            for c in self.df.columns:
                if c.lower().strip().replace(" ", "-") not in ['time-step', 'flow-time']:
                    self.listFiles.addItem(c)

        except Exception as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Erro")
            msg.setInformativeText("{0}".format(e))
            msg.setWindowTitle("Erro")
            msg.exec_()

    def reset_column_list(self):
        self.listColunas.clear()

    def readOutFile(self, filename: str):
        """ Read a .out file """
        with open(filename, 'r') as f:
            content = f.read().splitlines()

            # Get title
            title = content[0].strip('"')

            # Remove the second line of the file
            content.pop(1)

            # Get columns
            columns = content[1].strip("()\n").split('"')
            for i, val in enumerate(columns):
                if val.strip() == '':
                    columns.pop(i)

            # Format values to Float
            for i in range(0, len(content[2:])):
                line = content[2:][i].strip('\n').split(' ')
                line = [float(item) for item in line]

                content[i + 2] = line

        dataframe = pd.DataFrame(content[2:], columns=columns)
        # dataframe = dataframe.set_index('Time Step')
        dataframe.name = title

        return dataframe

    def calcular_ei(self):
        """ Calculate the Incident Energy """
        try:
            # Check if the file is selected
            if self.lineEdit.text() == "":
                raise Exception("Selecione um arquivo.")

            # Check if an item is selected
            if not self.listFiles.selectedItems():
                raise Exception("Selecione uma coluna")

            path = self.lineEdit.text()
            separador = " " if str(self.comboBoxSep.currentText()) == "Espaço" else str(self.comboBoxSep.currentText())
            decimal = str(self.comboBoxDecimal.currentText())

            # selecao = self.listFiles.selectedItems()[0].text()
            # selecao = list()
            self.colunas_ei.clear()
            self.colunas_temp.clear()
            mensagem = ""

            for selected in self.listFiles.selectedItems():
                # Calc EI using ASTM 
                coluna_temp   = selected.text()
                nome_original = coluna_temp.split("(")[0]
                coluna_ei     = coluna_temp.replace(nome_original, "EI")
                self.colunas_temp.append(coluna_temp)
                self.colunas_ei.append(coluna_ei)

                if self.radioButtonASTM.isChecked():
                    self.df[coluna_ei] = calc_by_ASTM(self.df[selected.text()].tolist())
                elif self.radioButtonEnergia.isChecked():
                    self.df[coluna_ei] = calc_by_energia_interna(self.df[selected.text()].tolist())

                # Get the max EI
                max_EI = self.df[coluna_ei].max()
                mensagem += f"\n{'Máxima ' + coluna_ei + ':':<30}{max_EI:.4f} [cal/cm^2]"

                self.EIs.append(max_EI)

                old_max_ei = self.max_EI 
                self.max_EI = max(self.max_EI, max_EI)
                if old_max_ei != self.max_EI:
                    self.max_EI_name = coluna_ei

                old_min_ei = self.min_EI 
                self.min_EI = min(self.min_EI, max_EI)
                if old_min_ei != self.min_EI:
                    self.min_EI_name = coluna_ei

            # Show the results
            # self.showResults()

            # Get the max EI
            mensagem += f"\n\n{'Média EI: ':<30}{sum(self.EIs)/len(self.EIs):.4f} [cal/cm^2]"
            mensagem += f"\n{'Máxima ' + self.max_EI_name + ' =':<30}{self.max_EI:.4f} [cal/cm^2]"
            mensagem += f"\n{'Mínima ' + self.min_EI_name + ' =':<30}{self.min_EI:.4f} [cal/cm^2]"

            # Print the max EI
            print(mensagem)

            # Make a plot
            if self.checkBoxPlotar.isChecked():
                self.plot()

            self.saveCSV()

            # Show a message with the max EI
            font = QFont()
            font.setFamily("Consolas")
            font.setPointSize(9)

            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText(mensagem)
            msg.setWindowTitle("Informação")
            msg.setFont(font)
            msg.exec_()
        except Exception as e:
            print("{0}".format(e))
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Erro")
            msg.setInformativeText("{0}".format(e))
            msg.setWindowTitle("Erro")
            msg.exec_()

    def plot(self, **kwargs):
        """ Make the plot using Plotly """

        df = self.df.copy()

        fig = make_subplots(rows=1, cols=2)

        # Add the first plot related to Temperature
        for i in range(0, len(self.colunas_temp)):
            fig.add_trace(
                go.Scatter(x=df['flow-time'], y=df[self.colunas_temp[i]], name=self.colunas_temp[i]),
                row=1, col=1)

            # Add the second plot related to EI
            fig.add_trace(
                go.Scatter(x=df['flow-time'], y=df[self.colunas_ei[i]], name=self.colunas_ei[i]),
                row=1, col=2)

            # Add an annotation to show the maximum EI
            fig.add_annotation(x=df['flow-time'].iat[-1], y=df[self.colunas_ei[i]].iat[-1],
                               text=f"{df[self.colunas_ei[i]].iat[-1]:.4f}",
                               showarrow=True,
                               arrowhead=1,
                               row=1, col=2)

        # Some configuration for the plot
        fig.update_layout(title_text="Energia Incidente")

        # Save the data if some checkbox is checked
        if (self.checkBoxHTML.isChecked() or 
            self.checkBoxPDF.isChecked() or
            self.checkBoxSVG.isChecked()):
            self.saveFigure(fig)

        # Show the plot
        fig.show()

    def getSavePath(self):
        """ Get the path to save the file """
        path = QFileDialog.getExistingDirectory(self, "Salvar em", "")
        # Generate a default name for the file with datetime
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d_%H%M%S")
        name = f"Energia_Incidente_{now_str}"

        # Set the name to file
        dialog = QInputDialog()  # type: QInputDialog
        text, ok = dialog.getText(self, 'Nome do arquivo', 'Insira um nome para salvar o arquivo', text=name)
        if ok:
            name = text

        return path, name

    def saveCSV(self):
        # Save the data in CSV file
        if self.checkBoxCSV.isChecked():
            directory, name = self.getSavePath()
            
            self.df.to_csv(f"{directory}/{name}.csv",
                            sep=";",
                            columns=['flow-time'] + self.colunas_temp + self.colunas_ei,
                            index=False,
                            na_rep="NA")

    def saveFigure(self, fig: go.Figure):
        """ Save the Temperature and EI """

        directory, name = self.getSavePath()

        # Save the plot in HTML file
        if self.checkBoxHTML.isChecked():
            fig.write_html(f"{directory}/{name}.html")

        # Save the plot in PDF file
        if self.checkBoxPDF.isChecked():
            fig.write_image(f"{directory}/{name}.pdf")

        # Save the plot in SVG file
        if self.checkBoxSVG.isChecked():
            fig.update_layout(title="")
            fig.write_image(f"{directory}/{name}.svg")

        self.filename1 = None
        self.filename2 = None

    def get_max_EI(self):
        """ Return the maximum EI """
        return self.df['EI'].max()


def round_up(n, decimals=0):
    """ Round up to the next 10^n

    Args:
        n (number): the number it will be rounded
        decimals (int, optional): decimal number to round. Defaults to 0.

    Returns:
        (float): number rounded up to the next 10^n
    """
    multiplier = 10 ** decimals
    return math.ceil(n * multiplier) / multiplier



if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = Ui()
    sys.exit(app.exec_())
