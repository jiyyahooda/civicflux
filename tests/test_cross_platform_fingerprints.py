from pathlib import Path, PureWindowsPath
from project_paths import PROJECT_ROOT
from src.civicflux import serving, portable

class WindowsRelativePath(type(Path())):
    """Keep local IO, but represent relative paths as a Windows checkout does."""
    def relative_to(self, *args, **kwargs):
        return PureWindowsPath(super().relative_to(*args, **kwargs).as_posix())

def test_interface_fingerprint_is_identical_with_windows_relative_paths(monkeypatch):
    expected = serving.interface_fingerprint(PROJECT_ROOT)
    monkeypatch.setattr(serving, 'Path', WindowsRelativePath)
    assert serving.interface_fingerprint(PROJECT_ROOT) == expected

def test_portable_artifact_hash_keys_are_identical_on_windows(monkeypatch):
    entry = next(r for r in serving.discover(PROJECT_ROOT) if r['component'] == 'traffic')
    expected = portable.runtime_artifact_hashes(PROJECT_ROOT, entry)
    assert expected
    files = portable.portable_files(PROJECT_ROOT, entry)
    monkeypatch.setattr(portable, 'portable_files', lambda root, entry: [WindowsRelativePath(p) for p in files])
    assert portable.runtime_artifact_hashes(PROJECT_ROOT, entry) == expected
