# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('data', 'data'), ('src', 'src')]
binaries = []
hiddenimports = ['src.utils.logger', 'src.utils.file_utils', 'src.utils.display_utils', 'src.utils.template_manager', 'src.utils.api_utils', 'src.utils.validation_utils', 'src.menus.main_menu', 'src.menus.processes_menu', 'src.menus.reports_menu', 'src.menus.guide_menu', 'src.config.config_manager', 'src.config.constants', 'src.config.state_mapping', 'src.services.freshdesk_service', 'src.services.clarity_service', 'src.features.processes', 'src.features.reports', 'src.features.sync_processes', 'src.features.guide', 'src.features.freshdesk_updater']
tmp_ret = collect_all('numpy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('pandas')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SyncDeskManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SyncDeskManager',
)
