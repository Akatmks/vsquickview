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

import bisect
import ctypes
import itertools
import os
import numpy as np
from pathlib import Path
from PySide6.QtCore import QObject, QMutex, Property, QReadWriteLock, QRunnable, Signal, Slot, QStandardPaths, QThreadPool
from PySide6.QtGui import QColorSpace, QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider
import traceback
import typing
from typing import Optional, Union
import vapoursynth as vs
from vapoursynth import core


Clips = [None] * 10
# [(color_space_in, color_space)]
ClipColorSpaces = [None] * 10
Names = [None] * 10


from .colourbars import ColourBars

def loadImage(clip, clip_color_space, frame):
    if clip.format.color_family == vs.RGB:
        if clip.format.bits_per_sample == 16:
            frame = clip.get_frame(frame)
            r = np.array(frame[0], dtype=np.uint16)
            g = np.array(frame[1], dtype=np.uint16)
            b = np.array(frame[2], dtype=np.uint16)
            a = np.array([np.iinfo(np.uint16).max], dtype=np.uint16)
            a = np.broadcast_to(a, (frame.height * frame.width, 1))
            image = np.hstack((r.reshape((-1, 1)), g.reshape((-1, 1)), b.reshape((-1, 1)), a)).reshape((frame.height, frame.width, 4))
            qimage = QImage(image.data, frame.width, frame.height, image.strides[0], QImage.Format.Format_RGBX64)

        elif clip.format.bits_per_sample == 8:
            frame = clip.get_frame(frame)
            r = np.array(frame[0], dtype=np.uint8)
            g = np.array(frame[1], dtype=np.uint8)
            b = np.array(frame[2], dtype=np.uint8)
            image = np.hstack((r.reshape((-1, 1)), g.reshape((-1, 1)), b.reshape((-1, 1)))).reshape((frame.height, frame.width, 3))
            qimage = QImage(image.data, frame.width, frame.height, image.strides[0], QImage.Format.Format_RGB888)

    elif clip.format.color_family == vs.GRAY:
        if clip.format.bits_per_sample == 16:
            frame = clip.get_frame(frame)
            ptr = ctypes.cast(frame.get_read_ptr(0), ctypes.POINTER(ctypes.c_uint16 * (frame.height * frame.get_stride(0))))
            qimage = QImage(ptr.contents, frame.width, frame.height, frame.get_stride(0), QImage.Format.Format_Grayscale16).copy()

        elif clip.format.bits_per_sample == 8:
            frame = clip.get_frame(frame)
            ptr = ctypes.cast(frame.get_read_ptr(0), ctypes.POINTER(ctypes.c_uint8 * (frame.height * frame.get_stride(0))))
            qimage = QImage(ptr.contents, frame.width, frame.height, frame.get_stride(0), QImage.Format.Format_Grayscale8).copy()

    qimage.setColorSpace(clip_color_space[0])
    if clip_color_space[1] != clip_color_space[0]:
        qimage.convertToColorSpace(clip_color_space[1])

    return qimage

ColourBarsCaches = {}
ColourBarsCaches[0] = loadImage(ColourBars, (QColorSpace(QColorSpace.SRgb), QColorSpace(QColorSpace.SRgb)), 0)


# The image provider in autoclip is unsynced.
# When frontend triggers a new frame, the request is sent into priority
# ThreadPool. When a task in the ThreadPool is completed, it checks the linked
# list to see if the result is still needed. If so, it set the QImage to
# Frame, remove anything later than the frame in linked list and trigger a
# rerender
Image = ColourBarsCaches[0]
ImageLock = QMutex()
# { "index": 0, "frame": 0, "prev": None }
ImagesPending = None
ImagesPendingCount = 0
ImagesPendingLock = QMutex()

class ImageProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image)

    def requestImage(self, id, size, requestedSize):
        ImageLock.lock()
        img = Image
        ImageLock.unlock()

        return img


