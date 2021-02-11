import sys

# Import QApplication and the required widgets from PyQt5.QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QRect, QCoreApplication
from PyQt5.QtGui import QPixmap
from functools import partial
#from digest import *
from digest import *



# Create a subclass of QMainWindow to setup the calculator's GUI
class Transmuter(QMainWindow):
    """PyCalc's View (GUI)."""
    def __init__(self):
        """View initializer."""
        super().__init__()
        # Set some main window's properties
        self.setWindowTitle('Link Analysis Transmuter')
        # Set the central widget and the general layout
        self.generalLayout = QVBoxLayout()
        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)
        self._centralWidget.setLayout(self.generalLayout)

        self._createButtons()
        self._createComboBox1()
        self._createComboBox2()
        self._imagePlaceHolder()


    def _createButtons(self):
        self.buttonsLayout = QGridLayout()

        self.jsonButton = QPushButton("Input JSON File")
        self.imageButton = QPushButton("Load Image")
        self.xlsButton = QPushButton("Generate XLS")

        self.buttonsLayout.addWidget(self.jsonButton, 0, 0)
        self.buttonsLayout.addWidget(self.imageButton, 1, 0)
        self.buttonsLayout.addWidget(self.xlsButton, 2, 0, 1, 0)

        self.generalLayout.addLayout(self.buttonsLayout)

    def _createComboBox1(self):
        self.combo_box1 = QComboBox(self)
        self.combo_box1.setFixedHeight(32)
        self.buttonsLayout.addWidget(self.combo_box1, 0, 1)

    def _seedList(self, seedNode):
        self.seedNode = seedNode


    def _moduleList(self, module):
        self.module = module

    def _createComboBox2(self):
        module_list = ["Select Module", "Relationship", "Transaction Flow (TDS)", "Transaction Flow (GST)", "Shareholders"]
        self.combo_box2 = QComboBox(self)
        self.combo_box2.setFixedHeight(32)
        self.buttonsLayout.addWidget(self.combo_box2, 1, 1)
        self.combo_box2.clear()
        self.combo_box2.addItems(module_list)


    def _imagePlaceHolder(self):
        self.gridlayout = QGridLayout(self)
        linebox = QLineEdit(self)
        linebox.setReadOnly(True)
        linebox.setFixedSize(810, 310)
        self.gridlayout.addWidget(linebox, 0, 0)
        self.generalLayout.addLayout(self.gridlayout)


    def _displayImage(self):
        img_path = QFileDialog.getOpenFileName(self, caption='Get a JSON from', filter='JSON Files(*.*)')[0]
        label = QLabel(self)
        pixmap = QPixmap(img_path)
        label.setPixmap(pixmap)
        label.setScaledContents(True)
        label.setFixedSize(1000, 510)
        self.gridlayout.addWidget(label, 0, 0)
        self.resize(pixmap.width(), pixmap.height())
        self.generalLayout.addLayout(self.gridlayout)
        self.img_path = img_path

    def _selectFile(self):
        path = QFileDialog.getOpenFileName(self, caption='Get a JSON from', filter='JSON Files(*.json)')[0]

        if path == "":
            return None
        else:
            data = getInputJson(path)

            try:
                nodes, edges = normalizeJson(data)
                self.nodes = nodes
                self.edges = edges
                seed_list = getAvailableSeed(self.nodes)['PAN Name'].tolist()
                self.combo_box1.clear()
                self.combo_box1.addItems(seed_list)

            except Exception as e:
                pass


            flattenData(self.nodes, self.edges)

            #related_nodes, related_links = flattenData(self.nodes, self.edges, self.module)
            #self.related_nodes = related_nodes
            #self.related_links = related_links

        #return
        #generateXLS(seed_node, module, related_nodes, related_links, img_path)
    def _generateXLS(self):
        try:
            status = generateXLS(self.seedNode, self.module, self.nodes, self.edges, self.img_path)

            if status:

                chk = QLabel(self)
                chk.setText("JSON has been transmuted to XLS successfully!")
                self.generalLayout.addWidget(chk)
            else:
                chk = QLabel(self)
                chk.setText("Error!")
                self.generalLayout.addWidget(chk)
        except Exception as e:
            print(e)



class TransmuterCtrl():

    def __init__(self, view):
        """Controller initializer."""
        self._view = view
        # Connect signals and slots
        self._connectSignals()


    def _connectSignals(self):
        """Connect signals and slots."""

        self._view.jsonButton.clicked.connect(partial(self._view._selectFile))
        self._view.imageButton.clicked.connect(partial(self._view._displayImage))
        self._view.combo_box1.activated[str].connect(partial(self._view._seedList))
        self._view.combo_box2.activated[str].connect(partial(self._view._moduleList))
        self._view.xlsButton.clicked.connect(partial(self._view._generateXLS))

# Client code
def main():
    """Main function."""
    # Create an instance of QApplication
    app = QApplication(sys.argv)
    view = Transmuter()
    view.show()
    TransmuterCtrl(view=view)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()