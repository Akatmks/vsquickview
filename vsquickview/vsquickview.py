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
from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, Qt, QRunnable, QThreadPool
from PyQt5.QtGui import QGuiApplication, QImage
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtQuick import QQuickImageProvider
import typing
import vapoursynth as vs
from vapoursynth import core


Clips = [None] * 10
Names = [None] * 10
Caches = [{ 1: {}, 2: {}, 3: {}, 4: {} }] * 10

pattern_1 = core.std.StackHorizontal([core.std.BlankClip(None, 240, 630, color=[414, 414, 414], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None, 206, 630, color=[721, 721, 721], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None, 206, 630, color=[721, 721,  64], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None, 206, 630, color=[ 64, 721, 721], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None, 204, 630, color=[ 64, 721,  64], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None, 206, 630, color=[721,  64, 721], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None, 206, 630, color=[721,  64,  64], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None, 206, 630, color=[ 64,  64, 721], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None, 240, 630, color=[414, 414, 414], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001)])
pattern_2 = core.std.StackHorizontal([core.std.BlankClip(None, 240,  90, color=[ 64, 940, 940], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None, 206,  90, color=[721, 721, 721], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None, 206,  90, color=[707, 717, 279], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None, 206,  90, color=[465, 698, 716], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None, 204,  90, color=[441, 694, 259], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None, 206,  90, color=[602, 250, 691], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None, 206,  90, color=[584, 237, 148], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None, 206,  90, color=[201, 134, 686], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None, 240,  90, color=[ 64,  64, 940], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001)])
ramp = core.std.BlankClip(None, (1 + 498 + 516), 90, format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001)
ramp_frame = ramp.get_frame(0).copy()
for plane in range(3):
    for x in range(ramp.width):
        for y in range(ramp.height):
            ramp_frame[plane][y, x] = round((1019 - 4) / (1 + 498 + 516) * x) + 4