Caches = [{}] * 10
CacheHeads = [0] * 10
CacheLocks = []
for _ in range(10):
    CacheLocks.append(QReadWriteLock())
CacheMinimumSize = 10
CacheCleaningFrequency = 5
    
# Loading frames to be displayed is using tryStart()
# When ThreadPool is full, all even frame loads are 5 and all odd frame
# loads are 4
# Preloading frames is 2
# Cache cleaning is runned in reserved thread
CacheThreadPool = QThreadPool()
CacheThreadPool.setMaxThreadCount(2)
# This lock is used when adding runnables to CacheThreadPool
# vsqv.View() and vsqv.RemoveView() uses the write lock,
# Backend.updateImage() and LoadImageOfNearbyIndex() uses the read lock
CacheThreadPoolLock = QReadWriteLock()

LoadImageOfNearbyIndexThreadPool = QThreadPool()
LoadImageOfNearbyIndexThreadPool.setMaxThreadCount(1)


class RequestImage(QRunnable):
    def __init__(self, index, frame, do_display=False):
        super().__init__()

        self.index = index
        self.frame = frame
        self.do_display = do_display

    def run(self):
        if Clips[self.index] and \
           0 <= self.frame < Clips[self.index].num_frames:
            if self.do_display:
                if CacheLocks[self.index].tryLockForRead() and \
                   self.frame in Caches[self.index]:
                    img = Caches[self.index][self.frame]
                    CacheLocks[self.index].unlock()
                    self.update_Image(img)
                else:
                    CacheLocks[self.index].unlock()
                    img = loadImage(Clips[self.index], ClipColorSpaces[self.index], self.frame)
                    self.update_Image(img)
                    self.update_Cache(img)
                
            else:
                CacheLocks[self.index].lockForRead()
                if self.frame in Caches[self.index]:
                    CacheLocks[self.index].unlock()
                else:
                    CacheLocks[self.index].unlock()
                    img = loadImage(Clips[self.index], ClipColorSpaces[self.index], self.frame)
                    self.update_Cache(img)
        else:
            if self.do_display:
                self.update_Image(ColourBarsCaches[0])
                
    def update_Image(self, img):
        global Image
        
        ImagesPendingLock.lock()
        head = ImagesPending
        while head:
            if head["index"] == self.index and head["frame"] == self.frame:
                ImageLock.lock()
                Image = img
                ImageLock.unlock()
                backend.imageReady.emit()
                head["prev"] = None
                break

            head = head["prev"]
        ImagesPendingLock.unlock()
        
    def update_Cache(self, img):
        head = None
        
        CacheLocks[self.index].lockForWrite()
        if self.frame in Caches[self.index]:
            del Caches[self.index][self.frame]
            Caches[self.index][self.frame] = img
        else:
            Caches[self.index][self.frame] = img
            head = CacheHeads[self.index] = CacheHeads[self.index] + 1
        CacheLocks[self.index].unlock()
        
        if head and head % CacheCleaningFrequency == 0:
            CacheLocks[self.index].lockForWrite()
            frame_list = list(Caches[self.index])
            for jndex in range(0, len(frame_list) - CacheMinimumSize):
                del Caches[self.index][frame_list[jndex]]
            CacheLocks[self.index].unlock()

