#Requires -Version 5.1
<#
.SYNOPSIS
    Виртуальная станция AIsktagOS для Windows: ставит VirtualBox, создаёт ВМ и ярлык на рабочем столе.

.DESCRIPTION
    1. Устанавливает VirtualBox (бесплатный) через winget, если его ещё нет.
    2. Находит ISO AIsktagOS: параметр -IsoPath, папка %USERPROFILE%\AIsktagOS, «Загрузки»,
       затем GitHub Releases; если ничего не найдено — предлагает выбрать файл.
    3. Создаёт ВМ «AIsktagOS»: UEFI, 3D-ускорение, диск 60 ГБ, общий буфер обмена.
    4. Кладёт на рабочий стол ярлыки «AIsktagOS VM» и «AIsktagOS VM — извлечь ISO».
    5. Запускает ВМ. В меню загрузки выберите «Установить AIsktagOS».

    Запуск: двойной щелчок по Install-AIsktagOS-VM.bat (или из PowerShell):
        powershell -ExecutionPolicy Bypass -File .\Install-AIsktagOS-VM.ps1
        powershell -ExecutionPolicy Bypass -File .\Install-AIsktagOS-VM.ps1 -IsoPath D:\aisktagos-1.0-amd64.iso
#>
[CmdletBinding()]
param(
    [string]$IsoPath = "",
    [int]$MemoryMB = 0,
    [int]$Cpus = 0,
    [int]$DiskGB = 60,
    [switch]$Recreate,
    [switch]$EjectIso
)

# Continue: в Windows PowerShell 5.1 режим Stop превращает любой вывод VBoxManage в stderr
# в фатальную ошибку. Коды возврата проверяются явно.
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
$VmName = 'AIsktagOS'
$Repo = 'tagiriskaliev18-hash/aisktagos'
$BaseDir = Join-Path $env:USERPROFILE 'AIsktagOS'

function Say([string]$Text) { Write-Host "==> $Text" -ForegroundColor Cyan }
function Warn([string]$Text) { Write-Host "ВНИМАНИЕ: $Text" -ForegroundColor Yellow }
function Fail([string]$Text) { Write-Host "Ошибка: $Text" -ForegroundColor Red; exit 1 }

# ---------------------------------------------------------------- VirtualBox --
function Find-VBoxManage {
    $candidates = @()
    if ($env:VBOX_MSI_INSTALL_PATH) { $candidates += (Join-Path $env:VBOX_MSI_INSTALL_PATH 'VBoxManage.exe') }
    $candidates += (Join-Path $env:ProgramFiles 'Oracle\VirtualBox\VBoxManage.exe')
    foreach ($c in $candidates) { if (Test-Path $c) { return $c } }
    $cmd = Get-Command VBoxManage.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

function Install-VirtualBox {
    Say 'Устанавливаю VirtualBox (бесплатный гипервизор Oracle)…'
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Start-Process 'https://www.virtualbox.org/wiki/Downloads'
        Fail 'winget не найден. Скачайте «Windows hosts» на открывшейся странице, установите VirtualBox и запустите этот скрипт снова.'
    }
    # Библиотеки Visual C++ нужны VirtualBox 7.x
    winget install --id Microsoft.VCRedist.2015+.x64 -e --silent --accept-package-agreements --accept-source-agreements | Out-Null
    winget install --id Oracle.VirtualBox -e --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0 -and -not (Find-VBoxManage)) {
        Fail 'VirtualBox не установился. Установите его вручную: https://www.virtualbox.org/wiki/Downloads'
    }
}

# ----------------------------------------------------------------------- ISO --
function Find-LocalIso {
    $dirs = @($BaseDir, (Join-Path $env:USERPROFILE 'Downloads'), (Join-Path $env:USERPROFILE 'Desktop'),
              [Environment]::GetFolderPath('Desktop'), $PSScriptRoot)
    foreach ($d in $dirs) {
        if (-not $d -or -not (Test-Path $d)) { continue }
        $iso = Get-ChildItem -Path $d -Filter 'aisktagos-*.iso' -File -ErrorAction SilentlyContinue |
               Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($iso) { return $iso.FullName }
    }
    return $null
}

function Save-Url([string]$Url, [string]$Dest) {
    try {
        Start-BitsTransfer -Source $Url -Destination $Dest -DisplayName 'AIsktagOS ISO' -Description $Url -ErrorAction Stop
    } catch {
        Invoke-WebRequest -Uri $Url -OutFile $Dest -UseBasicParsing -ErrorAction Stop
    }
}

