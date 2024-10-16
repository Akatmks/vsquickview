<h1 align="center">vsquickview</h1>

vsquickview is a VapourSynth preview script designed to be used together with Jupyter Notebook with these advantages:  

* Less waiting. vsquickview will run alongside Jupyter Notebook. Everytimes you make an adjustment, you can switch to the vsquickview window to view the result immediately.  
* Easier comparing between two clips with a right click, similar to that of [slow.pics](https://slow.pics/). Blind comparing is also possible.  

*Thanks to*  

* Setsugen no ao and Zewia for helping with VapourSynth magics.  
* witchymary and others for helping with the UX.  

### Install vsquickview

Install vsquickview from pip:  

```sh
python3 -m pip install vsquickview
```

### Using vsquickview's Python interface

Create a new Jupyter Notebook and import vsquickview:  
```py
%gui qt6
import vsquickview as vsqv
```
`%gui qt6` is a [magic command](https://ipython.readthedocs.io/en/stable/interactive/magics.html#magic-gui) to let Jupyter Notebook integrate with the Qt event loop. If you have both PyQt6 and PySide6 installed, you may add `os.environ["QT_API"] = "pyside6"` before `%gui qt6` to so that Jupyter Notebook would initialise with PySide6.  

After this cell is executed, a fullscreen vsquickview window should be opened, showing an ARIB STD-B66 colour bar. We will be looking at the GUI in the next section, but before that, let's see how we can add clips to vsquickview:  

```py
vsqv.View(src16, 0, "Source")
vsqv.View(compare16, 1, "Compare")
```

`vsquickview.View()` is defined as below:  
```py
View(clip: vs.VideoNode, index: int, name: Optional[str]=None)
```

* The first parameter is the clip to preview. vsquickview accepts `vs.YUV`, `vs.RGB` and `vs.GRAY` formats. vsquickview uses `core.resize.Spline36` internally to [convert](https://github.com/Akatmks/vsquickview/blob/08cdc9c9c84e11b75ce4711c23baacb94b353573/vsquickview/vsquickview.py#L400) the clip to either 16-bit `vs.RGB`, 8-bit `vs.RGB`, 16-bit `vs.GRAY` or 8-bit `vs.GRAY` format. You may supply vsquickview with clips of these formats to avoid conversions. For HDR source or calibrated display, see [Colour management](#colour-management).  
* Similar to vspreview, vsquickview has 10 video slots from 0 to 9. This is specifed using the second parameter `index`.  
* You can also pass a third parameter to specify a name for the clip. This will be displayed in vsquickview window alongside the clip's index.  

Clip on an index can be updated using the same `vsquickview.View()` function:  
```py
vsqv.View(new_compare16, 1, "New Compare")
```

To remove a clip with a specific index:  
```py
vsqv.RemoveView(1)
```

If you prefer a more VapourSynth-style call to vsquickview, you could call the functions like:  
```py
vsqv.View(compare16, index=1, name="Compare")
vsqv.RemoveView(None, index=1)
```

Here is a short list of functions and their definitions in vsquickview:  
```py
View(clip: vs.VideoNode, index: int, name: Optional[str]=None, color_space_in: QColorSpace=QColorSpace(QColorSpace.SRgb), color_space: QColorSpace=QColorSpace(QColorSpace.SRgb))
RemoveView(clip: Union[vs.VideoNode, int, None]=None, index: Optional[int]=None)
SetFrame(clip: Union[vs.VideoNode, int, None]=None, frame: Optional[int]=None)
SetIndex(clip: Union[vs.VideoNode, int, None]=None, index: Optional[int]=None)
Show(clip: Optional[vs.VideoNode]=None)
Hide(clip: Optional[vs.VideoNode]=None)
```

After previewing, you may directly export Jupyter Notebook to Python file for VSPipe. vsquickview will be automatically [dis](https://github.com/Akatmks/vsquickview/blob/08cdc9c9c84e11b75ce4711c23baacb94b353573/vsquickview/__init__.py#L27-L46)[abled](https://github.com/Akatmks/vsquickview/blob/08cdc9c9c84e11b75ce4711c23baacb94b353573/vsquickview/fakevsquickview.py#L26-L43) when run in VSPipe.  

### Using vsquickview's GUI

On startup, vsquickview displays the first frame of the clip at index 0 on startup. Press `Alt` or `AltGr` key and you will see a label on the bottom-left corner of the screen that reads `Index 0: [Name of the clip] / Frame 0`.  

You can switch to another frame using `G` key. Press `G` key and type in the frame number, then press `Enter` to switch to a new frame. You can also use the `Left` or `Right` key to go to previous or next frame.    

You can cycle between clips using `Right Mouse Button` or `Space` key. Press `Shift` with the `Right Mouse Button` or `Space` key to cycle the clips backwards.  

Other usages are listed below:  

* `Left Mouse Button` or `Middle Mouse Button`: Pan the clip preview.  
* `Scroll Wheel`: Zoom the preview.  
* `Alt` or `AltGr`: Toggle the label at the bottom-left corner of the screen.  
* `Right Mouse Button` or `Space`: Switch to the next available clip. `Shift` and `Right Mouse Button` or `Space`: Switch to the previous available clip.  
* `0`, `1`, `2` … `9`: Switch to the clip at the specific index, similar to the control of vspreview.  
* `Up` or `Down`: Go to the next or previous clip, but not cycling the clips.  
* `G` or `` ` ``: Press `G` or `` ` `` key and type the frame number followed by `Enter` key to go to a specific frame.  
* `Left` Key or `Right` Key: Go to the previous or the next frame.  
* `Ctrl` and `Left` Key or `Right` Key: Jump 12 frames backwards or forwards.  
* `F` or `F11`: Toggle fullscreen.  
* `Q`: Close vsquickview window.  

vsquickview will not quit when vsquickview window are closed. You can reopen the window by calling function `vsquickview.Show()`.  vsquickview will only quit when you terminate or restart Jupyter Notebook session.  

### Using preview group

Additionally, you can also create preview group for a selected list of frames you want to compare.  

Set preview group using the `vsquickview.SetPreviewGroup()` function:  
```py
vsqv.SetPreviewGroup([1934, 6849, 13226, 21647, 25374, 26811, 28499, 29111])
```

In the vsquickview GUI, use `Shift` key with `Left` or `Right` key to go to the previous or next frame in the set preview group.  

You can add frame to or remove frame from the preview group using `R` Key from GUI.  

You can retrieve the current preview group using the `vsquickview.PreviewGroup()` function.  
```py
pg = vsqv.PreviewGroup()
```

Here is a short list of functions and their definitions for preview group:  
```py
SetPreviewGroup(clip: Union[vs.VideoNode, list, None]=None, group: Optional[list]=None)
ClearPreviewGroup(clip: Optional[vs.VideoNode]=None)
PreviewGroup(clip: Optional[vs.VideoNode]=None)
```

### Colour management

QtQML *does not* currently support colour management. Before auto colour management is possible, you may manually [convert](https://doc.qt.io/qt/qimage.html#convertToColorSpace) the colour by passing two [`QColorSpace`](https://doc.qt.io/qt/qcolorspace.html) instances alongside the clip to `vsquickview.View()`.  

```py
from PySide6.QtCore import QFile, QIODevice
from PySide6.QtGui import QColorSpace

# (1) Previewing SDR videos with a calibrated display.
icc_profile = QFile("/path/to/calibrated.icc")
icc_profile.open(QIODevice.ReadOnly)
color_space = QColorSpace.fromIccProfile(icc_profile.readAll())

vsqv.View(compare16, index=1, name="Compare", color_space=color_space)

# (2) Previewing HDR videos with an sRGB display.
# See https://doc.qt.io/qt/qcolorspace.html#public-functions for more
# ways to construct QColorSpace, including using custom primaries and
# transfer function or transfer function table.
color_space_in = QColorSpace(QColorSpace.Bt2020)

# Only supports clips with vs.RGB or vs.GRAY format, because clips with
# vs.YUV format will be converted internally to vs.RGB assuming BT.709
# primaries, transfer and matrix.
vsqv.View(compare16, index=1, name="Compare", color_space_in=color_space_in)
```
```py
# Both `color_space_in` and `color_space` are optional and default to
# `QColorSpace(QColorSpace.SRgb)`.  
View(clip: vs.VideoNode, index: int, name: Optional[str]=None, color_space_in: QColorSpace=QColorSpace(QColorSpace.SRgb), color_space: QColorSpace=QColorSpace(QColorSpace.SRgb))
```