class LoadImageOfNearbyIndex(QRunnable):
    def __init__(self, index, frame):
        super().__init__()

        self.index = index
        self.frame = frame
        
    def run(self):
        CacheThreadPool.waitForDone()
        ImagesPendingLock.lock()
        if ImagesPending["frame"] == self.frame:
            ImagesPendingLock.unlock()
            if CacheThreadPoolLock.tryLockForRead():
                for jndex in itertools.chain(range(self.index + 1, 10), range(self.index)):
                    if Clips[jndex]:
                        CacheThreadPool.start(RequestImage(jndex, self.frame, False), priority=2)
                        break
                CacheThreadPoolLock.unlock()
                
                CacheThreadPool.waitForDone()
                ImagesPendingLock.lock()
                if ImagesPending["frame"] == self.frame:
                    ImagesPendingLock.unlock()
                    if CacheThreadPoolLock.tryLockForRead():
                        for jndex in itertools.chain(range(self.index - 1, -1, -1), range(10 - 1, self.index, -1)):
                            if Clips[jndex]:
                                CacheThreadPool.start(RequestImage(jndex, self.frame, False), priority=2)
                                break
                        CacheThreadPoolLock.unlock()
                else:
                    ImagesPendingLock.unlock()
        else:
            ImagesPendingLock.unlock()

