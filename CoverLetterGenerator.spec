# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['E:\\Project\\Random Projects\\google ai coverletter\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('E:\\Project\\Random Projects\\google ai coverletter\\profiles', 'profiles'), ('E:\\Project\\Random Projects\\google ai coverletter\\cache', 'cache'), ('E:\\Project\\Random Projects\\google ai coverletter\\files', 'files'), ('E:\\Project\\Random Projects\\google ai coverletter\\personal_context', 'personal_context'), ('E:\\Project\\Random Projects\\google ai coverletter\\chat_states', 'chat_states'), ('E:\\Project\\Random Projects\\google ai coverletter\\settings.json', 'settings.json')],
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='CoverLetterGenerator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['files\\storage\\icon.ico'],
)
