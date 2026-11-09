# Упаковывает «Подземку» целиком для переноса на другой компьютер:
# код + .env + данные всех сервисов (база сайта и Umami, Grafana, Prometheus)
# -> podzemka.zip на рабочем столе. На другом компьютере: распаковать и запустить start.bat.

Set-Location $PSScriptRoot

$Project = "podzemka"   # совпадает с name: в docker-compose.yml
$Volumes = "pgdata", "grafana-data", "prometheus-data"

function Assert-Ok($Message) {
    if ($LASTEXITCODE -ne 0) { throw $Message }
}

if (-not (Test-Path .env)) { throw "Нет .env — сначала запустите start.bat" }

# --- 1. Данные: копия томов при остановленных контейнерах, иначе база может оказаться битой ---
Write-Host "-> Останавливаю контейнеры"
docker compose stop
Assert-Ok "Не удалось остановить контейнеры"
New-Item -ItemType Directory -Force data | Out-Null
try {
    foreach ($name in $Volumes) {
        Write-Host "-> Сохраняю данные: ${Project}_$name"
        # plugins — ~500 МБ плагинов Grafana, она сама скачает их заново при старте
        docker run --rm -v "${Project}_${name}:/v:ro" -v "$PSScriptRoot\data:/b" postgres:17-alpine tar czf "/b/$name.tar.gz" --exclude=./plugins -C /v .
        Assert-Ok "Не удалось сохранить ${Project}_$name"
    }
} finally {
    Write-Host "-> Запускаю контейнеры обратно"
    docker compose up -d --wait
}

# --- 2. Список файлов: всё, что видит git (без venv, staticfiles и т. п.), + .env, data, история .git ---
[Console]::OutputEncoding = [Text.Encoding]::UTF8   # кириллица в именах файлов
$files = @(git -c core.quotepath=off ls-files -co --exclude-standard)
Assert-Ok "git ls-files не сработал"
$files = @($files | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf })
$files += ".env"
$files += Get-ChildItem data -Filter *.tar.gz | ForEach-Object { "data/$($_.Name)" }
$root = (Resolve-Path .).Path
$files += Get-ChildItem .git -Recurse -File -Force | ForEach-Object { $_.FullName.Substring($root.Length + 1) }

# --- 3. Архив. .NET пишет кириллические имена в UTF-8 с флагом — Проводник и 7-Zip их понимают ---
Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
$zipPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "podzemka.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath }
$zip = [IO.Compression.ZipFile]::Open($zipPath, "Create")
try {
    foreach ($file in $files) {
        $entry = "podzemka/" + ($file -replace '\\', '/')
        [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, (Join-Path $root $file), $entry) | Out-Null
    }
} finally {
    $zip.Dispose()
}

$size = [math]::Round((Get-Item $zipPath).Length / 1MB, 1)
Write-Host ""
Write-Host "Готово: $zipPath ($size МБ, файлов: $($files.Count))"
Write-Host "Внутри пароли (.env) — передавайте архив только сами."
Write-Host "На другом компьютере: распаковать (Проводник или 7-Zip) и запустить start.bat"
