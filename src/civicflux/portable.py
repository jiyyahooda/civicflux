"""Portable XGBoost recovery for the two trusted, unchanged research bundles.

Only the Booster is read from a native UBJSON export. Preprocessing, calibration,
thresholds and bundle classes still come from the original joblib. No global
monkeypatch, training, or mutation of the original bundle is involved.
"""
from pathlib import Path
import hashlib
import json

import joblib
from joblib.numpy_pickle import NumpyUnpickler
import xgboost as xgb

COMPONENTS = {'traffic', 'flood'}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def snapshot_model_bytes(snapshot):
    """Extract the exact native Model bytes from the known Config/Model wrapper.

    Reject unknown layouts rather than repairing or rewriting any tree values.
    Recovery additionally requires byte-identical native save_raw round-tripping.
    """
    snapshot = bytes(snapshot)
    config_key = b'L' + (6).to_bytes(8, 'big') + b'Config'
    model_key = b'L' + (5).to_bytes(8, 'big') + b'Model'
    if not snapshot.startswith(b'{' + config_key + b'{'):
        raise ValueError('Unsupported XGBoost snapshot header')
    if snapshot.count(model_key) != 1 or not snapshot.endswith(b'}}'):
        raise ValueError('Unsupported XGBoost snapshot layout')
    position = snapshot.index(model_key)
    if snapshot[position - 1:position] != b'}':
        raise ValueError('Unsupported XGBoost Config boundary')
    model = snapshot[position + len(model_key):-1]
    if not model.startswith(b'{L' + (7).to_bytes(8, 'big') + b'learner{'):
        raise ValueError('Unsupported XGBoost Model boundary')
    return model


def reconstruct_bundle(original, portable_model=None):
    """Scoped unpickler for these trusted uncompressed joblibs; returns evidence.

    portable_model=None is used only by the explicit recovery script. Serving
    supplies a previously verified export, never attempts automatic recovery.
    """
    original = Path(original)
    evidence = []

    class NativeModelBooster(xgb.Booster):
        def __setstate__(self, state):
            if set(state) != {'handle'} or not isinstance(state['handle'], (bytes, bytearray)):
                raise ValueError('Unsupported Booster state; original file preserved')
            snapshot = bytes(state['handle'])
            native = snapshot_model_bytes(snapshot)
            xgb.Booster.__init__(self, model_file=portable_model if portable_model else bytearray(native))
            if bytes(self.save_raw(raw_format='ubj')) != native:
                raise ValueError('Portable model differs from the original native Model bytes')
            evidence.append({'snapshot_sha256':hashlib.sha256(snapshot).hexdigest(),
                             'native_model_sha256':hashlib.sha256(native).hexdigest(),
                             'native_roundtrip_byte_identical':True})
            # The reconstructed object is a normal Booster, with no global patch.
            self.__class__ = xgb.Booster

    class BundleUnpickler(NumpyUnpickler):
        def find_class(self, module, name):
            if module == 'xgboost.core' and name == 'Booster':
                return NativeModelBooster
            return super().find_class(module, name)

    with original.open('rb') as stream:
        if stream.read(2) != b'\x80\x04':
            raise ValueError('Recovery supports only the inspected protocol-4 uncompressed bundles')
        stream.seek(0)
        bundle = BundleUnpickler(str(original), stream, mmap_mode=None).load()
    if len(evidence) != 1:
        raise ValueError('Expected exactly one XGBoost Booster')
    return bundle, evidence[0]


def portable_files(root, entry):
    if entry['component'] not in COMPONENTS:
        return None
    original = Path(root) / entry['artifact']
    directory = original.parent / 'portable-windows'
    if not directory.exists():
        return None
    return original, directory / 'booster.ubj', directory / 'manifest.json'


def runtime_artifact_hashes(root, entry):
    """Bind validation evidence to the original bundle AND portable export."""
    files = portable_files(root, entry)
    if files is None:
        return {}
    return {str(path.relative_to(root)):sha256(path) if path.is_file() else None for path in files}


def load_bundle(root, entry):
    files = portable_files(root, entry)
    if files is None:
        return joblib.load(Path(root) / entry['artifact'])
    original, model, manifest_file = files
    manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
    if (manifest.get('format_version') != 1 or manifest.get('component') != entry['component']
            or manifest.get('original_sha256') != sha256(original)
            or manifest.get('portable_sha256') != sha256(model)
            or manifest.get('verification', {}).get('passed') is not True):
        raise ValueError('Portable export verification/hash mismatch; refusing inference')
    bundle, evidence = reconstruct_bundle(original, model)
    if evidence['snapshot_sha256'] != manifest['snapshot_sha256']:
        raise ValueError('Original Booster snapshot hash mismatch')
    return bundle
