// AIsktagOS: строка меню сверху + плавающий док снизу (в духе macOS)

// ---- Строка меню ----------------------------------------------------------
var menuBar = new Panel;
menuBar.location = "top";
menuBar.height = Math.round(gridUnit * 1.6);
menuBar.floating = false;
menuBar.hiding = "none";

// Меню системы с логотипом AIsktagOS (аналог меню «яблока»)
var menu = menuBar.addWidget("org.kde.plasma.kickoff");
menu.currentConfigGroup = ["General"];
menu.writeConfig("icon", "aisktagos-logo-symbolic");
menu.writeConfig("favoritesPortedToKAstats", true);

// Глобальное меню активного приложения
menuBar.addWidget("org.kde.plasma.appmenu");
menuBar.addWidget("org.kde.plasma.panelspacer");
menuBar.addWidget("org.kde.plasma.systemtray");

var clock = menuBar.addWidget("org.kde.plasma.digitalclock");
clock.currentConfigGroup = ["Appearance"];
clock.writeConfig("showDate", true);
clock.writeConfig("dateDisplayFormat", "BesideTime");
clock.writeConfig("dateFormat", "shortDate");

// ---- Док ------------------------------------------------------------------
var dock = new Panel;
dock.location = "bottom";
dock.height = Math.round(gridUnit * 3.4);
dock.floating = true;
dock.alignment = "center";
dock.lengthMode = "fit";
dock.hiding = "dodgewindows";

// Все приложения на весь экран (аналог Launchpad)
var launchpad = dock.addWidget("org.kde.plasma.kickerdash");
launchpad.currentConfigGroup = ["General"];
launchpad.writeConfig("icon", "view-app-grid-symbolic");

// Для каждого места в доке — варианты по порядку; берётся первый установленный
var dockApps = [
    ["org.kde.dolphin.desktop"],
    ["firefox.desktop", "org.mozilla.firefox.desktop", "org.kde.falkon.desktop"],
    ["kitty.desktop", "org.kde.konsole.desktop"],
    ["com.microsoft.VSCode.desktop", "code.desktop", "org.kde.kate.desktop"],
    ["org.kde.discover.desktop"],
    ["aisktag-welcome.desktop"],
    ["systemsettings.desktop"]
];
var launchers = [];
for (var a = 0; a < dockApps.length; a++) {
    for (var b = 0; b < dockApps[a].length; b++) {
        if (applicationExists(dockApps[a][b])) {
            launchers.push("applications:" + dockApps[a][b]);
            break;
        }
    }
}

var tasks = dock.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", launchers);
tasks.writeConfig("indicateAudioStreams", true);
tasks.writeConfig("iconSpacing", 2);

dock.addWidget("org.kde.plasma.marginsseparator");
dock.addWidget("org.kde.plasma.trash");

// ---- Обои -----------------------------------------------------------------
var desktopsArray = desktopsForActivity(currentActivity());
for (var j = 0; j < desktopsArray.length; j++) {
    var d = desktopsArray[j];
    d.wallpaperPlugin = "org.kde.image";
    d.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    d.writeConfig("Image", "file:///usr/share/wallpapers/AIsktagOS/");
}
