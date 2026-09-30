#Requires -Version 5.1
<#
.SYNOPSIS
    Сборка ISO AIsktagOS на Windows через WSL 2 (Ubuntu). Результат — в %USERPROFILE%\AIsktagOS.

.DESCRIPTION
    Нужны: Windows 10 2004+ или Windows 11, включённая виртуализация, ~40 ГБ свободного места,
    интернет. Сборка идёт 40–90 минут. Если WSL ещё не установлен, скрипт установит его
    (понадобятся права администратора и, возможно, перезагрузка — затем запустите скрипт снова).

    Запуск: двойной щелчок по Build-AIsktagOS-ISO.bat, лежащему в папке tools\windows репозитория.
#>
[CmdletBinding()]
param(
    [string]$Distro = 'Ubuntu-24.04'
)

$ErrorActionPreference = 'Continue'
$OutDir = Join-Path $env:USERPROFILE 'AIsktagOS'

function Say([string]$Text) { Write-Host "==> $Text" -ForegroundColor Cyan }
function Fail([string]$Text) { Write-Host "Ошибка: $Text" -ForegroundColor Red; exit 1 }

# Корень репозитория: две папки выше tools\windows
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
if (-not (Test-Path (Join-Path $RepoRoot 'build.sh'))) {
    Fail "Не найден build.sh в $RepoRoot. Запускайте скрипт из папки tools\windows репозитория AIsktagOS."
}

if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    Fail 'WSL недоступен в этой версии Windows. Нужна Windows 10 2004+ или Windows 11.'
}

$installed = (wsl.exe --list --quiet 2>$null) -replace "`0", '' | Where-Object { $_.Trim() -eq $Distro }
if (-not $installed) {
    Say "Устанавливаю WSL и $Distro (понадобятся права администратора)…"
    Start-Process wsl.exe -ArgumentList "--install -d $Distro" -Verb RunAs -Wait
    Write-Host ''
    Write-Host "Если Windows попросит перезагрузку — перезагрузитесь. Откройте «$Distro» из меню Пуск," -ForegroundColor Yellow
    Write-Host 'создайте пользователя Linux, затем запустите этот скрипт снова.' -ForegroundColor Yellow
    exit 0
}

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$repoWsl = (wsl.exe -d $Distro -- wslpath -a "$RepoRoot").Trim()
$outWsl = (wsl.exe -d $Distro -- wslpath -a "$OutDir").Trim()

Say "Репозиторий: $RepoRoot"
Say "ISO появится в: $OutDir"
Say 'Устанавливаю инструменты сборки в WSL (введите пароль пользователя Linux, если попросят)…'
wsl.exe -d $Distro -- sudo apt-get update
wsl.exe -d $Distro -- sudo apt-get install -y debootstrap squashfs-tools xorriso grub-pc-bin grub-efi-amd64-bin mtools dosfstools
if ($LASTEXITCODE -ne 0) { Fail 'не удалось установить инструменты сборки в WSL.' }

Say 'Собираю AIsktagOS. Это 40–90 минут — окно можно свернуть.'
# Рабочий каталог — внутри файловой системы WSL: на дисках Windows chroot и сборка не работают
wsl.exe -d $Distro -- sudo env WORK_DIR=/var/tmp/aisktagos-work "OUT_DIR=$outWsl" bash "$repoWsl/build.sh"
if ($LASTEXITCODE -ne 0) { Fail 'сборка завершилась с ошибкой — пролистайте журнал выше.' }

$iso = Get-ChildItem -Path $OutDir -Filter 'aisktagos-*.iso' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $iso) { Fail "ISO не найден в $OutDir" }
Say "Готово: $($iso.FullName) ($([math]::Round($iso.Length / 1GB, 2)) ГБ)"
Write-Host 'Теперь запустите Install-AIsktagOS-VM.bat — он найдёт этот образ и создаст виртуальную машину.' -ForegroundColor Green
