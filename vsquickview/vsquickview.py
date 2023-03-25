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
import os
import numpy as np
from pathlib import Path
from PyQt5.QtCore import QObject, QMutex, pyqtProperty, pyqtSignal, pyqtSlot, Qt, QRunnable, QThread, QThreadPool
from PyQt5.QtGui import QGuiApplication, QImage
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtQuick import QQuickImageProvider
import typing
from typing import Optional, Union
import vapoursynth as vs
from vapoursynth import core


from .colourbars import ColourBars

Clips = [None] * 10
Names = [None] * 10

def loadImage(clip):
    if clip.format.bits_per_sample != 8:
        clip = core.fmtc.bitdepth(clip, bits=8)

    frame = clip.get_frame(0)
    r = np.array(frame[0], dtype=np.uint8).reshape((clip.height, clip.width))
    g = np.array(frame[1], dtype=np.uint8).reshape((clip.height, clip.width))
    b = np.array(frame[2], dtype=np.uint8).reshape((clip.height, clip.width))
    rgb = np.stack((r, g, b))
    rgb = np.moveaxis(rgb, 0, -1)

    return QImage(rgb.tobytes(), clip.width, clip.height, QImage.Format.Format_RGB888).copy()
    
ColourBarsCaches = {}
ColourBarsCaches[0] = loadImage(ColourBars)

Caches = [{}] * 10
CachesLocks = []
for _ in range(10):
    CachesLocks.append(QMutex())
CachesThreadPools = []
for _ in range(10):
    item = QThreadPool()
    item.setMaxThreadCount(1)
    CachesThreadPools.append(item)
CachesThreadPoolLocks = []
for _ in range(10):
    CachesThreadPoolLocks.append(QMutex())

def getImage(index, frame):
    if Clips[index] and 0 <= frame < Clips[index].num_frames:
        CachesLocks[index].lock()
        if frame not in Caches[index]:
            img = Caches[index][frame] = loadImage(Clips[index][frame])
        else:
            img = Caches[index][frame]
            del Caches[index][frame]
            Caches[index][frame] = img
        CachesLocks[index].unlock()
    else:
        img = ColourBarsCaches[0]

    return img

class CacheFrames(QRunnable):
    def __init__(self, index, frame, renew_index):
        super(CacheFrames, self).__init__()
        self.index = index
        self.frame = frame
        self.renew_index = renew_index
    @pyqtSlot()
    def run(self):
        if Clips[self.index] and 0 <= self.frame < Clips[self.index].num_frames:
            CachesLocks[self.index].lock()
            if self.frame not in Caches[self.index]:
                CachesLocks[self.index].unlock()
                img = loadImage(Clips[self.index][self.frame])
            else:
                img = Caches[self.index][self.frame]
                CachesLocks[self.index].unlock()

            CachesLocks[self.index].lock()
            if self.renew_index:
                del Caches[self.index][self.frame]
            Caches[self.index][self.frame] = img
            CachesLocks[self.index].unlock()
def cacheFrames(index, frame, renew_index):
    CachesThreadPoolLocks[index].lock()
    if renew_index:
        CachesThreadPools[index].start(CacheFrames(index, frame, True), priority=QThread.Priority.HighPriority)
    else:
        CachesThreadPools[index].start(CacheFrames(index, frame, False), priority=QThread.Priority.NormalPriority)
    CachesThreadPoolLocks[index].unlock()

class FreeOldCaches(QRunnable):
    def __init__(self, index):
        super(FreeOldCaches, self).__init__()
        self.index = index
    @pyqtSlot()
    def run(self):
        CachesLocks[self.index].lock()
        frame_list = list(Caches[self.index])
        for jndex in range(0, len(frame_list) - 18):
            del Caches[self.index][frame_list[jndex]]
        CachesLocks[self.index].unlock()
def freeOldCaches(index):
    CachesThreadPoolLocks[index].lock()
    CachesThreadPools[index].start(FreeOldCaches(index), priority=QThread.Priority.IdlePriority)
    CachesThreadPoolLocks[index].unlock()

def cancelAllAndClearCache(index):
    CachesThreadPoolLocks[index].lock()
    CachesThreadPools[index].clear()
    CachesThreadPools[index].waitForDone()
    CachesLocks[index].lock()
    Caches[index] = {}
    CachesLocks[index].unlock()
    CachesThreadPoolLocks[index].unlock()


