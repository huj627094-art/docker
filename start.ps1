﻿# Запуск «Подземки» на любом компьютере с Docker Desktop.
# - запускает Docker, если он не запущен;
# - при первом запуске создаёт .env со случайными паролями (если .env уже есть — берёт его);
# - восстанавливает данные из data/*.tar.gz (их кладёт pack.ps1), если томов ещё нет;
# - если порт сайта занят чужой программой — переключает сайт на 8080;
# - поднимает стек и один раз настраивает Umami (пароль admin, сайт, Website ID в .env).
# Повторный запуск безопасен.

Set-Location $PSScriptRoot

$Project = "podzemka"   # совпадает с name: в docker-compose.yml
$Utf8NoBom = New-Object Text.UTF8Encoding $false

function Test-Docker {
    # через cmd: в PowerShell 5.1 перенаправление stderr внешней программы превращается в ошибку
    cmd /c "docker info >nul 2>&1"
    return $LASTEXITCODE -eq 0
}

function New-Secret([int]$Length = 64) {
    $bytes = New-Object byte[] 32
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    return (-join ($bytes | ForEach-Object { $_.ToString("x2") })).Substring(0, $Length)
}

function Get-EnvValue($Name) {
    $line = Get-Content .env -Encoding UTF8 | Where-Object { $_ -like "$Name=*" } | Select-Object -First 1
    if ($line) { return $line.Substring($Name.Length + 1) }
}

# Записывает .env: берёт строки из $Source, заменяет значения из $Values, недостающие ключи дописывает в конец
function Write-EnvFile($Source, $Values) {
    $left = @{} + $Values
    $lines = @(Get-Content $Source -Encoding UTF8 | ForEach-Object {
        if ($_ -match '^([A-Z_]+)=' -and $left.ContainsKey($Matches[1])) {
            "$($Matches[1])=$($left[$Matches[1]])"
            $left.Remove($Matches[1])
        } else { $_ }
    })
    $lines += $left.Keys | ForEach-Object { "$_=$($left[$_])" }
    # Без BOM: иначе docker compose прочитает имя первой переменной с мусором
    [IO.File]::WriteAllLines("$PSScriptRoot\.env", [string[]]$lines, $Utf8NoBom)
}

function Test-Volume($Name) {
    return [bool](docker volume ls -q --filter "name=^$Name$")
}

