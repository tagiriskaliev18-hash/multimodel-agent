// DuoOS: строка меню сверху + плавающий док снизу (в духе macOS)

// ---- Строка меню ----------------------------------------------------------
var menuBar = new Panel;
menuBar.location = "top";
menuBar.height = Math.round(gridUnit * 1.6);
menuBar.floating = false;
menuBar.hiding = "none";

// Меню системы с логотипом DuoOS (аналог меню «яблока»)
var menu = menuBar.addWidget("org.kde.plasma.kickoff");
menu.currentConfigGroup = ["General"];
menu.writeConfig("icon", "duoos-logo-symbolic");
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

var tasks = dock.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", [
    "applications:org.kde.dolphin.desktop",
    "applications:firefox.desktop",
    "applications:org.kde.falkon.desktop",
    "applications:kitty.desktop",
    "applications:code.desktop",
    "applications:org.kde.kate.desktop",
    "applications:org.kde.discover.desktop",
    "applications:duo-welcome.desktop",
    "applications:systemsettings.desktop"
]);
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
    d.writeConfig("Image", "file:///usr/share/wallpapers/DuoOS/");
}
