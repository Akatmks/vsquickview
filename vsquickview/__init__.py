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

import __main__
import os

main = dir(__main__)

if "get_ipython" in main:
    os.environ["QT_API"] = "pyside6"
    __main__.get_ipython().run_line_magic("gui", "qt6")

# "__main__" seems to only get populated in interactive environments
# including vanilla Python and Jupyter Notebook (undocumented).
# "get_ipython" is a fail safe for Jupyter Notebook.
# "__file__" will get populated when Python code is run as a script
# (documented / intended), but for some reason it is not populated in
# VSPipe as of R65 (undocumented / probably not intended?).
if "__main__" in main or "get_ipython" in main or "__file__" in main:
    from .vsquickview import View, \
                             RemoveView, \
                             SetFrame, \
                             SetIndex, \
                             SetPreviewGroup, \
                             ClearPreviewGroup, \
                             PreviewGroup, \
                             Show, \
                             Hide, \
                             app
else:
    from .fakevsquickview import View, \
                                 RemoveView, \
                                 SetFrame, \
                                 SetIndex, \
                                 SetPreviewGroup, \
                                 ClearPreviewGroup, \
                                 PreviewGroup, \
                                 Show, \
                                 Hide, \
                                 app

__version__ = "1.1.5"
