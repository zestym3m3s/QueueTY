# QueueTY.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    [
        'gui.py',
        'gzip_and_unzip.py',
        'check_remote_directory.py',
        'clean_up_molecule_list.py',
        'generate_conformers_vconf.py',
        'cmdline_TMoleX_process.py',
        'submit_remote_jobs_to_cluster.py',
        'check_cluster_queue.py',
        'grab_files_from_cluster.py',
        'write_new_inp_file.py',
        'console_utils.py',
        'main.py',
        'termination.py'
    ],
    pathex=['C:\\Users\\trist\\PycharmProjects\\QueueTY_v1\\venv\\src'],
    binaries=[],
    datas=[
        ('README.txt', '.'),  # Include README.txt in the datas
        ('icon.ico', '.'),
        ('icon.png', '.'),
        ('cosmoprep.sh', '.'),
        ('define.sh', '.'),
        ('remote_script_template.sh', '.'),
        ('subscript.sh', '.'),
        ('constants_last.txt', '.'),
        ('default_settings.txt', '.'),
        # Place Python scripts in the root directory
        ('gzip_and_unzip.py', '.'),
        ('check_remote_directory.py', '.'),
        ('clean_up_molecule_list.py', '.'),
        ('generate_conformers_vconf.py', '.'),
        ('cmdline_TMoleX_process.py', '.'),
        ('submit_remote_jobs_to_cluster.py', '.'),
        ('check_cluster_queue.py', '.'),
        ('grab_files_from_cluster.py', '.'),
        ('write_new_inp_file.py', '.'),
        ('dictionary.py', '.'),
        ('console_utils.py', '.'),
        ('constants.py', '.'),
        ('main.py', '.'),
        ('termination.py', '.')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='QueueTY',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Enable the console window for debugging
    icon='icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='QueueTY'
)