function Get-IsoFromGitHub {
    Say "Ищу готовый образ в GitHub Releases ($Repo)…"
    try {
        $rel = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/releases/latest" -UseBasicParsing -ErrorAction Stop
    } catch {
        Warn 'Релиз на GitHub не найден (репозиторий закрыт или ещё не опубликован).'
        return $null
    }
    New-Item -ItemType Directory -Force -Path $BaseDir | Out-Null
    $isoAsset = $rel.assets | Where-Object { $_.name -like '*.iso' } | Select-Object -First 1
    $parts = @($rel.assets | Where-Object { $_.name -match '\.iso\.part\d+$' } | Sort-Object name)
    if ($isoAsset) {
        $dest = Join-Path $BaseDir $isoAsset.name
        Say "Скачиваю $($isoAsset.name) ($([math]::Round($isoAsset.size / 1GB, 2)) ГБ)…"
        Save-Url $isoAsset.browser_download_url $dest
        return $dest
    }
    if ($parts.Count -gt 0) {
        $isoName = $parts[0].name -replace '\.part\d+$', ''
        $dest = Join-Path $BaseDir $isoName
        $out = [System.IO.File]::Create($dest)
        try {
            foreach ($p in $parts) {
                $tmp = Join-Path $BaseDir $p.name
                Say "Скачиваю $($p.name)…"
                Save-Url $p.browser_download_url $tmp
                $in = [System.IO.File]::OpenRead($tmp)
                try { $in.CopyTo($out) } finally { $in.Close() }
                Remove-Item $tmp
            }
        } finally { $out.Close() }
        return $dest
    }
    Warn 'В релизе нет файла ISO.'
    return $null
}

function Select-IsoDialog {
    Add-Type -AssemblyName System.Windows.Forms
    $dlg = New-Object System.Windows.Forms.OpenFileDialog
    $dlg.Title = 'Выберите образ AIsktagOS (.iso)'
    $dlg.Filter = 'Образ диска (*.iso)|*.iso'
    $dlg.InitialDirectory = (Join-Path $env:USERPROFILE 'Downloads')
    if ($dlg.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $dlg.FileName }
    return $null
}

function Test-IsoChecksum([string]$Iso) {
    $sumFile = "$Iso.sha256"
    if (-not (Test-Path $sumFile)) { return }
    $expected = ((Get-Content $sumFile -Raw).Trim() -split '\s+')[0].ToLower()
    Say 'Проверяю контрольную сумму образа…'
    $actual = (Get-FileHash -Path $Iso -Algorithm SHA256).Hash.ToLower()
    if ($actual -ne $expected) { Fail "Образ повреждён (SHA256 не совпадает). Скачайте его заново: $Iso" }
    Say 'Контрольная сумма совпадает.'
}

# ------------------------------------------------------------------------ VM --
function Invoke-VBox([string[]]$VBoxArgs, [switch]$Optional) {
    & $script:VBox @VBoxArgs 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        if ($Optional) { Warn "не удалось: VBoxManage $($VBoxArgs -join ' ')" }
        else { Fail "VBoxManage $($VBoxArgs -join ' ')" }
    }
}

