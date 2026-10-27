"""Recover existing XGBoost trees and verify saved test predictions; never fit.

Writes additive native exports. Original models, data, notebooks and registry
remain unchanged. A manifest is published only after complete parity checks.
"""
from pathlib import Path
from datetime import datetime
import json
import platform
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
import xgboost
from civicflux_core import canonicalize, make_features, FLOOD_FEATURES
from src.civicflux.portable import reconstruct_bundle, sha256


def compare(actual, expected, *, atol, rtol):
    actual, expected = np.asarray(actual), np.asarray(expected)
    if actual.shape != expected.shape or not np.isfinite(actual).all() or not np.isfinite(expected).all():
        raise ValueError('Prediction comparison has invalid shape or values')
    np.testing.assert_allclose(actual, expected, atol=atol, rtol=rtol)
    return {'rows':len(actual), 'max_absolute_error':float(np.max(np.abs(actual - expected))),
            'absolute_tolerance':atol, 'relative_tolerance':rtol, 'passed':True}


def traffic_parity(bundle, expected):
    raw = pd.read_csv(ROOT / 'data/raw' / bundle.cfg['file'])
    history, _ = canonicalize(raw, bundle.cfg)
    features = make_features(history, bundle.cfg)
    expected = expected.copy()
    expected['entity'] = expected.entity.astype(str)
    for column in ['time', 'target_time']:
        expected[column] = pd.to_datetime(expected[column])
    features['entity'] = features.entity.astype(str)
    aligned = expected.merge(features, on=['entity','time','target_time'], how='left',
                              validate='one_to_one', suffixes=('_saved','_current'), indicator=True)
    if not aligned['_merge'].eq('both').all():
        raise ValueError('Could not reconstruct every original traffic test feature row')
    np.testing.assert_allclose(aligned.target_saved, aligned.target_current, rtol=0, atol=0)
    predictions = np.maximum(0, bundle.model.predict(aligned[bundle.features]))
    result = {'prediction':compare(predictions, aligned.prediction, atol=1e-5, rtol=1e-6),
              'lower_interval':compare(np.maximum(0, predictions-bundle.interval_radius), aligned.lower, atol=1e-5, rtol=1e-6),
              'upper_interval':compare(predictions+bundle.interval_radius, aligned.upper, atol=1e-5, rtol=1e-6),
              'entities':sorted(expected.entity.unique().tolist()), 'feature_recipe':'existing canonicalize + make_features'}
    return result


def flood_parity(bundle, expected):
    actual = bundle.predict(expected[FLOOD_FEATURES])
    result = {'calibrated_probability':compare(actual.simulated_flood_probability, expected.probability, atol=1e-7, rtol=1e-6),
              'alerts_identical':bool(np.array_equal(actual.scenario_alert.to_numpy(), expected.predicted.to_numpy())),
              'calibrator':type(bundle.calibrator).__name__, 'threshold':bundle.threshold}
    if not result['alerts_identical']:
        raise ValueError('Recovered flood decisions differ from saved research decisions')
    return result


def main():
    results = []
    for component in ['traffic', 'flood']:
        original = ROOT / 'artifacts' / component / 'pipeline.joblib'
        directory = original.parent / 'portable-windows'
        if directory.exists():
            raise FileExistsError('Refusing to overwrite existing recovery output: ' + str(directory))
        original_hash = sha256(original)
        bundle, evidence = reconstruct_bundle(original)
        expected_path = original.parent / 'test_predictions.csv'
        expected = pd.read_csv(expected_path)
        parity = traffic_parity(bundle, expected) if component == 'traffic' else flood_parity(bundle, expected)
        estimator = bundle.model.steps[-1][1] if hasattr(bundle.model, 'steps') else bundle.model
        booster = estimator.get_booster()
        directory.mkdir()
        booster.save_model(directory / 'booster.ubj')
        booster.save_model(directory / 'booster.json')
        reloaded, reload_evidence = reconstruct_bundle(original, directory / 'booster.ubj')
        # Verify the public bundle methods also retain native-export parity.
        if component == 'flood':
            compare(reloaded.predict(expected).simulated_flood_probability,
                    bundle.predict(expected).simulated_flood_probability, atol=0, rtol=0)
        else:
            from src.civicflux.integration import fixture
            sample = pd.DataFrame(fixture(component, ROOT)['history'])
            compare(reloaded.predict(sample).prediction, bundle.predict(sample).prediction, atol=0, rtol=0)
        if sha256(original) != original_hash or evidence != reload_evidence:
            raise ValueError('Original changed or native export did not round-trip')
        manifest = {'format_version':1, 'component':component,
                    'created_at':datetime.now(ZoneInfo('Asia/Kolkata')).isoformat(),
                    'method':'Exact native Model section extracted from original XGBoost UBJSON snapshot, loaded via load_model, exported via save_model',
                    'original_artifact':str(original.relative_to(ROOT)), 'original_sha256':original_hash,
                    'portable_sha256':sha256(directory / 'booster.ubj'),
                    'json_sha256':sha256(directory / 'booster.json'), **evidence,
                    'python':platform.python_version(), 'xgboost':xgboost.__version__,
                    'test_predictions_sha256':sha256(expected_path),
                    'verification':{'passed':True, 'rows':len(expected), **parity},
                    'limitations':['Research-only; original units, scope, provenance and validation limitations remain.',
                                   'Original macOS process unavailable; parity checked against all saved test outputs.',
                                   'No retraining; original preprocessing, calibration and thresholds retained.']}
        (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        results.append(manifest)
        print(component, 'recovered;', len(expected), 'saved test rows matched', flush=True)
    report = ROOT / 'reports/windows/recovery/recovery_results.json'
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(results, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
