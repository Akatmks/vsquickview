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
import numpy as np
import os
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QGuiApplication, QImage
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtQuick import QQuickImageProvider
import typing
import vapoursynth as vs
from vapoursynth import core


Clips = [None] * 10
Names = [None] * 10
Caches = [{ 1: {}, 2: {}, 3: {}, 4: {} }] * 10
ColourBars = QImage(Path(__file__).with_name("SMPTE_Color_Bars.svg.png").as_posix())
ColourBars.convertToFormat(QImage.Format.Format_RGB888)

class Backend(QObject):
    def __init__(self):
        QObject.__init__(self)

        self.indexChanged.connect(self.imageChanged)
        self.frameChanged.connect(self.imageChanged)
        self.scaleChanged.connect(self.imageChanged)
        self.imageChanged.connect(self.updateName)

    _index = 0
    def index_(self):
        return self._index
    def setIndex(self, index):
        if self._index != index:
            self._index = index
            self.indexChanged.emit()
    indexChanged = pyqtSignal()
    index = pyqtProperty(int, index_, setIndex, notify=indexChanged)

    _frame = 0
    def frame_(self):
        return self._frame
    def setFrame(self, frame):
        if self._frame != frame:
            self._frame = frame
            self.frameChanged.emit()
    frameChanged = pyqtSignal()
    frame = pyqtProperty(int, frame_, setFrame, notify=frameChanged)

    _scale = 1
    def scale_(self):
        return self._scale
    def setScale(self, scale):
        if self._scale != scale:
            self._scale = scale
            self.scaleChanged.emit()
    scaleChanged = pyqtSignal()
    scale = pyqtProperty(int, scale_, setScale, notify=scaleChanged)

    _name = ""
    def name_(self):
        return self._name
    def setName(self, name):
        if self._name != name:
            self._name = name
            self.nameChanged.emit()
    nameChanged = pyqtSignal()
    name = pyqtProperty(str, name_, setName, notify=nameChanged)
    
    imageChanged = pyqtSignal()
    @pyqtSlot()
    def updateName(self):
        self.name = Names[self.index]

    @pyqtSlot()
    def prevIndex(self):
        for i in itertools.chain(range(self.index - 1, -1, -1), range(10, self.index, -1)):
            if Clips[i]:
                self.index = i
                return
    @pyqtSlot()
    def nextIndex(self):
        for i in itertools.chain(range(self.index + 1, 10), range(self.index)):
            if Clips[i]:
                self.index = i
                return
    @pyqtSlot(int)
    def switchIndex(self, index):
        self.index = index

    @pyqtSlot()
    def prevFrame(self):
        if self.frame > 0:
            self.frame = self.frame - 1
        elif self.frame < 0:
            self.frame = 0
    @pyqtSlot()
    def nextFrame(self):
        if self.frame < Clips[self.index].num_frames - 1:
            self.frame = self.frame + 1
        elif self.frame > Clips[self.index].num_frames - 1:
            self.frame = Clips[self.index].num_frames - 1
    @pyqtSlot(int)
    def switchFrame(self, frame):
        self.frame = frame

    @pyqtSlot(result=float)
    def moreScale(self):
        if self.scale == 1:
            self.scale = 2
            return 2/1
        elif self.scale == 2:
            self.scale = 3
            return 3/2
        elif self.scale == 3:
            self.scale = 4
            return 4/3
        elif self.scale == 4:
            return 4/4
    @pyqtSlot(result=float)
    def lessScale(self):
        if self.scale == 1:
            return 1/1
        elif self.scale == 2:
            self.scale = 1
            return 1/2
        elif self.scale == 3:
            self.scale = 2
            return 2/3
        elif self.scale == 4:
            self.scale = 3
            return 3/4

class ImageProvider(QQuickImageProvider):
    def __init__(self):
        super(ImageProvider, self).__init__(QQuickImageProvider.ImageType.Image)

    def requestImage(self, id, requestedSize):
        if Clips[backend.index] and 0 <= backend.frame < Clips[backend.index].num_frames:
            if backend.frame in Caches[backend.index][backend.scale]:
                return Caches[backend.index][backend.scale][backend.frame], Caches[backend.index][backend.scale][backend.frame].size()
            else:
                clip = Clips[backend.index]
                if backend.scale != 1:
                    clip = core.fmtc.resample(clip, scale=backend.scale, kernel="point")
                    clip = core.fmtc.bitdepth(clip, bits=8)
                frame = clip.get_frame(backend.frame)
                r = np.array(frame[0], dtype=np.uint8).reshape((clip.height, clip.width))
                g = np.array(frame[1], dtype=np.uint8).reshape((clip.height, clip.width))
                b = np.array(frame[2], dtype=np.uint8).reshape((clip.height, clip.width))
                rgb = np.stack((r, g, b))
                rgb = np.moveaxis(rgb, 0, -1)

                img = QImage(rgb.tobytes(), clip.width, clip.height, QImage.Format.Format_RGB888).copy()
                Caches[backend.index][backend.scale][backend.frame] = img

                return img, img.size()
        else:
            img = ColourBars
            if backend.scale != 1:
                ptr = img.bits()
                ptr.setsize(img.height() * img.width() * 3)
                rgb = np.frombuffer(ptr, dtype=np.uint8).reshape((img.height(), img.width(), 3))
                rgb = np.repeat(rgb, backend.scale, axis=0)
                rgb = np.repeat(rgb, backend.scale, axis=1)
                img = QImage(rgb.tobytes(), rgb.shape[0], rgb.shape[1], QImage.Format.Format_RGB888).copy()

            return img, img.size()


class WindowControl(QObject):
    def __init__(self):
        QObject.__init__(self)

    show = pyqtSignal()
    hide = pyqtSignal()


os.environ["QT_QUICK_CONTROLS_STYLE"] = "Material"
os.environ["QT_QUICK_CONTROLS_MATERIAL_THEME"] = "Dark"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
QGuiApplication.setAttribute(Qt.AA_EnableHighDpiScaling, 0)
QGuiApplication.setAttribute(Qt.AA_UseOpenGLES)

if not (app := QGuiApplication.instance()):
    app = QGuiApplication([])
engine = QQmlApplicationEngine()

image_provider = ImageProvider()
engine.addImageProvider("backend", ImageProvider())
backend = Backend()
engine.rootContext().setContextProperty("backend", backend)
window_control = WindowControl()
engine.rootContext().setContextProperty("windowcontrol", window_control)

qml_file = Path(__file__).with_name("vsquickview.qml").as_posix()
engine.load(qml_file)


def view(index: int, clip, name: typing.Optional[str]=None):
    clip = clip[:]
    if clip.format.color_family == vs.YUV:
        clip = core.fmtc.resample(clip, css="444", kernel="spline64")
        clip = core.fmtc.matrix(clip, mat="709", col_fam=vs.RGB)
    if clip.format.bits_per_sample != 8:
        clip = core.fmtc.bitdepth(clip, bits=8)

    Clips[index] = clip
    Names[index] = name
    Caches[index] = { 1: {}, 2: {}, 3: {}, 4: {} }

    if backend.index == index:
        backend.imageChanged.emit()

def removeView(index: int):
    Clips[index] = None
    Names[index] = None
    Caches[index] = { 1: {}, 2: {}, 3: {}, 4: {} }

    if backend.index == index:
        backend.imageChanged.emit()

def show():
    window_control.show.emit()

def hide():
    window_control.hide.emit()