class Backend(QObject):
    def __init__(self):
        QObject.__init__(self)

        self.indexChanged.connect(self.imageChanged)
        self.frameChanged.connect(self.imageChanged)

        self.indexChanged.connect(self.updateName)

        self.imageChanged.connect(self.cacheFrames)
        self.imageChanged.connect(self.freeOldCaches)
        self.cacheUpdateTrigger.connect(self.cacheFrames)
        self.cacheUpdateTrigger.connect(self.freeOldCaches)

    cacheUpdateTrigger = pyqtSignal()

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
        if Clips[self.index] and 0 <= self.frame < Clips[self.index].num_frames:
            self.name = Names[self.index]
        else:
            self.name = ""

    @pyqtSlot()
    def prevIndex(self):
        for i in range(self.index - 1, -1, -1):
            if Clips[i] and 0 <= self.frame < Clips[i].num_frames:
                self.index = i
                return
    @pyqtSlot()
    def nextIndex(self):
        for i in range(self.index + 1, 10):
            if Clips[i] and 0 <= self.frame < Clips[i].num_frames:
                self.index = i
                return
    @pyqtSlot()
    def cycleIndex(self):
        for i in itertools.chain(range(self.index + 1, 10), range(self.index)):
            if Clips[i] and 0 <= self.frame < Clips[i].num_frames:
                self.index = i
                return
    @pyqtSlot()
    def cycleIndexBackwards(self):
        for i in itertools.chain(range(self.index - 1, -1, -1), range(10 - 1, self.index, -1)):
            if Clips[i] and 0 <= self.frame < Clips[i].num_frames:
                self.index = i
                return
    @pyqtSlot(int)
    def switchIndex(self, index):
        self.index = index

    @pyqtSlot()
    def prevFrame(self):
        if Clips[self.index] and 0 <= self.frame < Clips[self.index].num_frames:
            if self.frame > 0:
                self.frame = self.frame - 1
            elif self.frame < 0:
                self.frame = 0
        else:
            self.frame = self.frame - 1
    @pyqtSlot()
    def nextFrame(self):
        if Clips[self.index] and 0 <= self.frame < Clips[self.index].num_frames:
            if self.frame < Clips[self.index].num_frames - 1:
                self.frame = self.frame + 1
            elif self.frame > Clips[self.index].num_frames - 1:
                self.frame = Clips[self.index].num_frames - 1
        else:
            self.frame = self.frame + 1
    @pyqtSlot(int)
    def switchFrame(self, frame):
        self.frame = frame

    @pyqtSlot()
    def cacheFrames(self):
        cacheFrames(self.index, self.frame, True)
        for index in range(10):
            cacheFrames(index, self.frame, False)
        for frame in [self.frame + 1, self.frame - 1, self.frame + 2, self.frame - 2]:
            cacheFrames(self.index, frame, False)

    @pyqtSlot()
    def freeOldCaches(self):
        freeOldCaches(self.index)

class ImageProvider(QQuickImageProvider):
    def __init__(self):
        super(ImageProvider, self).__init__(QQuickImageProvider.ImageType.Image)

    def requestImage(self, id, requestedSize):
        img = getImage(backend.index, backend.frame)
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


def View(clip: vs.VideoNode, index: int, name: Optional[str]=None):
    assert(type(index) == int and 0 <= index < 10)
    assert(isinstance(name, typing.get_args(Optional[str])))

    clip = clip[:]
    if clip.format.color_family == vs.YUV:
        clip = core.fmtc.resample(clip, css="444", kernel="spline64")
        clip = core.fmtc.matrix(clip, mat="709", col_fam=vs.RGB)
    if clip.format.bits_per_sample != 8:
        clip = core.fmtc.bitdepth(clip, bits=8)

    Clips[index] = clip
    Names[index] = name
    cancelAllAndClearCache(index)

    if backend.index == index:
        backend.indexChanged.emit()
    else:
        backend.cacheUpdateTrigger.emit()

def RemoveView(clip: Union[vs.VideoNode, int, None]=None, index: Optional[int]=None):
    if not index:
        index = clip
    assert(type(index) == int and 0 <= index < 10)

    Clips[index] = None
    Names[index] = None
    cancelAllAndClearCache(index)

    if backend.index == index:
        backend.indexChanged.emit()
    else:
        backend.cacheUpdateTrigger.emit()

def SetFrame(clip: Union[vs.VideoNode, int, None]=None, frame: Optional[int]=None):
    if not frame:
        frame = clip
    assert(type(frame) == int)

    backend.switchFrame(frame)
def SetIndex(clip: Union[vs.VideoNode, int, None]=None, index: Optional[int]=None):
    if not index:
        index = clip
    assert(type(index) == int and 0 <= index < 10)

    backend.switchIndex(index)

def Show(clip: Optional[vs.VideoNode]=None):
    window_control.show.emit()

def Hide(clip: Optional[vs.VideoNode]=None):
    window_control.hide.emit()
