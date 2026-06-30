@echo off
chcp 65001 >nul
echo === Ciné Canicule ===

python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR : Python n'est pas installe ou n'est pas dans le PATH.
    echo Installez Python depuis https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Installation des dependances...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERREUR : Installation des dependances a echoue.
    pause
    exit /b 1
)

echo Demarrage du serveur sur http://localhost:5000 ...
python app.py
