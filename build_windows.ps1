$ErrorActionPreference = "Stop"
# PyInstaller searches PATH for every imported DLL. Poppler's ICU DLLs can conflict
# with Qt 6's Windows ICU ABI, so exclude Poppler's directory during dependency discovery.
$env:PATH = ($env:PATH -split ';' | Where-Object { $_ -notmatch '(?i)poppler[\\/]Library[\\/]bin' }) -join ';'
python -m PyInstaller --noconfirm --onefile --windowed --name GaussianEliminationVisualizer `
    --icon assets/gauss_icon.ico --add-data "assets/gauss_icon.png;assets" `
    --paths src --exclude-module matplotlib --exclude-module pandas --exclude-module IPython `
    --exclude-module pytest --exclude-module pymupdf4llm --exclude-module pymupdf.layout `
    --exclude-module tkinter --runtime-hook pyi_rthook_qt_paths.py `
    src/gauss_visualizer/__main__.py
