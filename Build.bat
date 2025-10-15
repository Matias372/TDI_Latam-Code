@echo off
echo 🏗️ Construyendo SyncDesk Manager...
echo.

:: Limpiar builds anteriores
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

:: Verificar que run.py existe
if not exist "run.py" (
    echo ❌ ERROR: No se encuentra run.py
    echo 💡 Asegúrate de ejecutar este script desde la raíz del proyecto
    pause
    exit /b 1
)

:: Verificar estructura de carpetas
echo 📁 Verificando estructura del proyecto...
if not exist "src" (
    echo ❌ ERROR: No se encuentra la carpeta src/
    pause
    exit /b 1
)

echo ✅ Estructura verificada
echo.

:: Construir con PyInstaller - ENFOQUE SIMPLIFICADO
echo 🔄 Ejecutando PyInstaller (esto puede tomar unos minutos)...
pyinstaller --onefile ^
 --name "SyncDeskManager" ^
 --add-data "data;data" ^
 --hidden-import=src.main ^
 --hidden-import=src.menus.main_menu ^
 --hidden-import=src.utils.logger ^
 --hidden-import=src.utils.file_utils ^
 --hidden-import=src.utils.validation_utils ^
 --hidden-import=src.utils.template_manager ^
 --hidden-import=src.utils.api_utils ^
 --hidden-import=src.utils.display_utils ^
 --hidden-import=src.services.freshdesk_service ^
 --hidden-import=src.services.clarity_service ^
 --hidden-import=src.features.processes ^
 --hidden-import=src.features.reports ^
 --hidden-import=src.features.sync_processes ^
 --hidden-import=src.features.guide ^
 --hidden-import=src.config.config_manager ^
 --hidden-import=src.config.state_mapping ^
 --hidden-import=src.config.constants ^
 --log-level=INFO ^
 run.py

:: Verificar resultado
if not exist "dist\SyncDeskManager.exe" (
    echo.
    echo ❌ ERROR: PyInstaller no generó el ejecutable
    echo 📋 Posibles soluciones:
    echo   1. Ejecutar en terminal normal (no como admin)
    echo   2. Verificar que todos los módulos importen correctamente
    echo   3. Probar enfoque alternativo (ver abajo)
    echo.
    echo 🛠️  Probando enfoque alternativo...
    goto :ALTERNATIVE_BUILD
)

echo ✅ Ejecutable generado: dist\SyncDeskManager.exe
goto :CREATE_PACKAGE

:ALTERNATIVE_BUILD
echo.
echo 🛠️  Intentando enfoque alternativo...
:: Enfoque más simple - sin --onefile primero
pyinstaller --name "SyncDeskManager" --add-data "data;data" run.py

if not exist "dist\SyncDeskManager\SyncDeskManager.exe" (
    echo ❌ Enfoque alternativo también falló
    echo 💡 Revisa los mensajes de error de PyInstaller arriba
    pause
    exit /b 1
)

echo ✅ Ejecutable generado (en carpeta): dist\SyncDeskManager\SyncDeskManager.exe
echo 💡 Usando versión en carpeta para el package...

:CREATE_PACKAGE
echo.
echo 📦 Creando paquete de release...
if exist release-package rmdir /s /q release-package
mkdir release-package

:: Copiar ejecutable (dependiendo de si es --onefile o no)
if exist "dist\SyncDeskManager.exe" (
    copy "dist\SyncDeskManager.exe" "release-package\"
) else if exist "dist\SyncDeskManager\SyncDeskManager.exe" (
    copy "dist\SyncDeskManager\SyncDeskManager.exe" "release-package\SyncDeskManager.exe"
    :: Copiar también las DLLs y dependencias si existen
    if exist "dist\SyncDeskManager\*.dll" copy "dist\SyncDeskManager\*.dll" "release-package\"
) else (
    echo ❌ ERROR: No se encuentra el ejecutable en ninguna ubicación
    pause
    exit /b 1
)

:: Verificar que se copió
if not exist "release-package\SyncDeskManager.exe" (
    echo ❌ ERROR: No se pudo copiar el ejecutable al package
    pause
    exit /b 1
)

echo ✅ Ejecutable copiado al package

:: Copiar README
if exist "README.md" (
    copy "README.md" "release-package\README_Usuario.md"
    echo ✅ README copiado
) else (
    echo ⚠️  Advertencia: No se encontró README.md
)

echo 📁 Copiando estructura de datos...
if exist "data" (
    xcopy "data" "release-package\data" /E /I /Y
    echo ✅ Estructura de datos copiada
) else (
    echo ❌ ERROR: No se encuentra la carpeta data
    pause
    exit /b 1
)

echo 🗜️ Comprimiendo...
if exist "SyncDeskManager-v1.0.0.zip" del "SyncDeskManager-v1.0.0.zip"

:: Comprimir
if exist "C:\Program Files\7-Zip\7z.exe" (
    "C:\Program Files\7-Zip\7z.exe" a -tzip "SyncDeskManager-v1.0.0.zip" "release-package\*"
) else (
    echo ⚠️  7-Zip no encontrado, usando PowerShell...
    powershell -Command "Compress-Archive -Path 'release-package\*' -DestinationPath 'SyncDeskManager-v1.0.0.zip' -Force"
)

if not exist "SyncDeskManager-v1.0.0.zip" (
    echo ❌ ERROR: No se pudo crear el archivo ZIP
    pause
    exit /b 1
)

echo.
echo ✅ PAQUETE LISTO: SyncDeskManager-v1.0.0.zip
echo 📁 Contenido del paquete:
dir "release-package"
echo.
echo 📊 Tamaño del ejecutable: 
for %%F in ("release-package\SyncDeskManager.exe") do echo   %%~zF bytes
echo.
echo 🚀 Proximo paso: Subir "SyncDeskManager-v1.0.0.zip" a GitHub Releases
pause