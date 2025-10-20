@echo off
echo 🏗️ BUILD DEFINITIVO - ESTRUCTURA COMPLETA
echo.

echo 🧹 Limpiando...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist release-package rmdir /s /q release-package
if exist *.spec del *.spec

echo 📦 Instalando dependencias...
pip install numpy==1.26.4 pandas==2.2.2 requests==2.31.0 openpyxl==3.1.2 psutil==5.9.5

echo 🔨 Construyendo con especificación completa...
pyinstaller --name SyncDeskManager --console ^
 --add-data "data;data" ^
 --add-data "src;src" ^
 --hidden-import=src.utils.logger ^
 --hidden-import=src.utils.file_utils ^
 --hidden-import=src.utils.display_utils ^
 --hidden-import=src.utils.template_manager ^
 --hidden-import=src.utils.api_utils ^
 --hidden-import=src.utils.validation_utils ^
 --hidden-import=src.menus.main_menu ^
 --hidden-import=src.menus.processes_menu ^
 --hidden-import=src.menus.reports_menu ^
 --hidden-import=src.menus.guide_menu ^
 --hidden-import=src.config.config_manager ^
 --hidden-import=src.config.constants ^
 --hidden-import=src.config.state_mapping ^
 --hidden-import=src.services.freshdesk_service ^
 --hidden-import=src.services.clarity_service ^
 --hidden-import=src.features.processes ^
 --hidden-import=src.features.reports ^
 --hidden-import=src.features.sync_processes ^
 --hidden-import=src.features.guide ^
 --hidden-import=src.features.freshdesk_updater ^
 --collect-all numpy ^
 --collect-all pandas ^
 run.py

echo 📦 Creando paquete...
if exist dist\SyncDeskManager (
    if not exist release-package mkdir release-package
    xcopy dist\SyncDeskManager release-package /E /I /Y
    echo ✅ EJECUTABLE LISTO: release-package\SyncDeskManager.exe
    
    :: Verificar estructura
    echo 📁 Verificando estructura del paquete...
    if exist release-package\src (
        echo ✅ Carpeta src incluida correctamente
        dir release-package\src /B
    ) else (
        echo ❌ ERROR: Carpeta src no está en el paquete
    )
) else (
    echo ❌ Error: No se generó el ejecutable
)

pause