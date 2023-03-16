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

vsquickview also requires fmtc to function. Make sure you have fmtc installed.  

### Using vsquickview

Create a new Jupyter Notebook and import vsquickview:  
```py
%gui qt5
import vsquickview
```
`%gui qt5` is a magic command to let Jupyter Notebook integrates itself with the Qt event loop. Please make sure to call it before importing vsquickview.  

After this cell is executed, a fullscreen vsquickview window should be opened, showing an ARIB STD-B66 colour bar.  

Now we can add clips to the vsquickview using function `vsquickview.view()`:  
```py
vsquickview.view(0, clip1, "Source")
vsquickview.view(1, clip2, "Compare")
```

`vsquickview.view()` is defined as below:  
```py
view(index: int, clip, name: typing.Optional[str]=None)
```

* Similar to vspreview, vsquickview has 10 video slots from 0 to 9. This is specifed using the first parameter `index`.  
* The second parameter `clip` is the clip to preview.  
* You can also pass a third parameter to specify a name for the clip. This will be displayed in vsquickview window alongside the clip's index.  

Clip on an index can be updated using the same `vsquickview.view()` function:  
```py
vsquickview.view(1, clip_new, "New Compare")
```

To remove a clip with a specific index:  
```py
vsquickview.removeView(1)
```

Now we have explained vsquickview's Python interface, we can now have a look at vsquickview window.  

vsquickview displays the first frame of the clip at index 0 on startup. Press `Alt` key and you will see a label on the bottom-left corner of the screen `Index 0: [Name of the clip] / Frame 0`.  

You can switch to another frame using `G` key. Press `G` key and type in the frame number, then press `Enter` and a new frame will be displayed.  

You can cycle between clips using the right mouse button. If you have more than one clip loaded and available at the specific frame number, press the right mouse button and the same frame of the next available clip will be displayed.  

Other usages are listed below:  

* `Left Mouse Button` or `Middle Mouse Button`: Pan the clip preview.  
* `Scroll Wheel`: Zoom the preview at 100%, 200%, 300%, or 400%.  
* `Alt`: Toggle the label at the bottom-left corner of the screen.  
* `Right Mouse Button` or `Space`: Switch to the next available clip.  
* `0`, `1`, `2` … `9`: Switch to the clip at the specific index.  
* `G`: Press `G` key and type the frame number followed by `Enter` key to go to a specific frame.  
* `Left` Key or `Right` Key: Go to the previous or the next frame.  
* `F` or `F11`: Toggle fullscreen.  

vsquickview will be closed when you terminate or restart the Jupyter Notebook section. If you close the vsquickview window by accident, you can reopen it by calling function `vsquickview.show()`.  