function Test-VmExists {
    & $script:VBox showvminfo $VmName --machinereadable 2>&1 | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function New-AIsktagVm([string]$Iso) {
    $ramMB = [int]((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1MB)
    if ($MemoryMB -le 0) { $script:MemoryMB = [math]::Max(4096, [math]::Min(8192, [int]($ramMB / 2))) }
    if ($Cpus -le 0) { $script:Cpus = [math]::Max(2, [math]::Min(6, [int]([Environment]::ProcessorCount / 2))) }
    Say "Создаю ВМ «$VmName»: $($script:MemoryMB) МБ ОЗУ, $($script:Cpus) ядер, диск $DiskGB ГБ, UEFI"

    Invoke-VBox @('createvm', '--name', $VmName, '--ostype', 'Ubuntu_64', '--register', '--basefolder', $BaseDir)
    Invoke-VBox @('modifyvm', $VmName, '--memory', "$($script:MemoryMB)", '--cpus', "$($script:Cpus)",
                  '--firmware', 'efi', '--graphicscontroller', 'vmsvga', '--vram', '128', '--nic1', 'nat',
                  '--rtcuseutc', 'on', '--boot1', 'disk', '--boot2', 'dvd', '--boot3', 'none', '--boot4', 'none')
    # Необязательные удобства (названия ключей различаются между версиями VirtualBox)
    foreach ($opt in @(@('--accelerate-3d', 'on'), @('--accelerate3d', 'on'),
                       @('--clipboard-mode', 'bidirectional'), @('--draganddrop', 'bidirectional'),
                       @('--mouse', 'usbtablet'), @('--audio-enabled', 'on'), @('--audio-out', 'on'))) {
        & $script:VBox modifyvm $VmName @opt 2>&1 | Out-Null
    }

    $vdi = Join-Path (Join-Path $BaseDir $VmName) "$VmName.vdi"
    Invoke-VBox @('createmedium', 'disk', '--filename', $vdi, '--size', "$($DiskGB * 1024)", '--format', 'VDI')
    Invoke-VBox @('storagectl', $VmName, '--name', 'SATA', '--add', 'sata', '--controller', 'IntelAhci',
                  '--portcount', '2', '--bootable', 'on')
    Invoke-VBox @('storageattach', $VmName, '--storagectl', 'SATA', '--port', '0', '--device', '0',
                  '--type', 'hdd', '--medium', $vdi)
    Invoke-VBox @('storageattach', $VmName, '--storagectl', 'SATA', '--port', '1', '--device', '0',
                  '--type', 'dvddrive', '--medium', $Iso)
}

function New-DesktopShortcuts {
    $desktop = [Environment]::GetFolderPath('Desktop')
    $shell = New-Object -ComObject WScript.Shell
    $icon = Join-Path (Split-Path $script:VBox) 'VirtualBox.exe'

    $lnk = $shell.CreateShortcut((Join-Path $desktop 'AIsktagOS VM.lnk'))
    $lnk.TargetPath = $script:VBox
    $lnk.Arguments = "startvm `"$VmName`" --type gui"
    $lnk.WorkingDirectory = $BaseDir
    $lnk.Description = 'Запустить виртуальную машину AIsktagOS'
    if (Test-Path $icon) { $lnk.IconLocation = "$icon,0" }
    $lnk.Save()

    $ps = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $lnk2 = $shell.CreateShortcut((Join-Path $desktop 'AIsktagOS VM — извлечь ISO.lnk'))
    $lnk2.TargetPath = $ps
    $lnk2.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -EjectIso"
    $lnk2.Description = 'Извлечь установочный ISO после установки AIsktagOS'
    $lnk2.Save()
    Say "Ярлыки на рабочем столе: «AIsktagOS VM» и «AIsktagOS VM — извлечь ISO»"
}

# ------------------------------------------------------------------ Основное --
Write-Host ''
Write-Host '  AIsktagOS — виртуальная станция' -ForegroundColor Magenta
Write-Host ''

$script:VBox = Find-VBoxManage
if (-not $script:VBox) {
    Install-VirtualBox
    $script:VBox = Find-VBoxManage
    if (-not $script:VBox) { Fail 'VBoxManage.exe не найден после установки. Перезагрузите компьютер и запустите скрипт снова.' }
}
Say "VirtualBox: $script:VBox"

if ($EjectIso) {
    Invoke-VBox @('storageattach', $VmName, '--storagectl', 'SATA', '--port', '1', '--device', '0',
                  '--type', 'dvddrive', '--medium', 'emptydrive')
    Say 'ISO извлечён. Теперь ВМ загружается с установленной системы.'
    exit 0
}

if ((Test-VmExists) -and -not $Recreate) {
    Say "ВМ «$VmName» уже есть — запускаю её. Чтобы пересоздать: параметр -Recreate"
    New-DesktopShortcuts
    & $script:VBox startvm $VmName --type gui
    exit 0
}
if ((Test-VmExists) -and $Recreate) {
    Say "Удаляю старую ВМ «$VmName»…"
    & $script:VBox controlvm $VmName poweroff 2>&1 | Out-Null
    Start-Sleep -Seconds 2
    Invoke-VBox @('unregistervm', $VmName, '--delete')
}

if (-not $IsoPath) { $IsoPath = Find-LocalIso }
if (-not $IsoPath) { $IsoPath = Get-IsoFromGitHub }
if (-not $IsoPath) {
    Say 'Выберите файл образа AIsktagOS…'
    $IsoPath = Select-IsoDialog
}
if (-not $IsoPath -or -not (Test-Path $IsoPath)) { Fail 'Образ AIsktagOS (.iso) не выбран.' }
$IsoPath = (Resolve-Path $IsoPath).Path
Say "Образ: $IsoPath"
Test-IsoChecksum $IsoPath

New-Item -ItemType Directory -Force -Path $BaseDir | Out-Null
New-AIsktagVm $IsoPath
New-DesktopShortcuts

Say 'Запускаю ВМ. В меню загрузки выберите «Установить AIsktagOS».'
& $script:VBox startvm $VmName --type gui
Write-Host ''
Write-Host 'После установки нажмите ярлык «AIsktagOS VM — извлечь ISO», затем «AIsktagOS VM».' -ForegroundColor Green
