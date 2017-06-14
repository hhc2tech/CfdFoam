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

from __future__ import print_function
from PySide import QtCore
from PySide.QtCore import Qt, QRunnable, QObject, QThread


class CfdThread:
    """ Class to simplify running a function in a worker thread. Gets forcibly terminated when object is deleted.
     Supply a status function to be run in parent thread, an error message function to print the exception
     message if the worker throws an error, and a function to be called on completion. All optional."""
    def __init__(self):
        self.thread = CfdQThread()
        self.statusHook = None
        self.errorHook = None
        self.finishedHook = None

    def __del__(self):
        print("In destructor", self.thread.isRunning())
        if self.thread.isRunning():
            self.thread.terminate()

    def start(self, worker_function, **kwargs):
        """
        :param worker_function: Function to execute
        :param fn_args: List of arguments for worker function
        :param fn_kwargs: Dict of keyword-args for worker function
        :param statusHook: Function to receive status message from call in thread
        :param errorHook: Function to receive error message from exception in thread
        :param finishedHook: Function to receive completed notification (with succcess True/False)
        """
        if self.thread.isRunning():
            raise Exception("Already running")
        self.thread.function = worker_function
        self.finishedHook = kwargs.get('finishedHook')
        self.statusHook = kwargs.get('statusHook')
        self.errorHook = kwargs.get('errorHook')
        try:  # Ignore errors of signals already disconnected
            self.thread.signals.finished.disconnect()
        except RuntimeError:
            pass
        try:
            self.thread.signals.status.disconnect()
        except RuntimeError:
            pass
        try:
            self.thread.signals.error.disconnect()
        except RuntimeError:
            pass
        if self.finishedHook:
            self.thread.signals.finished.connect(self.finishedHook)
        if self.statusHook:
            self.thread.signals.status.connect(self.statusHook)
        if self.errorHook:
            self.thread.signals.error.connect(self.errorHook)
        self.thread.args = kwargs.get('fn_args', ())
        self.thread.kwargs = kwargs.get('fn_kwargs', {})
        self.thread.start()


class CfdQThreadSignals(QObject):
    error = QtCore.Signal(str)  # Signal in PySide, pyqtSignal in PyQt
    finished = QtCore.Signal(bool)
    status = QtCore.Signal(str)


class CfdQThread(QThread):
    """ Wrapper for QThread for use by CfdThread class """
    def __init__(self):
        super(CfdQThread, self).__init__()
        self.signals = CfdQThreadSignals()
        self.function = None
        self.args = ()
        self.kwargs = {}

    def run(self):
        if self.function is None:
            raise Exception("No function set")
        try:
            self.function(self.emitStatus, *self.args, **self.kwargs)
        except Exception as e:
            self.signals.error.emit(str(e))
            self.signals.finished.emit(False)
            raise
        self.signals.finished.emit(True)

    def emitStatus(self, msg):
        self.signals.status.emit(msg)
