"""
PyInstaller runtime hook: pre-configures DLL search paths for onnxruntime
and numpy before any import occurs. Runs at the bootloader level.
"""
import sys
import os


def _setup_dll_dirs():
    base = getattr(sys, '_MEIPASS', None)
    if not base:
        return

    capi_dir = os.path.join(base, 'onnxruntime', 'capi')

    # Collect directories that contain native DLLs
    dll_dirs = [base]

    if os.path.isdir(capi_dir):
        dll_dirs.append(capi_dir)

    # Auto-discover *.libs directories (numpy.libs, scipy.libs, etc.)
    try:
        for entry in os.listdir(base):
            if entry.endswith('.libs'):
                libs_path = os.path.join(base, entry)
                if os.path.isdir(libs_path):
                    dll_dirs.append(libs_path)
    except OSError:
        pass

    # Inject into PATH for legacy resolution
    os.environ['PATH'] = os.pathsep.join(dll_dirs) + os.pathsep + os.environ.get('PATH', '')

    # Register with Python 3.8+ extension loader
    if hasattr(os, 'add_dll_directory'):
        for d in dll_dirs:
            try:
                os.add_dll_directory(d)
            except OSError:
                pass

    # Preload ONNX DLLs using kernel32 (bypasses PyInstaller's ctypes hook)
    if os.path.isdir(capi_dir):
        try:
            import ctypes
            _LoadLibraryW = ctypes.windll.kernel32.LoadLibraryW
            _LoadLibraryW.restype = ctypes.c_void_p
            _LoadLibraryW.argtypes = [ctypes.c_wchar_p]

            for name in ['onnxruntime_providers_shared.dll', 'DirectML.dll', 'onnxruntime.dll']:
                dll = os.path.join(capi_dir, name)
                if os.path.isfile(dll):
                    _LoadLibraryW(dll)
        except Exception:
            pass


_setup_dll_dirs()
