import QtQuick 2.15
import QtQuick3D 6.7
import QtQuick3D.AssetUtils 6.7

Item {
    id: root
    anchors.fill: parent

    signal overlayDragStarted()
    signal overlayDragMoved()
    signal overlayDragFinished()

    property bool overlayMode: tamagoOverlayMode
    property real modelYaw: 0
    property real modelPitch: 0
    property real yawVelocity: 0
    property real pitchVelocity: 0
    property real dragX: 0
    property real dragY: 0
    property double lastPointerTime: 0
    property string petMood: tamagoPetMood
    property string dragMode: "none"
    property bool windowDragGesture: false

    function wrapAngle(value) {
        return ((value % 360) + 360) % 360
    }

    function isPetClick(x, y) {
        // RuntimeLoader GLB meshes are not pickable by default. Keep ray picking when possible,
        // then use the character silhouette as a fallback on Qt versions without model access.
        var hit = view.pick(x, y)
        if (hit.objectHit)
            return true

        var nx = x / Math.max(1, view.width)
        var ny = y / Math.max(1, view.height)
        function inEllipse(cx, cy, rx, ry) {
            var dx = (nx - cx) / rx
            var dy = (ny - cy) / ry
            return dx * dx + dy * dy <= 1
        }
        return inEllipse(0.53, 0.57, 0.36, 0.39)
                || inEllipse(0.50, 0.11, 0.26, 0.20)
                || inEllipse(0.50, 0.92, 0.25, 0.07)
    }

    function isSproutGrab(x, y) {
        var nx = x / Math.max(1, view.width)
        var ny = y / Math.max(1, view.height)
        function inEllipse(cx, cy, rx, ry) {
            var dx = (nx - cx) / rx
            var dy = (ny - cy) / ry
            return dx * dx + dy * dy <= 1
        }
        return inEllipse(0.34, 0.20, 0.20, 0.16)
                || inEllipse(0.66, 0.20, 0.20, 0.16)
                || inEllipse(0.50, 0.34, 0.08, 0.14)
    }

    Rectangle {
        anchors.fill: parent
        color: tamagoBackgroundColor
        visible: !root.overlayMode
    }

    Image {
        id: roomBackground
        anchors.fill: parent
        visible: !root.overlayMode && tamagoBackgroundSource.toString().length > 0
        source: tamagoBackgroundSource
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        cache: true
    }

    View3D {
        id: view
        anchors.fill: parent

        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Transparent
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
        }

        camera: PerspectiveCamera {
            position: Qt.vector3d(0, 1.35, 5.2)
            fieldOfView: 35
            clipNear: 0.1
            clipFar: 100
        }

        DirectionalLight {
            eulerRotation: Qt.vector3d(-25, -25, 0)
            color: "#fff7ed"
            ambientColor: "#786d62"
            brightness: 1.15
        }

        DirectionalLight {
            eulerRotation: Qt.vector3d(-15, 145, 0)
            color: "#e8efff"
            ambientColor: "#394152"
            brightness: 0.55
        }

        Node {
            position: Qt.vector3d(0, 1.35, 0)
            eulerRotation: Qt.vector3d(root.modelPitch, root.modelYaw, 0)

            Node {
                id: idleMotion
                property real breathScale: 1.0
                property real pokeSquash: 1.0
                property real pokeWiggle: 0.0
                property real pokeFaceOpacity: 0.0
                x: pokeWiggle * 0.004
                scale: Qt.vector3d(pokeSquash, breathScale * pokeSquash, pokeSquash)
                eulerRotation: Qt.vector3d(0, 0, 0)

                RuntimeLoader {
                    source: idleMotion.pokeFaceOpacity >= 0.5 || root.petMood === "angry"
                            ? tamagoAngryModelSource
                            : root.petMood === "tense" ? tamagoTenseModelSource : tamagoModelSource
                    position: Qt.vector3d(0, -1.05, 0)
                    scale: Qt.vector3d(0.70, 0.70, 0.70)
                }
                // A slow, low-amplitude idle loop: a tiny lift and soft breath.
                // It lives below the drag rotation node, so dragging and inertia remain independent.
                ParallelAnimation {
                    running: true
                    loops: Animation.Infinite

                    SequentialAnimation {
                        NumberAnimation {
                            target: idleMotion
                            property: "y"
                            from: 0.0
                            to: 0.022
                            duration: 2300
                            easing.type: Easing.InOutSine
                        }
                        NumberAnimation {
                            target: idleMotion
                            property: "y"
                            from: 0.022
                            to: 0.0
                            duration: 2300
                            easing.type: Easing.InOutSine
                        }
                    }

                    SequentialAnimation {
                        NumberAnimation {
                            target: idleMotion
                            property: "breathScale"
                            from: 1.0
                            to: 1.012
                            duration: 2300
                            easing.type: Easing.InOutSine
                        }
                        NumberAnimation {
                            target: idleMotion
                            property: "breathScale"
                            from: 1.012
                            to: 1.0
                            duration: 2300
                            easing.type: Easing.InOutSine
                        }
                    }
                }

                // A quick, playful wobble as if the little character is mildly annoyed.
                SequentialAnimation {
                    id: pokeReaction
                    running: false

                    ParallelAnimation {
                        NumberAnimation {
                            target: idleMotion
                            property: "pokeSquash"
                            to: 0.93
                            duration: 85
                            easing.type: Easing.OutCubic
                        }
                        NumberAnimation {
                            target: idleMotion
                            property: "pokeWiggle"
                            to: -6
                            duration: 85
                            easing.type: Easing.OutCubic
                        }
                        NumberAnimation {
                            target: idleMotion
                            property: "pokeFaceOpacity"
                            to: 1.0
                            duration: 65
                            easing.type: Easing.OutCubic
                        }
                    }
                    NumberAnimation {
                        target: idleMotion
                        property: "pokeWiggle"
                        to: 6
                        duration: 80
                        easing.type: Easing.InOutSine
                    }
                    NumberAnimation {
                        target: idleMotion
                        property: "pokeWiggle"
                        to: -4
                        duration: 75
                        easing.type: Easing.InOutSine
                    }
                    NumberAnimation {
                        target: idleMotion
                        property: "pokeWiggle"
                        to: 2
                        duration: 75
                        easing.type: Easing.InOutSine
                    }
                    ParallelAnimation {
                        NumberAnimation {
                            target: idleMotion
                            property: "pokeSquash"
                            to: 1.0
                            duration: 180
                            easing.type: Easing.OutBack
                        }
                        NumberAnimation {
                            target: idleMotion
                            property: "pokeWiggle"
                            to: 0
                            duration: 160
                            easing.type: Easing.OutCubic
                        }
                        NumberAnimation {
                            target: idleMotion
                            property: "pokeFaceOpacity"
                            to: 0.0
                            duration: 180
                            easing.type: Easing.InOutSine
                        }
                    }
                }
            }
        }
    }

    MouseArea {
        id: rotationArea
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        preventStealing: true
        cursorShape: root.overlayMode && containsMouse && root.isSproutGrab(mouseX, mouseY)
                     ? Qt.SizeAllCursor
                     : pressed ? Qt.ClosedHandCursor : Qt.OpenHandCursor

        onPressed: function(mouse) {
            root.windowDragGesture = root.overlayMode && root.isSproutGrab(mouse.x, mouse.y)
            if (root.windowDragGesture) {
                root.dragMode = "move"
                root.overlayDragStarted()
                return
            }
            root.dragMode = "rotate"
            inertia.stop()
            root.yawVelocity = 0
            root.pitchVelocity = 0
            root.dragX = mouse.x
            root.dragY = mouse.y
            root.lastPointerTime = Date.now()
        }

        onPositionChanged: function(mouse) {
            if (!pressed)
                return
            if (root.dragMode === "move") {
                root.overlayDragMoved()
                return
            }

            var now = Date.now()
            var elapsed = Math.max(1, now - root.lastPointerTime)
            var dx = mouse.x - root.dragX
            var dy = mouse.y - root.dragY
            var yawDelta = dx * 0.48
            var pitchDelta = dy * 0.30

            root.modelYaw = root.wrapAngle(root.modelYaw + yawDelta)
            var nextPitch = root.modelPitch + pitchDelta
            root.modelPitch = Math.max(-16, Math.min(16, nextPitch))
            root.yawVelocity = Math.max(-0.32, Math.min(0.32, yawDelta / elapsed))
            root.pitchVelocity = root.modelPitch === nextPitch
                    ? Math.max(-0.20, Math.min(0.20, pitchDelta / elapsed)) : 0
            root.dragX = mouse.x
            root.dragY = mouse.y
            root.lastPointerTime = now
        }

        onReleased: {
            if (root.dragMode === "move") {
                root.overlayDragFinished()
                root.dragMode = "none"
                return
            }
            root.dragMode = "none"
            inertia.lastTick = Date.now()
            if (Math.abs(root.yawVelocity) > 0.003 || Math.abs(root.pitchVelocity) > 0.003)
                inertia.start()
        }

        onCanceled: {
            if (root.dragMode === "move")
                root.overlayDragFinished()
            root.dragMode = "none"
        }

        onClicked: function(mouse) {
            if (!root.windowDragGesture && root.isPetClick(mouse.x, mouse.y)) {
                inertia.stop()
                root.yawVelocity = 0
                root.pitchVelocity = 0
                pokeReaction.restart()
            }
        }
    }

    Timer {
        id: inertia
        interval: 16
        repeat: true
        property double lastTick: 0

        onTriggered: {
            var now = Date.now()
            var elapsed = Math.min(50, Math.max(1, now - lastTick))
            lastTick = now
            root.modelYaw = root.wrapAngle(root.modelYaw + root.yawVelocity * elapsed)

            var nextPitch = root.modelPitch + root.pitchVelocity * elapsed
            root.modelPitch = Math.max(-16, Math.min(16, nextPitch))
            if (root.modelPitch !== nextPitch)
                root.pitchVelocity = 0

            var friction = Math.exp(-elapsed / 500)
            root.yawVelocity *= friction
            root.pitchVelocity *= friction
            if (Math.abs(root.yawVelocity) < 0.003 && Math.abs(root.pitchVelocity) < 0.003) {
                root.yawVelocity = 0
                root.pitchVelocity = 0
                stop()
            }
        }
    }
}
