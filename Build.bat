@echo off
echo 🏗️ Construyendo SyncDesk Manager...
pyinstaller --onefile --name "SyncDeskManager" --add-data "data;data" --hidden-import=src run.py

echo 📦 Creando paquete de release...
if exist release-package rmdir /s /q release-package
mkdir release-package
copy dist\SyncDeskManager.exe release-package\
copy README.md release-package\README_Usuario.md

echo 📁 Copiando estructura de datos...
xcopy data release-package\data /E /I /Y

echo 🗜️ Comprimiendo...
if exist "SyncDeskManager-v1.0.0.zip" del "SyncDeskManager-v1.0.0.zip"
"C:\Program Files\7-Zip\7z.exe" a -tzip "SyncDeskManager-v1.0.0.zip" "release-package\*"

echo.
echo ✅ PAQUETE LISTO: SyncDeskManager-v1.0.0.zip
echo 📁 Contenido del paquete:
dir release-package
echo.
echo 📋 Proximo paso: Subir "SyncDeskManager-v1.0.0.zip" a GitHub Releases
pause