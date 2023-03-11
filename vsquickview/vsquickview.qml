import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material

ApplicationWindow {
    id: window
    visible: true
    visibility: "FullScreen"
    
    Material.theme: Material.Dark

    ScrollView {
        anchors.fill: parent

        Rectangle {
            width:  Math.max(window.width, image.width)
            height:  Math.max(window.height, image.height)
            color: "transparent"

            Image {
                id: image
                anchors.centerIn: parent

                source: "image://backend/0"
            }
        }
    }
}