class Backend(QObject):
    def __init__(self):
        QObject.__init__(self)

        self.indexChanged.connect(self.updateImage)
        self.frameChanged.connect(self.updateImage)

        self.indexChanged.connect(self.updateName)

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
    
    @Slot()
    def updateImage(self):
        global ImagesPending
        global ImagesPendingCount
        
        CacheThreadPoolLock.lockForRead()
        request_image = RequestImage(self.index, self.frame, True)
        ImagesPendingLock.lock()
        if not CacheThreadPool.tryStart(request_image):
            if ImagesPendingCount % 2 == 0:
                CacheThreadPool.clear()
                CacheThreadPool.start(request_image, priority=5)
            else:
                CacheThreadPool.start(request_image, priority=4)
        CacheThreadPoolLock.unlock()
        ImagesPending = { "index": self.index, "frame": self.frame, "prev": ImagesPending }
        ImagesPendingCount += 1
        ImagesPendingLock.unlock()
        LoadImageOfNearbyIndexThreadPool.clear()
        LoadImageOfNearbyIndexThreadPool.start(LoadImageOfNearbyIndex(self.index, self.frame))
    imageReady = Signal()
    
    _name = ""
    def name_(self):
        return self._name
    def setName(self, name):
        if self._name != name:
            self._name = name
            self.nameChanged.emit()
    nameChanged = Signal()
    name = Property(str, name_, setName, notify=nameChanged)

    preview_group = []
    previewGroupChanged = Signal()

    _devicePixelRatioOverride = 0.0
    def devicePixelRatioOverride_(self):
        return self._devicePixelRatioOverride
    def setDevicePixelRatioOverride(self, device_pixel_ratio_override):
        if self._devicePixelRatioOverride != device_pixel_ratio_override:
            self._devicePixelRatioOverride = device_pixel_ratio_override
            self.devicePixelRatioOverrideChanged.emit()
    devicePixelRatioOverrideChanged = Signal()
    devicePixelRatioOverride = Property(float, devicePixelRatioOverride_, setDevicePixelRatioOverride, notify=devicePixelRatioOverrideChanged)

    @Slot()
    def updateName(self):
        if Clips[self.index] and 0 <= self.frame < Clips[self.index].num_frames:
            self.name = Names[self.index]
        else:
            self.name = ""

    @Slot()
    def prevIndex(self):
        for i in range(self.index - 1, -1, -1):
            if Clips[i] and 0 <= self.frame < Clips[i].num_frames:
                self.index = i
                return
    @Slot()
    def nextIndex(self):
        for i in range(self.index + 1, 10):
            if Clips[i] and 0 <= self.frame < Clips[i].num_frames:
                self.index = i
                return
    @Slot()
    def cycleIndex(self):
        for i in itertools.chain(range(self.index + 1, 10), range(self.index)):
            if Clips[i] and 0 <= self.frame < Clips[i].num_frames:
                self.index = i
                return
    @Slot()
    def cycleIndexBackwards(self):
        for i in itertools.chain(range(self.index - 1, -1, -1), range(10 - 1, self.index, -1)):
            if Clips[i] and 0 <= self.frame < Clips[i].num_frames:
                self.index = i
                return
    @Slot(int)
    def switchIndex(self, index):
        self.index = index

    @Slot()
    def prevFrame(self):
        if Clips[self.index] and 0 <= self.frame < Clips[self.index].num_frames:
            if self.frame > 0:
                self.frame = self.frame - 1
            else:
                self.frame = 0
        else:
            self.frame = self.frame - 1
    @Slot()
    def prevTwelveFrames(self):
        if Clips[self.index] and 0 <= self.frame < Clips[self.index].num_frames:
            if self.frame >= 12:
                self.frame = self.frame - 12
            else:
                self.frame = 0
        else:
            self.frame = self.frame - 12
    @Slot()
    def prevPreviewGroupFrame(self):
        if self.preview_group:
            if self.frame > self.preview_group[0]:
                self.frame = self.preview_group[bisect.bisect_left(self.preview_group, self.frame) - 1]
        else:
            self.prevFrame()
    @Slot()
    def nextFrame(self):
        if Clips[self.index] and 0 <= self.frame < Clips[self.index].num_frames:
            if self.frame < Clips[self.index].num_frames - 1:
                self.frame = self.frame + 1
            else:
                self.frame = Clips[self.index].num_frames - 1
        else:
            self.frame = self.frame + 1
    @Slot()
    def nextTwelveFrames(self):
        if Clips[self.index] and 0 <= self.frame < Clips[self.index].num_frames:
            if self.frame < Clips[self.index].num_frames - 12:
                self.frame = self.frame + 12
            else:
                self.frame = Clips[self.index].num_frames - 1
        else:
            self.frame = self.frame + 12
    @Slot()
    def nextPreviewGroupFrame(self):
        if self.preview_group:
            if self.frame < self.preview_group[-1]:
                self.frame = self.preview_group[bisect.bisect_left(self.preview_group, self.frame + 1)]
        else:
            self.nextFrame()
    @Slot(int)
    def switchFrame(self, frame):
        self.frame = frame
    
    @Slot(result=bool)
    def frameInPreviewGroup(self):
        return self.frame in self.preview_group
    @Slot()
    def toggleFrameInPreviewGroup(self):
        if self.frame in self.preview_group:
            self.preview_group.remove(self.frame)
        else:
            self.preview_group.append(self.frame)
            self.preview_group.sort()
        self.previewGroupChanged.emit()

    _message = ""
    def message_(self):
        return self._message
    def setMessage(self, msg):
        if self._message != msg:
            self._message = msg
            if self._message != "":
                self.newMessage.emit()
            self.messageChanged.emit()
    messageChanged = Signal()
    message = Property(str, message_, setMessage, notify=messageChanged)
    newMessage = Signal()

    @Slot()
    def saveImage(self):
        index = self.index
        frame = self.frame
        name = self.name

        CacheThreadPoolLock.lockForWrite()
        try:
            if "VSQV_SAVE_IMAGE_DIRECTORY" in os.environ:
                path = Path(os.environ["VSQV_SAVE_IMAGE_DIRECTORY"]).expanduser()
            else:
                if len((path := QStandardPaths.standardLocations(QStandardPaths.PicturesLocation))) >= 1:
                    path = Path(path[0])
                else:
                    path = Path("~/Pictures").expanduser()
            if "VSQV_SAVE_IMAGE_FORMAT" in os.environ:
                format = os.environ["VSQV_SAVE_IMAGE_FORMAT"]
            else:
                format = "PNG"
            if name != "":
                path = path.joinpath(f"Index {index} ({name}) Frame {frame}.vsqv.{format.lower()}")
            else:
                path = path.joinpath(f"Index {index} Frame {frame}.vsqv.{format.lower()}")
            path = path.as_posix()
            if "VSQV_SAVE_IMAGE_QUALITY" in os.environ:
                quality = int(os.environ["VSQV_SAVE_IMAGE_QUALITY"])
            else:
                quality = 100
        
            CacheThreadPool.waitForDone()

            ImageLock.lock()
            if Image.save(path, format, quality):
                self.message = f"Image saved to \"{path}\""
            else:
                self.message = f"Failed to save image to \"{path}\""
            ImageLock.unlock()
        except Exception as e:
            self.message = str(traceback.format_exception(e, value=e, tb=None)[0]).splitlines()[0]
        CacheThreadPoolLock.unlock()

