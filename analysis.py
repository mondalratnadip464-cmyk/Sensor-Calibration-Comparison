"""
analysis.py
===========
Pandas-based analysis of calibration runs (CO5) using the NumPy-based
Calibrator and metrics from calibration.py (CO4).

Experiments
-----------
1. Held-out evaluation  : train on the first 70 % of trials, test on the rest.
2. Extrapolation test   : train only on reference <= 50 C, test on > 50 C.
3. Spike-fault test     : plain linear fit vs linear fit with outlier trimming.
"""

import json

import pandas as pd

from calibration import Calibrator, bias, mae, max_abs_error, rmse

TRAIN_FRACTION = 0.7
METHODS = ("offset", "linear", "quadratic")


def runs_to_dataframe(runs):
    """Flatten CalibrationRun objects into one tidy DataFrame (uses __iter__)."""
    rows = []
    for run in runs:
        for ref, raw in run:
            rows.append({"sensor": run.sensor, "trial": run.trial,
                         "reference_c": ref, "raw_c": raw})
    df = pd.DataFrame(rows)
    df["error_c"] = df["raw_c"] - df["reference_c"]
    return df


def summarise_trials(df):
    """Mean error, spread and RMSE for every (sensor, trial) pair."""
    grouped = df.groupby(["sensor", "trial"])["error_c"]
    summary = grouped.agg(mean_error="mean", std_error="std").reset_index()
    summary["rmse"] = grouped.apply(lambda s: (s ** 2).mean() ** 0.5).values
    return summary.round(3)


def summarise_sensors(df):
    """Per-sensor overview of the raw (uncorrected) errors."""
    out = df.groupby("sensor")["error_c"].agg(
        readings="count", mean_error="mean", std_error="std",
        min_error="min", max_error="max").reset_index()
    out["mae"] = df.groupby("sensor")["error_c"].apply(lambda s: s.abs().mean()).values
    return out.round(3)


def split_trials(df, train_fraction=TRAIN_FRACTION):
    """
    Split by WHOLE TRIALS (not by random rows) so that no reading of a test
    trial is ever used for training. Returns (train_df, test_df, train_trials).
    """
    trials = sorted(df["trial"].unique())
    n_train = max(1, int(round(train_fraction * len(trials))))
    train_trials = trials[:n_train]
    train_df = df[df["trial"].isin(train_trials)].copy()
    test_df = df[~df["trial"].isin(train_trials)].copy()
    return train_df, test_df, train_trials


def metrics_row(error):
    """Collect the four error metrics for a NumPy/Pandas array of errors."""
    return {"bias": bias(error), "mae": mae(error),
            "rmse": rmse(error), "max_abs": max_abs_error(error)}


def fit_calibrators(train_df, methods=METHODS, trim=False):
    """Fit one Calibrator per (sensor, method). Returns dict[(sensor, method)]."""
    fitted = {}
    for sensor, part in train_df.groupby("sensor"):
        for method in methods:
            cal = Calibrator(method, trim=trim)
            cal.fit(part["raw_c"].to_numpy(), part["reference_c"].to_numpy())
            fitted[(sensor, method)] = cal
    return fitted


def evaluate_methods(test_df, fitted, methods=METHODS):
    """
    Experiment 1: error of 'no correction' and every method on the TEST data.
    improvement_pct is the relative reduction in RMSE versus no correction.
    """
    rows = []
    for sensor, part in test_df.groupby("sensor"):
        raw = part["raw_c"].to_numpy()
        ref = part["reference_c"].to_numpy()
        base = metrics_row(raw - ref)
        rows.append({"sensor": sensor, "method": "none", **base,
                     "improvement_pct": 0.0})
        for method in methods:
            corrected = fitted[(sensor, method)].predict(raw)
            m = metrics_row(corrected - ref)
            m["improvement_pct"] = 100.0 * (base["rmse"] - m["rmse"]) / base["rmse"]
            rows.append({"sensor": sensor, "method": method, **m})
    return pd.DataFrame(rows).round(4)


def best_method_per_sensor(results):
    """Return {sensor: method with the lowest test RMSE (excluding 'none')}."""
    candidates = results[results["method"] != "none"]
    idx = candidates.groupby("sensor")["rmse"].idxmin()
    return {row["sensor"]: row["method"] for _, row in candidates.loc[idx].iterrows()}


def extrapolation_experiment(train_df, test_df, split_ref=50.0, methods=METHODS):
    """
    Experiment 2 (failure case): train only on readings with reference <= split_ref
    and test on held-out readings with reference > split_ref.
    A 'quadratic+trim' row is added to show the effect of outlier trimming.
    """
    tr = train_df[train_df["reference_c"] <= split_ref]
    te = test_df[test_df["reference_c"] > split_ref]
    variants = [(m, False) for m in methods] + [("quadratic", True)]
    rows = []
    for sensor in sorted(tr["sensor"].unique()):
        a, b = tr[tr["sensor"] == sensor], te[te["sensor"] == sensor]
        raw_b, ref_b = b["raw_c"].to_numpy(), b["reference_c"].to_numpy()
        base = metrics_row(raw_b - ref_b)
        rows.append({"sensor": sensor, "method": "none",
                     "rmse": base["rmse"], "max_abs": base["max_abs"]})
        for method, trim in variants:
            cal = Calibrator(method, trim=trim).fit(
                a["raw_c"].to_numpy(), a["reference_c"].to_numpy())
            m = metrics_row(cal.predict(raw_b) - ref_b)
            rows.append({"sensor": sensor, "method": cal.label(),
                         "rmse": m["rmse"], "max_abs": m["max_abs"]})
    return pd.DataFrame(rows).round(4)


def spike_experiment(train_df, test_df):
    """
    Experiment 3 (failure case): linear fit with and without outlier trimming.
    Reports test RMSE and how many training readings were trimmed.
    """
    rows = []
    for sensor in sorted(train_df["sensor"].unique()):
        a = train_df[train_df["sensor"] == sensor]
        b = test_df[test_df["sensor"] == sensor]
        for trim in (False, True):
            cal = Calibrator("linear", trim=trim).fit(
                a["raw_c"].to_numpy(), a["reference_c"].to_numpy())
            err = cal.predict(b["raw_c"].to_numpy()) - b["reference_c"].to_numpy()
            rows.append({"sensor": sensor, "fit": "linear+trim" if trim else "linear",
                         "trimmed_points": cal.n_trimmed,
                         "test_rmse": rmse(err), "test_max_abs": max_abs_error(err)})
    return pd.DataFrame(rows).round(4)


def save_results(path_json, payload):
    """CO5/CO2: store a dictionary of results as JSON."""
    with open(path_json, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
