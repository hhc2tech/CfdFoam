# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
# *   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

from PySide import QtGui, QtCore
from PySide.QtCore import QObject, Signal, Slot, QThread

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar


# See example from http://matplotlib.org/examples/user_interfaces/embedding_in_qt4.html
class ResidualPlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5.0, height=4.0, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.canvas = FigureCanvas(fig)
        self.ax = fig.add_subplot(111)

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.updated = False
        self.UxResiduals = []
        self.UyResiduals = []
        self.UzResiduals = []
        self.pResiduals = []

    def compute_initial_figure(self):
        self.ax.set_title("Simulation residuals")
        self.ax.set_xlabel("Iteration")
        self.ax.set_ylabel("Residual")
        self.ax.set_yscale('log')
        self.ax.grid()

    def updateResiduals(self, UxResiduals, UyResiduals, UzResiduals, pResiduals):
        self.updated = True
        self.UxResiduals = UxResiduals
        self.UyResiduals = UyResiduals
        self.UzResiduals = UzResiduals
        self.pResiduals = pResiduals

    def refresh(self):
        if self.updated:
            self.updated = False
            self.ax.cla()
            self.ax.set_title("Simulation residuals")
            self.ax.set_xlabel("Iteration")
            self.ax.set_ylabel("Residual")

            self.ax.plot(self.UxResiduals, label="Ux", color='violet', linewidth=1)
            self.ax.plot(self.UyResiduals, label="Uy", color='green', linewidth=1)
            self.ax.plot(self.UzResiduals, label="Uz", color='blue', linewidth=1)
            self.ax.plot(self.pResiduals, label="p", color='orange', linewidth=1)

            self.ax.grid()
            self.ax.set_yscale('log')
            self.ax.legend()

            self.draw()


class ResidualPlotWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.main_widget = QtGui.QWidget(self)

        l = QtGui.QVBoxLayout(self.main_widget)
        dc = ResidualPlotCanvas(self.main_widget, width=6.5, height=5, dpi=100)
        l.addWidget(dc)

        self.dc = dc
        self.navi_toolbar = NavigationToolbar(self.dc, self)
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.navi_toolbar)

        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)


class PlottingWorker(QObject):
    def __init__(self):
        super(PlottingWorker, self).__init__()
        self.Timer = QtCore.QTimer()
        self.Timer.timeout.connect(self.refresh)
        self.Timer.start(1000)
        self.window = ResidualPlotWindow()

    @Slot(list, list, list, list)
    def updateResiduals(self, UxResiduals, UyResiduals, UzResiduals, pResiduals):
        self.window.dc.updateResiduals(UxResiduals, UyResiduals, UzResiduals, pResiduals)
        self.window.show()

    def refresh(self):
        self.window.dc.refresh()
