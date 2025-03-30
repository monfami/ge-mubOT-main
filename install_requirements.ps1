# スクリプトを実行するディレクトリに移動
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
cd $scriptPath

# venv仮想環境が存在しない場合は作成
if (-not (Test-Path ".\venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Green
    python -m venv venv
}

Write-Host "Activating virtual environment..." -ForegroundColor Green

# venv仮想環境を有効化（Windows用）
& .\venv\Scripts\Activate.ps1

# requirements.txtのパッケージをインストール
if (Test-Path ".\requirements.txt") {
    Write-Host "Installing packages from requirements.txt..." -ForegroundColor Green
    pip install -r requirements.txt
} else {
    Write-Host "requirements.txt not found." -ForegroundColor Red
    exit 1
}

Write-Host "Installation completed!" -ForegroundColor Green
Write-Host "To deactivate the virtual environment, run 'deactivate' command." -ForegroundColor Yellow
