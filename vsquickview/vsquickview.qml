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
            label.text = "Index " + backend.index.toString() + (backend.name ? ": " + backend.name : "")
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
        
        property bool space: false
        property bool pan: false
        property real offset_before_start_x
        property real offset_before_start_y
        property real start_x
        property real start_y

        onPressed: (mouse) => {
            if((mouse.button == Qt.LeftButton && space) ||
               mouse.button == Qt.MiddleButton) {
                pan = true
                offset_before_start_x = image.anchors.horizontalCenterOffset
                offset_before_start_y = image.anchors.verticalCenterOffset
                start_x = mouseX
                start_y = mouseY
            }
            
            else if(mouse.button == Qt.LeftButton) {
                backend.nextIndex()
            }

            else if(mouse.button == Qt.RightButton) {
                window.showLabelText = !window.showLabelText
            }
        }
        onPositionChanged: (mouse) => {
            if(pan) {
                image.anchors.horizontalCenterOffset = mouseX - start_x + offset_before_start_x
                image.anchors.verticalCenterOffset = mouseY - start_y + offset_before_start_y
            }
        }
        onReleased: (mouse) => {
            if(pan && (mouse.button == Qt.LeftButton ||
                       mouse.button == Qt.MiddleButton)) {
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
        property int gotoFrame: -1
        onGotoFrameChanged: {
            if(gotoFrame >= 0) {
                extraLabelText = "Goto frame " + (gotoFrame > 0 ? gotoFrame.toString() : "")
            }
            else {
                extraLabelText = ""
            }
        }

        Keys.onPressed: (event) => {
            if(event.key == Qt.Key_F11 || event.key == Qt.Key_F) {
                if(window.visibility == Window.Windowed ||
                   window.visibility == Window.Maximized) {
                    previous_visibility = window.visibility
                    window.visibility = Window.FullScreen
                }
                else if(window.visibility == Window.FullScreen) {
                    window.visibility = previous_visibility
                }
            }

            else if(event.key == Qt.Key_Space) {
                space = true
            }

            else if(event.key == Qt.Key_Right) {
                backend.nextFrame()
            }
            else if(event.key == Qt.Key_Left) {
                backend.prevFrame()
            }

            else if(event.key == Qt.Key_G) {
                gotoFrame = 0
            }
            else if(gotoFrame != -1 && event.key == Qt.Key_0) {
                gotoFrame = gotoFrame * 10 + 0
            }
            else if(gotoFrame != -1 && event.key == Qt.Key_1) {
                gotoFrame = gotoFrame * 10 + 1
            }
            else if(gotoFrame != -1 && event.key == Qt.Key_2) {
                gotoFrame = gotoFrame * 10 + 2
            }
            else if(gotoFrame != -1 && event.key == Qt.Key_3) {
                gotoFrame = gotoFrame * 10 + 3
            }
            else if(gotoFrame != -1 && event.key == Qt.Key_4) {
                gotoFrame = gotoFrame * 10 + 4
            }
            else if(gotoFrame != -1 && event.key == Qt.Key_5) {
                gotoFrame = gotoFrame * 10 + 5
            }
            else if(gotoFrame != -1 && event.key == Qt.Key_6) {
                gotoFrame = gotoFrame * 10 + 6
            }
            else if(gotoFrame != -1 && event.key == Qt.Key_7) {
                gotoFrame = gotoFrame * 10 + 7
            }
            else if(gotoFrame != -1 && event.key == Qt.Key_8) {
                gotoFrame = gotoFrame * 10 + 8
            }
            else if(gotoFrame != -1 && event.key == Qt.Key_9) {
                gotoFrame = gotoFrame * 10 + 9
            }
            else if(event.key == Qt.Key_Return || event.key == Qt.Key_Enter) {
                backend.switchFrame(gotoFrame)
                gotoFrame = -1
            }

            else if(gotoFrame == -1 && event.key == Qt.Key_0) {
                backend.switchIndex(0)
            }
            else if(gotoFrame == -1 && event.key == Qt.Key_1) {
                backend.switchIndex(1)
            }
            else if(gotoFrame == -1 && event.key == Qt.Key_2) {
                backend.switchIndex(2)
            }
            else if(gotoFrame == -1 && event.key == Qt.Key_3) {
                backend.switchIndex(3)
            }
            else if(gotoFrame == -1 && event.key == Qt.Key_4) {
                backend.switchIndex(4)
            }
            else if(gotoFrame == -1 && event.key == Qt.Key_5) {
                backend.switchIndex(5)
            }
            else if(gotoFrame == -1 && event.key == Qt.Key_6) {
                backend.switchIndex(6)
            }
            else if(gotoFrame == -1 && event.key == Qt.Key_7) {
                backend.switchIndex(7)
            }
            else if(gotoFrame == -1 && event.key == Qt.Key_8) {
                backend.switchIndex(8)
            }
            else if(gotoFrame == -1 && event.key == Qt.Key_9) {
                backend.switchIndex(9)
            }

            else {
                event.accepted = False
            }
        }

        Keys.onReleased: (event) => {
            if(event.key == Qt.Key_Space) {
                space = false
            }
        }
    }
}
