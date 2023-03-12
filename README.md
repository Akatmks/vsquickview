## vsquickview

vsquickview is a single-frame VapourSynth preview script designed to be used together with Jupyter Notebook with these advantages:  
– Less waiting. vsquickview will run alongside Jupyter Notebook. Everytimes you make an adjustment, you can switch to the vsquickview window to see the updated result immediately.  
– Easier comparing between two clips with a left click similar to slow.pics. Also possible for blind compare between two clips.  

```py
%gui qt5
import vsquickview

vsquickview.view(0, clip, "Original")
vsquickview.view(1, clip, "Compare")
```
