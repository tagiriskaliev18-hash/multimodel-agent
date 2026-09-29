// Слайды, которые показываются во время копирования файлов
import QtQuick 2.0
import calamares.slideshow 1.0

Presentation {
    id: presentation

    // Тёмная подложка вместо белых полей вокруг слайдов
    Rectangle {
        anchors.fill: parent
        color: "#12142a"
        z: -1
    }

    Timer {
        interval: 9000
        running: true
        repeat: true
        onTriggered: presentation.goToNextSlide()
    }

    component InfoSlide: Slide {
        property string title
        property string body
        property string glyph

        Image {
            anchors.fill: parent
            source: "slide-bg.jpg"
            fillMode: Image.PreserveAspectCrop
        }
        Column {
            anchors.centerIn: parent
            width: parent.width * 0.78
            spacing: 18
            Text {
                text: glyph
                font.pixelSize: 64
                color: "#ffffff"
                anchors.horizontalCenter: parent.horizontalCenter
            }
            Text {
                text: title
                font.pixelSize: 30
                font.weight: Font.DemiBold
                color: "#ffffff"
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
            }
            Text {
                text: body
                font.pixelSize: 17
                color: "#d6d9f0"
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                lineHeight: 1.25
            }
        }
    }

    InfoSlide {
        glyph: "👋"
        title: "Добро пожаловать в AIsktagOS"
        body: "Удобство macOS, свобода Linux Mint и мощь Ubuntu LTS — в одной системе. Установка займёт 5–15 минут."
    }
    InfoSlide {
        glyph: "⌘"
        title: "Привычный интерфейс"
        body: "Строка меню сверху, док снизу, поиск по Meta+Space (как Spotlight), обзор окон — Meta+W или угол экрана слева снизу."
    }
    InfoSlide {
        glyph: "</>"
        title: "Готова к разработке сразу"
        body: "VS Code, Git, Docker и Podman, Python, Node.js, Rust, компиляторы C/C++, терминал kitty с zsh и подсказками — всё уже установлено."
    }
    InfoSlide {
        glyph: "🎮"
        title: "Любая видеокарта"
        body: "AMD и Intel работают сразу. Для NVIDIA откройте «Менеджер драйверов» — он предложит нужный драйвер в один клик."
    }
    InfoSlide {
        glyph: "⏪"
        title: "Обновления без страха"
        body: "Перед каждым обновлением создаётся снимок системы. Если что-то пошло не так — откат в Timeshift за минуту."
    }
    InfoSlide {
        glyph: "🛍"
        title: "Тысячи приложений"
        body: "Центр приложений Discover: пакеты Ubuntu и магазин Flathub — Telegram, Spotify, Slack, JetBrains, OBS и многое другое."
    }
}
