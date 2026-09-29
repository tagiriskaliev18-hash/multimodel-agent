// Слайды, которые показываются во время копирования файлов.
// Переключение сделано своим таймером внутри одного слайда: так оно не зависит
// от навигации Presentation, которая в этой версии Calamares не листает слайды.
import QtQuick 2.0
import calamares.slideshow 1.0

Presentation {
    id: presentation

    Slide {
        id: show
        anchors.fill: parent

        property int current: 0
        property var slides: [
            { glyph: "👋", title: "Добро пожаловать в AIsktagOS",
              body: "Удобство macOS, свобода Linux Mint и надёжность Ubuntu LTS в одной системе. Установка займёт 5–15 минут." },
            { glyph: "⌘", title: "Привычный интерфейс",
              body: "Строка меню сверху, док снизу, поиск по Meta+Space (как Spotlight), обзор окон по Meta+W или в углу экрана слева снизу." },
            { glyph: "</>", title: "Готова к разработке сразу",
              body: "VS Code, Git, Docker и Podman, Python, Node.js, Rust, компиляторы C/C++, терминал kitty с zsh и подсказками уже установлены." },
            { glyph: "🎮", title: "Любая видеокарта",
              body: "AMD и Intel работают сразу. Для NVIDIA откройте «Менеджер драйверов»: он предложит нужный драйвер в один клик." },
            { glyph: "⏪", title: "Обновления без страха",
              body: "Перед каждым обновлением создаётся снимок системы. Если что-то пошло не так, откат в Timeshift занимает минуту." },
            { glyph: "🛍", title: "Тысячи приложений",
              body: "Центр приложений Discover: пакеты Ubuntu и магазин Flathub. Telegram, Spotify, Slack, JetBrains, OBS и многое другое." }
        ]

        Rectangle {
            anchors.fill: parent
            color: "#12142a"
        }
        Image {
            anchors.fill: parent
            source: "slide-bg.jpg"
            fillMode: Image.PreserveAspectCrop
        }

        Column {
            id: content
            anchors.centerIn: parent
            width: parent.width * 0.78
            spacing: 18
            opacity: 1
            Behavior on opacity { NumberAnimation { duration: 350 } }

            Text {
                text: show.slides[show.current].glyph
                font.pixelSize: 64
                color: "#ffffff"
                anchors.horizontalCenter: parent.horizontalCenter
            }
            Text {
                text: show.slides[show.current].title
                font.pixelSize: 30
                font.weight: Font.DemiBold
                color: "#ffffff"
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
            }
            Text {
                text: show.slides[show.current].body
                font.pixelSize: 17
                color: "#d6d9f0"
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                lineHeight: 1.25
            }
        }

        // Точки-индикаторы
        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 24
            spacing: 10
            Repeater {
                model: show.slides.length
                Rectangle {
                    width: 8; height: 8; radius: 4
                    color: index === show.current ? "#ffffff" : "#5a5f86"
                }
            }
        }

        Timer {
            interval: 9000
            running: true
            repeat: true
            onTriggered: show.current = (show.current + 1) % show.slides.length
        }
    }
}