class WindowControl(QObject):
    def __init__(self):
        QObject.__init__(self)

    show = Signal()
    hide = Signal()


os.environ["QT_QUICK_CONTROLS_STYLE"] = "Material"
os.environ["QT_QUICK_CONTROLS_MATERIAL_THEME"] = "Dark"

# Options
# os.environ["VSQV_FORCE_8_BIT"]
# os.environ["VSQV_SCREEN_DEVICE_PIXEL_RATIO"]

if not (app := QGuiApplication.instance()):
    app = QGuiApplication([])
engine = QQmlApplicationEngine()

image_provider = ImageProvider()
engine.addImageProvider("backend", ImageProvider())
backend = Backend()
if "VSQV_SCREEN_DEVICE_PIXEL_RATIO" in os.environ:
    try:
        backend._devicePixelRatioOverride = float(os.environ["VSQV_SCREEN_DEVICE_PIXEL_RATIO"])
    except:
        raise ValueError("Environment variable \"VSQV_SCREEN_DEVICE_PIXEL_RATIO\" was set but isn't a number.")
    if np.isnan(backend._devicePixelRatioOverride):
        raise ValueError("Environment variable \"VSQV_SCREEN_DEVICE_PIXEL_RATIO\" was set but is not a number.")
    if backend._devicePixelRatioOverride < 0.0:
        raise ValueError("Environment variable \"VSQV_SCREEN_DEVICE_PIXEL_RATIO\" is less than 0.")
engine.rootContext().setContextProperty("backend", backend)
window_control = WindowControl()
engine.rootContext().setContextProperty("windowcontrol", window_control)

qml_file = Path(__file__).with_name("vsquickview.qml").as_posix()
engine.load(qml_file)


