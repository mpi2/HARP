# -*- mode: python -*-
a = Analysis(['harp.py'],
             pathex=['C:\\Users\\james.brown\\Documents\\GitHub\\mrchsig\\HARP'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='harp.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False , icon='harp.ico')
coll = COLLECT(exe,
               a.binaries + [('msvcp100.dll', 'C:\\Windows\\System32\\msvcp100.dll', 'BINARY'),
							 ('msvcr100.dll', 'C:\\Windows\\System32\\msvcr100.dll', 'BINARY')]
			   if sys.platform == 'win32' else a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='harp')
