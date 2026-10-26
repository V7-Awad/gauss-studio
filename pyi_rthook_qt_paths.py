"""Register bundled Qt DLL locations before PySide6 extension modules load."""

import os
import sys
import ctypes


if sys.platform == "win32" and hasattr(sys, "_MEIPASS"):
    # Avoid loading Poppler's incompatible ICU DLLs before Qt's bundled ICU.
    _path_entries = os.environ.get("PATH", "").split(os.pathsep)
    _safe_path_entries = []
    for _entry in _path_entries:
        _normalized_entry = os.path.normcase(os.path.normpath(_entry))
        if _normalized_entry.endswith(os.path.normcase(os.path.join("poppler", "Library", "bin"))):
            continue
        _safe_path_entries.append(_entry)

    _dll_directory_handles = getattr(sys, "_gauss_dll_directory_handles", [])
    for _folder in ("PySide6", "shiboken6"):
        _path = os.path.join(sys._MEIPASS, _folder)
        if os.path.isdir(_path):
            _dll_directory_handles.append(os.add_dll_directory(_path))
    _qt_dir = os.path.join(sys._MEIPASS, "PySide6")
    if os.path.isdir(_qt_dir):
        os.environ["PATH"] = os.pathsep.join([_qt_dir, *_safe_path_entries])
    else:
        os.environ["PATH"] = os.pathsep.join(_safe_path_entries)
    for _library in ("Qt6Core.dll", "Qt6Gui.dll", "Qt6Widgets.dll"):
        _library_path = os.path.join(_qt_dir, _library)
        if os.path.isfile(_library_path):
            ctypes.WinDLL(_library_path)
    sys._gauss_dll_directory_handles = _dll_directory_handles
