$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venv = Join-Path $root '.venv'
$python = Join-Path $venv 'Scripts\python.exe'
$dist = Join-Path $root '便携版'
$work = Join-Path $root 'build_portable'

if (-not (Test-Path $python)) { throw "项目虚拟环境不存在: $python" }
New-Item -ItemType Directory -Force $dist | Out-Null
# 构建时只允许项目虚拟环境和 Windows 系统 DLL 路径，避免误收集外部 Qt/ICU。
$env:PATH = "$(Join-Path $venv 'Scripts');C:\Windows\System32;C:\Windows"
& $python -m PyInstaller --noconfirm --clean --onefile --windowed `
  --name '经文排版程序' --distpath $dist --workpath $work --specpath $work `
  --hidden-import psd_tools --hidden-import numpy (Join-Path $root 'main.py')
if ($LASTEXITCODE -ne 0) { throw "PyInstaller 构建失败，退出码 $LASTEXITCODE" }
Write-Host "已生成: $(Join-Path $dist '经文排版程序.exe')"
