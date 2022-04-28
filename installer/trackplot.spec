# -*- mode: python ; coding: utf-8 -*-
# https://github.com/chriskiehl/Gooey/blob/master/docs/packaging/build-win.spec
# from https://chriskiehl.com/article/packaging-gooey-with-pyinstaller
# https://stackoverflow.com/questions/54836440/branca-python-module-is-unable-to-find-2-essential-json-files-when-running-an-ex/55982529#55982529

from PyInstaller.utils.hooks import collect_dynamic_libs
from PyInstaller.utils.hooks import collect_data_files # this is very helpful

block_cipher = None

import gooey
gooey_root = os.path.dirname(gooey.__file__)
gooey_languages = Tree(os.path.join(gooey_root, 'languages'), prefix = 'gooey/languages')
gooey_images = Tree(os.path.join(gooey_root, 'images'), prefix = 'gooey/images')

# https://github.com/chriskiehl/Gooey/blob/master/docs/packaging/Packaging-Custom-Images.md
#image_overrides = Tree('C:\\Users\\patrice.ponchant\\Documents\\GitHub\\trackplot\\src\\icons', 
#                        prefix='C:\\Users\\patrice.ponchant\\Documents\\GitHub\\trackplot\\src\\icons')

hidden_imports = [
    'ctypes',
    'ctypes.util',
    'fiona',
    'gdal',
    'shapely',
    'shapely.geometry',
    'pyproj',
    'rtree',
    'geopandas.datasets',
    'fiona._shim',
    'fiona.schema',
    'cftime',
]

version='Cedric_beta_version'
# Fernando
sources_root = os.path.join(os.environ["USERPROFILE"], 'Documents\\GitHub\\Trackplot')
venv_root = os.path.join(os.environ["USERPROFILE"], 'Documents\\python_env\\trackplot')

# Adapt to your configuration
# sources_root = 'C:\\dev\\Trackplot'
# venv_root = os.path.join(os.environ["USERPROFILE"], 'anaconda3\\envs\\trackplot')

site_packages = os.path.join(venv_root, 'Lib\\site-packages')
trackplot_src = os.path.join(sources_root, 'src\\trackplot')
datas = collect_data_files('pyproj', 'geopandas', subdir='datasets') + [
                    (f"{sources_root}\\src\\Trackplot\\assets","assets"),
                    (f"{site_packages}\\branca\\*.json","branca"),
                    (f"{site_packages}\\branca\\templates","templates"),
                    (f"{site_packages}\\folium\\templates","templates"),
                    (f"{site_packages}\\geopandas\\datasets","geopandas\\datasets")
                    ]

gui_a = Analysis(['C:\\Users\\fernando.carneiro\\Documents\\GitHub\\Trackplot\\src\\Trackplot\\trackplot_gui.py'],
                      pathex=['C:\\Users\\fernando.carneiro\\Documents\\GitHub\\Trackplot\\src\\Trackplot'],
                      binaries=collect_dynamic_libs("rtree"),
                      datas=datas,
                      hiddenimports=hidden_imports,
                      hookspath=[],
                      runtime_hooks=[],
                      win_no_prefer_redirects=False,
                      win_private_assemblies=False,
                      cipher=block_cipher,
                      noarchive=False)


gui_pyz = PYZ(gui_a.pure, gui_a.zipped_data,
                  cipher=block_cipher)
gui_exe = EXE(gui_pyz,
                  gui_a.scripts,
                  [],
                  exclude_binaries=True,
                  name=f'trackplot-gui-v{version}',
                  debug=False,
                  bootloader_ignore_signals=False,
                  strip=False,
                  upx=True,
                  console=True,
                  icon=os.path.join(gooey_root, 'images', 'program_icon.ico'))


coll = COLLECT(gui_exe,
               gui_a.binaries,
               gui_a.zipfiles,
               gui_a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name=f'trackplot-v{version}',
               icon=os.path.join(gooey_root, 'images', 'program_icon.ico'))