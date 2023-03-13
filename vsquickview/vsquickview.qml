// vsquickview
// Copyright (c) Akatsumekusa and contributors

/* Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 * 
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
 * BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
 * ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 * CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Window 2.15

ApplicationWindow {
    id: window
    width: 1280
    height: 720
    visible: true
    visibility: Window.FullScreen

    title: "vsquickview"
    
    Material.theme: Material.Dark

    onClosing: (close) => {
        window.visible = false
        close.accepted = false
    }

    Connections {
        target: windowcontrol
        function onShow() {
            window.visible = true
        }
        function onHide() {
            window.visible = false
        }
    }

    Connections {
        target: backend
        function onImageChanged() {
            image.source = "image://backend/" + Math.random().toExponential()
        }
    }
    
    Image {
        id: image
        anchors.centerIn: parent
        anchors.horizontalCenterOffset: 0
        anchors.verticalCenterOffset: 0

        source: "image://backend/" + Math.random().toExponential()
    }

    property bool showLabelText: false
    property string extraLabelText: ""
    function updateLabelText() {
        if(extraLabelText) {
            label.text = extraLabelText
        }
        else if(showLabelText) {
            label.text = "Index " + backend.index.toString() + (backend.name ? ": " + backend.name : "") + " / Frame " + backend.frame.toString()
        }
        else {
            label.text = ""
        }
    }
    Connections {
        target: window
        function onShowLabelTextChanged() {
            updateLabelText()
        }
        function onExtraLabelTextChanged() {
            updateLabelText()
        }
    }
    Connections {
        target: backend
        function onIndexChanged() {
            updateLabelText()
        }
    }
    Connections {
        target: backend
        function onFrameChanged() {
            updateLabelText()
        }
    }
    Connections {
        target: backend
        function onNameChanged() {
            updateLabelText()
        }
    }

    Label {
        id: label
        font.pixelSize: 35
        color: "#B0FFFFFF"
        antialiasing: true
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 54
        anchors.left: parent.left
        anchors.leftMargin: 84

        text: ""
        onTextChanged: {
            if(text) {
                visible = true
            }
            else {
                visible = false
            }
        }

        background: Rectangle {
            color: "#40000000"
        }
    }
    
    MouseArea {
        id: mousearea
        z: 100
        focus: true
        anchors.fill: parent

        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
        
        property bool pan: false
        property real offset_before_start_x
        property real offset_before_start_y
        property real start_x
        property real start_y

        onPressed: (mouse) => {
            if(mouse.button === Qt.LeftButton || mouse.button === Qt.MiddleButton) {
                pan = true
                offset_before_start_x = image.anchors.horizontalCenterOffset
                offset_before_start_y = image.anchors.verticalCenterOffset
                start_x = mouseX
                start_y = mouseY
            }

            else if(mouse.button === Qt.RightButton) {
                backend.nextIndex()
            }
        }
        onPositionChanged: (mouse) => {
            if(pan) {
                image.anchors.horizontalCenterOffset = mouseX - start_x + offset_before_start_x
                image.anchors.verticalCenterOffset = mouseY - start_y + offset_before_start_y

                if(backend.scale === 1 && image.anchors.horizontalCenterOffset < 6 &&
                                          image.anchors.verticalCenterOffset < 6) {
                    image.anchors.horizontalCenterOffset = 0
                    image.anchors.verticalCenterOffset = 0
                }
                
            }
        }
        onReleased: (mouse) => {
            if(pan && (mouse.button === Qt.LeftButton || mouse.button === Qt.MiddleButton)) {
                pan = false
            }
        }

        onWheel: (wheel) => {
            let image_x = image.x
            let image_y = image.y
            let image_width = image.width
            let image_height = image.height
            let scaling = 1.0

            if(wheel.angleDelta.y > 0) {
                scaling = backend.moreScale()
            }
            else if(wheel.angleDelta.y < 0) {
                scaling = backend.lessScale()
            }

            if(mouseX > image_x && mouseX < image_x + image_width &&
               mouseY > image_y && mouseY < image_y + image_height) {
                image.anchors.horizontalCenterOffset = image.anchors.horizontalCenterOffset - (mouseX - image_x - image_width/2) * (scaling - 1)
                image.anchors.verticalCenterOffset = image.anchors.verticalCenterOffset - (mouseY - image_y - image_height/2) * (scaling - 1)
            }
        }

        property int previous_visibility: Window.AutomaticVisibility
        property string gotoFrame: "NaN"
        onGotoFrameChanged: {
            if(gotoFrame !== "NaN") {
                extraLabelText = "Goto frame " + gotoFrame
            }
            else {
                extraLabelText = ""
            }
        }
        property bool altPressed: false

        Keys.onPressed: (event) => {
            if((event.modifiers & Qt.AltModifier) && event.key !== Qt.Key_Alt) {
                altPressed = false
            }

            if(event.key === Qt.Key_F11 || event.key === Qt.Key_F) {
                if(window.visibility === Window.Windowed ||
                   window.visibility === Window.Maximized) {
                    previous_visibility = window.visibility
                    window.visibility = Window.FullScreen
                }
                else if(window.visibility === Window.FullScreen) {
                    window.visibility = previous_visibility
                }
            }

            else if(event.key === Qt.Key_Space) {
                backend.nextIndex()
            }
            else if(event.key === Qt.Key_Alt) {
                altPressed = true
            }

            else if(event.key === Qt.Key_Right) {
                backend.nextFrame()
            }
            else if(event.key === Qt.Key_Left) {
                backend.prevFrame()
            }

            else if(event.key === Qt.Key_G) {
                gotoFrame = ""
            }
            else if(gotoFrame !== "NaN" && event.key === Qt.Key_0) {
                if(gotoFrame === "0");
                else {
                    gotoFrame = gotoFrame + "0"
                }
            }
            else if(gotoFrame !== "NaN" && event.key === Qt.Key_1) {
                if(gotoFrame === "0") {
                    gotoFrame = "1"
                }
                else {
                    gotoFrame = gotoFrame + "1"
                }
            }
            else if(gotoFrame !== "NaN" && event.key === Qt.Key_2) {
                if(gotoFrame === "0") {
                    gotoFrame = "2"
                }
                else {
                    gotoFrame = gotoFrame + "2"
                }
            }
            else if(gotoFrame !== "NaN" && event.key === Qt.Key_3) {
                if(gotoFrame === "0") {
                    gotoFrame = "3"
                }
                else {
                    gotoFrame = gotoFrame + "3"
                }
            }
            else if(gotoFrame !== "NaN" && event.key === Qt.Key_4) {
                if(gotoFrame === "0") {
                    gotoFrame = "4"
                }
                else {
                    gotoFrame = gotoFrame + "4"
                }
            }
            else if(gotoFrame !== "NaN" && event.key === Qt.Key_5) {
                if(gotoFrame === "0") {
                    gotoFrame = "5"
                }
                else {
                    gotoFrame = gotoFrame + "5"
                }
            }
            else if(gotoFrame !== "NaN" && event.key === Qt.Key_6) {
                if(gotoFrame === "0") {
                    gotoFrame = "6"
                }
                else {
                    gotoFrame = gotoFrame + "6"
                }
            }
            else if(gotoFrame !== "NaN" && event.key === Qt.Key_7) {
                if(gotoFrame === "0") {
                    gotoFrame = "7"
                }
                else {
                    gotoFrame = gotoFrame + "7"
                }
            }
            else if(gotoFrame !== "NaN" && event.key === Qt.Key_8) {
                if(gotoFrame === "0") {
                    gotoFrame = "8"
                }
                else {
                    gotoFrame = gotoFrame + "8"
                }
            }
            else if(gotoFrame !== "NaN" && event.key === Qt.Key_9) {
                if(gotoFrame === "0") {
                    gotoFrame = "9"
                }
                else {
                    gotoFrame = gotoFrame + "9"
                }
            }
            else if(gotoFrame !== "NaN" && event.key === Qt.Key_Backspace) {
                gotoFrame = gotoFrame.substring(0, gotoFrame.length - 1)
            }
            else if(gotoFrame !== "NaN" && event.key === Qt.Key_Escape) {
                gotoFrame = "NaN"
            }
            else if(gotoFrame !== "NaN" && event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                backend.switchFrame(+gotoFrame)
                gotoFrame = "NaN"
            }

            else if(event.key === Qt.Key_0) {
                backend.switchIndex(0)
            }
            else if(event.key === Qt.Key_1) {
                backend.switchIndex(1)
            }
            else if(event.key === Qt.Key_2) {
                backend.switchIndex(2)
            }
            else if(event.key === Qt.Key_3) {
                backend.switchIndex(3)
            }
            else if(event.key === Qt.Key_4) {
                backend.switchIndex(4)
            }
            else if(event.key === Qt.Key_5) {
                backend.switchIndex(5)
            }
            else if(event.key === Qt.Key_6) {
                backend.switchIndex(6)
            }
            else if(event.key === Qt.Key_7) {
                backend.switchIndex(7)
            }
            else if(event.key === Qt.Key_8) {
                backend.switchIndex(8)
            }
            else if(event.key === Qt.Key_9) {
                backend.switchIndex(9)
            }

            else {
                event.accepted = false
            }
        }
        Keys.onReleased: (event) => {
            if(altPressed && event.key === Qt.Key_Alt) {
                window.showLabelText = !window.showLabelText
                altPressed = false
            }
        }
    }
}
