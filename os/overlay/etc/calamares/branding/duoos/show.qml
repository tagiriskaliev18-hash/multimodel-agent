// Слайды, которые показываются во время копирования файлов
import QtQuick 2.0
import calamares.slideshow 1.0

Presentation {
    id: presentation

    Timer {
        interval: 9000
        running: true
        repeat: true
        onTriggered: presentation.goToNextSlide()
    }

    component DuoSlide: Slide {
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

    DuoSlide {
        glyph: "👋"
        title: "Добро пожаловать в DuoOS"
        body: "Удобство macOS, свобода Linux Mint и мощь Ubuntu LTS — в одной системе. Установка займёт 5–15 минут."
    }
    DuoSlide {
        glyph: "⌘"
        title: "Привычный интерфейс"
        body: "Строка меню сверху, док снизу, поиск по Meta+Space (как Spotlight), обзор окон — Meta+W или угол экрана слева снизу."
    }
    DuoSlide {
        glyph: "</>"
        title: "Готова к разработке сразу"
        body: "VS Code, Git, Docker и Podman, Python, Node.js, Rust, компиляторы C/C++, терминал kitty с zsh и подсказками — всё уже установлено."
    }
    DuoSlide {
        glyph: "🎮"
        title: "Любая видеокарта"
        body: "AMD и Intel работают сразу. Для NVIDIA откройте «Менеджер драйверов» — он предложит нужный драйвер в один клик."
    }
    DuoSlide {
        glyph: "⏪"
        title: "Обновления без страха"
        body: "Перед каждым обновлением создаётся снимок системы. Если что-то пошло не так — откат в Timeshift за минуту."
    }
    DuoSlide {
        glyph: "🛍"
        title: "Тысячи приложений"
        body: "Центр приложений Discover: пакеты Ubuntu и магазин Flathub — Telegram, Spotify, Slack, JetBrains, OBS и многое другое."
    }
}
