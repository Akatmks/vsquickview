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

import vapoursynth as vs
from vapoursynth import core

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
            ramp_frame[plane][y, x] = round(ramp.width / (1 + 498 + 516) * x) + 4
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
