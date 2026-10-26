# Gaussian Elimination Visualizer

A Windows desktop app for exact, step-by-step Gaussian and Gauss–Jordan elimination.
The math engine uses `fractions.Fraction`; UI and document/OCR services are kept out of `core/`.
The Windows build uses the custom matrix icon in `assets/gauss_icon.ico`.

## Run

Requires Python 3.11 or newer. From this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m gauss_visualizer
```

The initial system is a worked example; press **Solve** to inspect its steps. You can change
the equation and variable counts, enter equations individually, or switch to the matrix grid.
Use the left/right arrow keys or the navigation buttons to move between operations. The File
menu exports all solution snapshots to PDF.

## Image and PDF import

PDF text extraction uses PyMuPDF. Scanned PDFs and image files use Tesseract OCR through
`pytesseract`; install Tesseract OCR separately. The app checks `PATH` and common Windows install
folders automatically. Imported lines appear in an editable review dialog before they are loaded
into the equation editor. If Tesseract is installed in a custom folder, set `GAUSS_TESSERACT_PATH`
to the full `tesseract.exe` path before launching the application.
OCR is bounded to 20 seconds per page/image so a difficult scan cannot leave the import worker
waiting indefinitely. Application error logs are written to the operating system's per-user
application data folder.

## Tests

```powershell
python -m pytest
```

The `core` package has no PySide6, OCR, or file-service imports and can be used independently.

## Licensing notes

PySide6 is available under LGPL/commercial licensing. PyMuPDF is AGPL/commercial; review those
terms before distributing a packaged application.

## Build a Windows executable

After installing requirements, run `./build_windows.ps1`. The single-file executable is written to
`dist/GaussianEliminationVisualizer.exe`.
Tesseract is an external install and is not bundled by this script.

## GitHub

The repository does not include a license. Choose a license before publishing if you want others
to have explicit reuse rights. Also review the PyMuPDF AGPL/commercial terms above before
distributing binaries.
