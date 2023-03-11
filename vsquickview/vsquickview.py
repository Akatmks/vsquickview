# vsquickview
# Copyright (c) Akatsumekusa and contributors

# ---------------------------------------------------------------------
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ---------------------------------------------------------------------

import itertools
import typing
import numpy as np
from pathlib import Path
from PySide6.QtCore import Property, QObject, Qt, Signal, Slot
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider


Clips = [None] * 10
Names = [None] * 10
ColourBars = QImage(Path(__file__).with_name("SMPTE_Color_Bars.svg.png"))

class Backend(QObject):
    def __init__(self):
        QObject.__init__(self)

        self.indexChanged.connect(self.imageChanged)
        self.frameChanged.connect(self.imageChanged)
        self.imageChanged.connect(self.updateName)

    _index = 0
    def index_(self):
        return self._index
    def setIndex(self, index):
        if self._index != index:
            self._index = index
            self.indexChanged.emit()
    indexChanged = Signal()
    index = Property(int, index_, setIndex, notify=indexChanged)

    _frame = 0
    def frame_(self):
        return self._frame
    def setFrame(self, frame):
        if self._frame != frame:
            self._frame = frame
            self.frameChanged.emit()
    frameChanged = Signal()
    frame = Property(int, frame_, setFrame, notify=frameChanged)

    _name = ""
    def name_(self):
        return self._name
    def setName(self, name):
        if self._name != name:
            self._name = name
            self.nameChanged.emit()
    nameChanged = Signal()
    name = Property(str, name_, setName, notify=nameChanged)
    
    imageChanged = Signal()
    @Slot()
    def updateName(self):
        self.name = Names[self.index]

    @Slot()
    def prevIndex(self):
        for i in itertools.chain(range(self.index - 1, -1, -1), range(10, self.index, -1)):
            if Clips[i]:
                self.index = i
                return
    @Slot()
    def nextIndex(self):
        for i in itertools.chain(range(self.index + 1, 10), range(self.index)):
            if Clips[i]:
                self.index = i
                return
    @Slot()
    def switchIndex(self, index):
        self.index = index

    @Slot()
    def prevFrame(self):
        if self.frame > 0:
            self.frame = self.frame - 1
        elif self.frame < 0:
            self.frame = 0
    @Slot()
    def nextFrame(self):
        if self.frame < Clips[self.index].num_frames - 1:
            self.frame = self.frame + 1
        elif self.frame > Clips[self.index].num_frames - 1:
            self.frame = Clips[self.index].num_frames - 1
    @Slot()
    def switchFrame(self, frame):
        self.frame = frame

class ImageProvider(QQuickImageProvider):
    def __init__(self):
        super(ImageProvider, self).__init__(QQuickImageProvider.Image)

    def requestImage(self, id, size, requestedSize):
        if Clips[backend.index] and 0 <= backend.frame < Clips[backend.index].num_frames:
            frame = Clips[backend.index].get_frame(backend.frame)
            r = np.array(frame[0], dtype=np.uint8).reshape((clip.height, clip.width))
            g = np.array(frame[1], dtype=np.uint8).reshape((clip.height, clip.width))
            b = np.array(frame[2], dtype=np.uint8).reshape((clip.height, clip.width))
            rgb = np.stack((r, g, b))
            rgb = np.moveaxis(rgb, 0, -1)

            return QImage(rgb.data, clip.width, clip.height, QImage.Format_RGB888)
        else:
            return ColourBars


QGuiApplication.setAttribute(Qt.AA_DisableHighDpiScaling)

app = QGuiApplication([])
engine = QQmlApplicationEngine()

image_provider = ImageProvider()
engine.addImageProvider("backend", ImageProvider())
backend = Backend()
engine.rootContext().setContextProperty("backend", backend)

qml_file = Path(__file__).with_name("vsquickview.qml")
engine.load(qml_file)


def view(index: int, clip, name: typing.Optional[str]=None):
    clip = clip[:]
    if clip.format.color_family == vs.YUV:
        clip.fmtc.resample(css="444", kernel="spline64")
        clip.fmtc.matrix(mat="RGB", col_fam=vs.RGB)
    if clip.format.bits_per_sample != 8:
        clip.fmtc.bitdepth(bits=8)

    Clips[index] = clip
    Names[index] = name

    if backend.index == index:
        backend.imageChanged.emit()

def removeView(index: int):
    Clips[index] = None
    Names[index] = None

    if backend.index == index:
        backend.imageChanged.emit()

def show():
    pass

def hide():
    pass