function Invoke-Umami($Path, $Token, $Body) {
    $headers = @{}
    if ($Token) { $headers.Authorization = "Bearer $Token" }
    # байты, а не строка: PowerShell 5.1 иначе отправит кириллицу не в UTF-8
    $bytes = [Text.Encoding]::UTF8.GetBytes(($Body | ConvertTo-Json -Compress))
    return Invoke-RestMethod -Method Post -Uri "http://localhost:3000$Path" -Headers $headers `
        -ContentType "application/json; charset=utf-8" -Body $bytes
}

function Get-UmamiToken($Password) {
    try { return (Invoke-Umami "/api/auth/login" $null @{ username = "admin"; password = $Password }).token }
    catch { return $null }
}

function Assert-Ok($Message) {
    if ($LASTEXITCODE -ne 0) { throw $Message }
}

# --- 1. Docker ---
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker не установлен. Скачайте Docker Desktop: https://www.docker.com/products/docker-desktop/"
}
if (-not (Test-Docker)) {
    $desktop = "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $desktop) {
        Write-Host "-> Запускаю Docker Desktop (первый старт может занять пару минут)..."
        Start-Process $desktop
    }
    for ($i = 0; $i -lt 60 -and -not (Test-Docker); $i++) { Start-Sleep -Seconds 5 }
    if (-not (Test-Docker)) { throw "Docker не отвечает. Запустите Docker Desktop вручную и повторите." }
}

# --- 2. .env ---
if (-not (Test-Path .env)) {
    # База уже создавалась с паролем из старого .env — новый пароль к ней не подойдёт
    if (Test-Volume "${Project}_pgdata") {
        throw "Нет .env, но база ${Project}_pgdata уже есть. Верните старый .env или удалите данные: docker compose down -v"
    }
    Write-Host "-> Создаю .env со случайными паролями"
    Write-EnvFile .env.example @{
        DJANGO_SECRET_KEY      = New-Secret
        DJANGO_ADMIN_PASSWORD  = New-Secret 16
        POSTGRES_PASSWORD      = New-Secret
        UMAMI_DB_PASSWORD      = New-Secret
        UMAMI_APP_SECRET       = New-Secret
        UMAMI_ADMIN_PASSWORD   = New-Secret 16
        GRAFANA_ADMIN_PASSWORD = New-Secret 16
    }
}

# --- 3. Данные с другого компьютера ---
foreach ($archive in Get-ChildItem data -Filter *.tar.gz -ErrorAction SilentlyContinue) {
    $name = $archive.Name -replace '\.tar\.gz$', ''
    $volume = "${Project}_$name"
    if (Test-Volume $volume) { continue }   # данные уже есть — не затираем
    Write-Host "-> Восстанавливаю данные: $volume"
    # метки — чтобы compose считал том своим и не ругался
    docker volume create --label "com.docker.compose.project=$Project" --label "com.docker.compose.volume=$name" $volume | Out-Null
    # postgres:17-alpine всё равно нужен стеку, отдельный образ для tar не качаем
    docker run --rm -v "${volume}:/v" -v "$PSScriptRoot\data:/b:ro" postgres:17-alpine tar xzf "/b/$($archive.Name)" -C /v
    Assert-Ok "Не удалось восстановить $volume"
}

# --- 4. Порт сайта ---
$port = Get-EnvValue SITE_PORT
if (-not $port) { $port = "80" }   # .env из старой версии, без SITE_PORT
$ours = docker compose ps -q --status running nginx
if (-not $ours -and (Get-NetTCPConnection -LocalPort ([int]$port) -State Listen -ErrorAction SilentlyContinue)) {
    Write-Host "-> Порт $port занят другой программой, сайт будет на 8080"
    $port = "8080"
    Write-EnvFile .env @{ SITE_PORT = $port; DJANGO_CSRF_TRUSTED_ORIGINS = "http://localhost:$port,http://127.0.0.1:$port" }
}

# --- 5. Стек ---
Write-Host "-> Собираю и запускаю контейнеры (первый раз — несколько минут)"
docker compose up -d --build --wait
Assert-Ok "docker compose up завершился с ошибкой — смотрите вывод выше и 'docker compose logs web'"

# --- 6. Umami: один раз, пока в .env нет Website ID ---
if (-not (Get-EnvValue UMAMI_WEBSITE_ID)) {
    Write-Host "-> Настраиваю Umami"
    $password = Get-EnvValue UMAMI_ADMIN_PASSWORD
    if (-not $password) { $password = New-Secret 16 }
    $token = Get-UmamiToken $password
    if (-not $token) {
        # свежий Umami со стандартным паролем — сразу меняем
        $token = Get-UmamiToken "umami"
        if (-not $token) { throw "Не удалось войти в Umami: проверьте UMAMI_ADMIN_PASSWORD в .env" }
        Invoke-Umami "/api/me/password" $token @{ currentPassword = "umami"; newPassword = $password } | Out-Null
    }
    Write-EnvFile .env @{ UMAMI_ADMIN_PASSWORD = $password }
    $website = Invoke-Umami "/api/websites" $token @{ name = "Подземка"; domain = "localhost" }
    Write-EnvFile .env @{ UMAMI_WEBSITE_ID = $website.id }
    # web — чтобы подхватил ID; nginx — чтобы заново нашёл адрес пересозданного web
    docker compose up -d --wait --force-recreate web nginx
    Assert-Ok "Не удалось перезапустить сайт после настройки Umami"
}

$site = if ($port -eq "80") { "http://localhost" } else { "http://localhost:$port" }
Write-Host ""
Write-Host "Готово."
Write-Host "  Сайт:    $site"
Write-Host "  Админка: $site/admin/   admin / $(Get-EnvValue DJANGO_ADMIN_PASSWORD)"
Write-Host "  Umami:   http://localhost:3000   admin / $(Get-EnvValue UMAMI_ADMIN_PASSWORD)"
Write-Host "  Grafana: http://localhost:3001   admin / $(Get-EnvValue GRAFANA_ADMIN_PASSWORD)"
Write-Host "Остановить: docker compose down   (данные сохранятся)"
Write-Host "Упаковать для другого компьютера: pack.bat"