ramp = core.std.ModifyFrame(ramp, ramp, lambda n, f: ramp_frame)
pattern_3 = core.std.StackHorizontal([core.std.BlankClip(None, 240,  90, color=[940, 940,  64], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None, 221,  90, color=[  4,   4,   4], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      ramp,
                                      core.std.BlankClip(None, 204,  90, color=[1019, 1019, 1019], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None, 240,  90, color=[940,  64,  64], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001)])
vertical_stripe_ba = core.std.StackHorizontal([(vertical_stripe_b := core.std.BlankClip(None,   1, 135, color=[940, 940, 940], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001)), 
                                               (vertical_stripe_a := core.std.BlankClip(None,   1, 135, color=[940,  64, 940], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001))])
vertical_stripe_ba_2 = core.std.StackHorizontal([vertical_stripe_ba  , vertical_stripe_ba  ])
vertical_stripe_ba_3 = core.std.StackHorizontal([vertical_stripe_ba_2, vertical_stripe_ba_2])
vertical_stripe_ba_4 = core.std.StackHorizontal([vertical_stripe_ba_3, vertical_stripe_ba_3])
vertical_stripe_ba_5 = core.std.StackHorizontal([vertical_stripe_ba_4, vertical_stripe_ba_4])
vertical_stripe_ba_6 = core.std.StackHorizontal([vertical_stripe_ba_5, vertical_stripe_ba_5])
vertical_stripe = core.std.StackHorizontal([vertical_stripe_ba_6,
                                            vertical_stripe_ba_5,
                                            vertical_stripe_ba_2])
block = core.std.StackVertical([core.std.BlankClip(None,  40,  68, color=[940, 502, 940], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                core.std.BlankClip(None,  40,  67, color=[792, 502, 792], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001)])
horizontal_stripe_ba = core.std.StackVertical([(horizontal_stripe_b := core.std.BlankClip(None, 100,   1, color=[940, 940, 940], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001)),
                                               (horizontal_stripe_a := core.std.BlankClip(None, 100,   1, color=[940,  64, 940], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001))])
horizontal_stripe_ba_2 = core.std.StackVertical([horizontal_stripe_ba  , horizontal_stripe_ba  ])
horizontal_stripe_ba_3 = core.std.StackVertical([horizontal_stripe_ba_2, horizontal_stripe_ba_2])
horizontal_stripe_ba_4 = core.std.StackVertical([horizontal_stripe_ba_3, horizontal_stripe_ba_3])
horizontal_stripe_ba_5 = core.std.StackVertical([horizontal_stripe_ba_4, horizontal_stripe_ba_4])
horizontal_stripe_ba_6 = core.std.StackVertical([horizontal_stripe_ba_5, horizontal_stripe_ba_5])
horizontal_stripe_ba_7 = core.std.StackVertical([horizontal_stripe_ba_6, horizontal_stripe_ba_6])
horizontal_stripe = core.std.StackVertical([horizontal_stripe_ba_7,
                                            horizontal_stripe_ba_2,
                                            horizontal_stripe_ba,
                                            horizontal_stripe_b])
cyclone = core.std.BlankClip(None,  10,   9, color=[940, 940, 940], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001)
cyclone_frame = cyclone.get_frame(0).copy()
if True:
    x = 9
    y = 8
    cyclone_frame[0][y, x] = 64
    cyclone_frame[1][y, x] = 64
    cyclone_frame[2][y, x] = 64
    route = [[0, -1, 0, -8], [-1, 0, -8, 0], [0, 1, 0, 7], [1, 0, 6, 0], [0, -1, 0, -5], [-1, 0, -4, 0], [0, 1, 0, 3], [1, 0, 2, 0], [0, -1, 0, -1]]
    while route:
        step = route.pop(0)
        while step[2] or step[3]:
            x += step[0]
            y += step[1]
            cyclone_frame[0][y, x] = 64
            cyclone_frame[1][y, x] = 64
            cyclone_frame[2][y, x] = 64

            step[2] -= step[0]
            step[3] -= step[1]
cyclone = core.std.ModifyFrame(cyclone, cyclone, lambda n, f: cyclone_frame)
vertical_cyclone = core.std.StackVertical([cyclone] * 15)
cyclone_pattern = core.std.StackHorizontal([vertical_cyclone] * 24)
full_hd_pattern = core.std.StackVertical([core.std.StackHorizontal([vertical_stripe,
                                                                    block,
                                                                    horizontal_stripe]),
                                          cyclone_pattern])
pattern_4 = core.std.StackHorizontal([core.std.BlankClip(None, 240, 270, color=[414, 414, 414], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None, 282, 270, color=[ 64,  64,  64], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None, 438, 270, color=[940, 940, 940], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None, 232, 270, color=[ 64,  64,  64], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None,  68, 270, color=[ 48,  48,  48], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None,  70, 270, color=[ 64,  64,  64], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None,  68, 270, color=[ 80,  80,  80], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      core.std.BlankClip(None, 282, 270, color=[ 64,  64,  64], format=vs.RGB30, length=1, fpsnum=24000, fpsden=1001),
                                      full_hd_pattern])
ColourBars = core.std.StackVertical([pattern_1, pattern_2, pattern_3, pattern_4])
ColourBarsCaches = { 1: {}, 2: {}, 3: {}, 4: {} }


def loadImage(clip, scale):
    if scale != 1:
        clip = core.fmtc.resample(clip, scale=scale, kernel="point")
    if clip.format.bits_per_sample != 8:
        clip = core.fmtc.bitdepth(clip, bits=8)

    frame = clip.get_frame(0)
    r = np.array(frame[0], dtype=np.uint8).reshape((clip.height, clip.width))
    g = np.array(frame[1], dtype=np.uint8).reshape((clip.height, clip.width))
    b = np.array(frame[2], dtype=np.uint8).reshape((clip.height, clip.width))
    rgb = np.stack((r, g, b))
    rgb = np.moveaxis(rgb, 0, -1)

    return QImage(rgb.tobytes(), clip.width, clip.height, QImage.Format.Format_RGB888).copy()

class CacheImage(QRunnable):
    def __init__(self, clip, cache, frame):
        super(CacheImage, self).__init__()

        self.clip = clip
        self.cache = cache
        self.frame = frame

    @pyqtSlot()
    def run(self):
        for scale in range(1, 5):
            if self.frame not in self.cache[scale] and \
               0 <= self.frame < self.clip.num_frames:
                    self.cache[scale][self.frame] = loadImage(self.clip[self.frame], scale)

CacheImageThreadPool = QThreadPool()

if True:
    CacheImageThreadPool.start(CacheImage(ColourBars, ColourBarsCaches, 0))


class Backend(QObject):
    def __init__(self):
        QObject.__init__(self)

        self.indexChanged.connect(self.imageChanged)
        self.frameChanged.connect(self.imageChanged)
        self.scaleChanged.connect(self.imageChanged)
        self.imageChanged.connect(self.updateName)

        self.frameChanged.connect(self.cacheImage)

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
        if Clips[self.index] and 0 <= self.frame < Clips[self.index].num_frames:
            self.name = Names[self.index]
        else:
            self.name = ""

    @pyqtSlot()
    def prevIndex(self):
        for i in itertools.chain(range(self.index - 1, -1, -1), range(10, self.index, -1)):
            if Clips[i] and 0 <= self.frame < Clips[i].num_frames:
                self.index = i
                return
    @pyqtSlot()
    def nextIndex(self):
        for i in itertools.chain(range(self.index + 1, 10), range(self.index)):
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

    @pyqtSlot()
    def cacheImage(self):
        for index in range(10):
            if Clips[index]:
                CacheImageThreadPool.start(CacheImage(Clips[index], Caches[index], backend.frame))


class ImageProvider(QQuickImageProvider):
    def __init__(self):
        super(ImageProvider, self).__init__(QQuickImageProvider.ImageType.Image)

    def requestImage(self, id, requestedSize):
        if Clips[backend.index] and 0 <= backend.frame < Clips[backend.index].num_frames:
            if backend.frame in Caches[backend.index][backend.scale]:
                img = Caches[backend.index][backend.scale][backend.frame]
            else:
                img = loadImage(Clips[backend.index][backend.frame], backend.scale)
        else:
            if 0 in ColourBarsCaches[backend.scale]:
                img = ColourBarsCaches[backend.scale][0]
            else:
                img = loadImage(ColourBars[0], backend.scale)

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

    Clips[index] = clip
    Names[index] = name
    Caches[index] = { 1: {}, 2: {}, 3: {}, 4: {} }

    if backend.index == index:
        backend.imageChanged.emit()

    backend.cacheImage()

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
