<h1 align="center">vsquickview</h1>

vsquickview is a frame-by-frame VapourSynth preview script designed to be used together with Jupyter Notebook with these advantages:  

* Less waiting. vsquickview will run alongside Jupyter Notebook. Everytimes you make an adjustment, you can switch to the vsquickview window to see the updated result immediately.  
* Easier comparing between two clips with a right click. Blind comparing is also possible.  

*Thanks to*  

* Setsugen no ao for helping with VapourSynth magics.  
* witchymary and others for helping with the UX.  

### Install vsquickview

Install vsquickview from pip:  

```sh
python3 -m pip install vsquickview
```

vsquickview also requires fmtc to work. Make sure you have fmtc installed or install it using the following command:  

```sh
vsrepo install fmtc
```

### Using vsquickview's Python interface

Create a new Jupyter Notebook and import vsquickview:  
```py
%gui qt5
import vsquickview as vsqv
```
`%gui qt5` is a magic command to let Jupyter Notebook integrates with the Qt event loop. Please make sure to call it before importing vsquickview.  

After this cell is executed, a fullscreen vsquickview window should be opened, showing an ARIB STD-B66 colour bar. We will be looking at the GUI in the next section, but before that, let's see how we can add clips to vsquickview:  

```py
vsqv.View(src16, 0, "Source")
vsqv.View(compare16, 1, "Compare")
```

`vsquickview.View()` is defined as below:  
```py
View(clip: vs.VideoNode, index: int, name: Optional[str]=None)
```

* The first parameter is the clip for preview.  
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
View(clip: vs.VideoNode, index: int, name: Optional[str]=None)
RemoveView(clip: Union[vs.VideoNode, int, None]=None, index: Optional[int]=None)
SetFrame(clip: Union[vs.VideoNode, int, None]=None, frame: Optional[int]=None)
SetIndex(clip: Union[vs.VideoNode, int, None]=None, index: Optional[int]=None)
Show(clip: Optional[vs.VideoNode]=None)
Hide(clip: Optional[vs.VideoNode]=None)
```

### Using vsquickview's GUI

On startup, vsquickview displays the first frame of the clip at index 0 on startup. Press `Alt` key and you will see a label on the bottom-left corner of the screen that reads `Index 0: [Name of the clip] / Frame 0`.  

You can switch to another frame using `G` key. Press `G` key and type in the frame number, then press `Enter` to switch to a new frame. You can also use the `Left` or `Right` key to go to previous or next frame.    

You can cycle between clips using the right mouse button. If you have more than one clip loaded and available at the specific frame number, press the right mouse button and the same frame of the next available clip will be displayed. Press `Shift` and the right mouse button and the clip will be cycled backwards.  

Other usages are listed below:  

* `Left Mouse Button` or `Middle Mouse Button`: Pan the clip preview.  
* `Scroll Wheel`: Zoom the preview at 100%, 200%, 300%, or 400%.  
* `Right Mouse Button` or `Space`: Switch to the next available clip. `Shift` and `Right Mouse Button` or `Space`: Switch to the previous available clip.  
* `Alt`: Toggle the label at the bottom-left corner of the screen.  
* `0`, `1`, `2` … `9`: Switch to the clip at the specific index.  
* `G`: Press `G` key and type the frame number followed by `Enter` key to go to a specific frame.  
* `Left` Key or `Right` Key: Go to the previous or the next frame.  
* `Up` Key or `Down` Key: Go to the next or previous clip, but not cycling the clips.  
* `F` or `F11`: Toggle fullscreen.  

vsquickview will be closed when you terminate or restart the Jupyter Notebook section. If you close the vsquickview window by accident, you can reopen it by calling function `vsquickview.Show()`.  