def View(clip: vs.VideoNode, index: int, name: Optional[str]=None, color_space_in: QColorSpace=QColorSpace(QColorSpace.SRgb), color_space: QColorSpace=QColorSpace(QColorSpace.SRgb)) -> None:
    assert(type(index) == int and 0 <= index < 10)
    assert(isinstance(name, typing.get_args(Optional[str])))

    clip = clip[:]
    if "VSQV_FORCE_8_BIT" not in os.environ:
        if clip.format.color_family == vs.YUV:
            clip = clip.resize.Spline36(format=vs.RGB48, matrix_in=vs.MATRIX_BT709, matrix=vs.MATRIX_RGB, transfer_in=vs.TRANSFER_BT709, transfer=13, dither_type="none")
        elif clip.format.color_family == vs.RGB:
            if clip.format.bits_per_sample == 8:
                pass
            elif clip.format.bits_per_sample == 16:
                pass
            else:
                clip = clip.resize.Spline36(format=vs.RGB48, dither_type="none")
        elif clip.format.color_family == vs.GRAY:
            if clip.format.bits_per_sample == 8:
                pass
            elif clip.format.bits_per_sample == 16:
                pass
            else:
                clip = clip.resize.Spline36(format=vs.GRAY16, dither_type="none")
        else:
            raise TypeError("Unsupported clip.format.color_family. vsquickview only supports vs.RGB, vs.YUV or vs.GRAY. To add support for other formats, raise an issue or make a pull request at https://github.com/Akatmks/vsquickview .")

    else: # "VSQV_FORCE_8_BIT" in os.environ
        if clip.format.color_family == vs.YUV:
            clip = clip.resize.Spline36(format=vs.RGB24, matrix_in=vs.MATRIX_BT709, matrix=vs.MATRIX_RGB, transfer_in=vs.TRANSFER_BT709, transfer=13, dither_type="none")
        elif clip.format.color_family == vs.RGB:
            clip = clip.resize.Spline36(format=vs.RGB24, dither_type="none")
        elif clip.format.color_family == vs.GRAY:
            clip = clip.resize.Spline36(format=vs.GRAY8, dither_type="none")
        else:
            raise TypeError("Unsupported clip.format.color_family. vsquickview only supports vs.RGB, vs.YUV or vs.GRAY. To add support for other formats, raise an issue or make a pull request at https://github.com/Akatmks/vsquickview .")

    if "VSQV_SCREEN_DEVICE_PIXEL_RATIO" in os.environ:
        try:
            device_pixel_ratio_override = float(os.environ["VSQV_SCREEN_DEVICE_PIXEL_RATIO"])
        except:
            raise ValueError("Environment variable \"VSQV_SCREEN_DEVICE_PIXEL_RATIO\" was set but isn't a number.")
        if np.isnan(device_pixel_ratio_override):
            raise ValueError("Environment variable \"VSQV_SCREEN_DEVICE_PIXEL_RATIO\" was set but is not a number.")
        if device_pixel_ratio_override < 0.0:
            raise ValueError("Environment variable \"VSQV_SCREEN_DEVICE_PIXEL_RATIO\" is less than 0.")
        backend.devicePixelRatioOverride = device_pixel_ratio_override

    Clips[index] = clip
    ClipColorSpaces[index] = (color_space_in, color_space)
    Names[index] = name
    CacheThreadPoolLock.lockForWrite()
    CacheThreadPool.waitForDone()
    CacheLocks[index].lockForWrite()
    Caches[index] = {}
    CacheHeads[index] = 0
    CacheLocks[index].unlock()
    CacheThreadPoolLock.unlock()

    backend.indexChanged.emit()

def RemoveView(clip: Union[vs.VideoNode, int, None]=None, index: Optional[int]=None) -> None:
    if index == None:
        index = clip
    assert(type(index) == int and 0 <= index < 10)

    Clips[index] = None
    ClipColorSpaces[index] = None
    Names[index] = None
    CacheThreadPoolLock.lockForWrite()
    CacheThreadPool.waitForDone()
    CacheLocks[index].lockForWrite()
    Caches[index] = {}
    CacheHeads[index] = 0
    CacheLocks[index].unlock()
    CacheThreadPoolLock.unlock()

    if backend.index == index:
        backend.indexChanged.emit()

def SetFrame(clip: Union[vs.VideoNode, int, None]=None, frame: Optional[int]=None) -> None:
    if frame == None:
        frame = clip
    assert(type(frame) == int)

    backend.switchFrame(frame)
def SetIndex(clip: Union[vs.VideoNode, int, None]=None, index: Optional[int]=None) -> None:
    if index == None:
        index = clip
    assert(type(index) == int and 0 <= index < 10)

    backend.switchIndex(index)
def SetPreviewGroup(clip: Union[vs.VideoNode, list[int], None]=None, group: Optional[list[int]]=None) -> None:
    if group == None:
        group = clip

    group = list(set(group))
    assert(all([type(item) == int and item >= 0 for item in group]))
    group.sort()

    backend.preview_group = group

    backend.previewGroupChanged.emit()
def ClearPreviewGroup(clip: Optional[vs.VideoNode]=None) -> None:
    backend.preview_group = []
    
    backend.previewGroupChanged.emit()
def PreviewGroup(clip: Optional[vs.VideoNode]=None) -> list[int]:
    return list(backend.preview_group)

def Show(clip: Optional[vs.VideoNode]=None) -> None:
    window_control.show.emit()
def Hide(clip: Optional[vs.VideoNode]=None) -> None:
    window_control.hide.emit()
