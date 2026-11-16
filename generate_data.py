"""
generate_data.py
================
Creates the SIMULATED demonstration dataset used by this project.

IMPORTANT: the readings are produced by a mathematical procedure with a fixed
random seed. They are NOT measurements from real sensors. Every table, figure
and conclusion in the report must therefore be described as a simulation result.

Scenario
--------
Two temperature sensors are compared with a trusted reference thermometer.
Reference temperatures run from 20 C to 80 C in 5 C steps (13 points) and the
experiment is repeated 10 times (10 trials) for each sensor.

  Sensor A ("analog, LM35-like")  : gain error + offset error (a straight line)
  Sensor B ("thermistor-like")    : gain + offset + curvature (non-linear)

The file also contains
  * 5 deliberately invalid rows (blank, text, fault code, ...) so that the
    validation code has something to reject, and
  * 4 "spike" faults (valid-looking but wrong readings) placed ONLY in the
    training trials, so the effect of contaminated calibration data can be
    studied in a controlled way.

Run:  python generate_data.py
"""

import csv
import os

import numpy as np

SEED = 2026
REFERENCE_POINTS = np.arange(20.0, 80.1, 5.0)   # 20, 25, ..., 80  (13 values)
N_TRIALS = 10
OUTPUT_PATH = os.path.join("data", "simulated_sensor_readings.csv")


def true_sensor_response(sensor, reference, rng):
    """Return the raw reading a sensor would give for a reference value."""
    if sensor == "A":
        # straight-line error: gain 1.04, offset -3.0 C, noise sigma 0.35 C
        return 1.04 * reference - 3.0 + rng.normal(0.0, 0.35, reference.shape)
    # sensor B: gain 0.98, offset +1.2 C, curvature, noise sigma 0.30 C
    return (0.98 * reference + 1.2
            + 0.004 * (reference - 50.0) ** 2
            + rng.normal(0.0, 0.30, reference.shape))


def build_valid_rows(rng):
    """Create all valid (sensor, trial, reference, raw) rows as a list of dicts."""
    rows = []
    for sensor in ("A", "B"):
        for trial in range(1, N_TRIALS + 1):
            raw = true_sensor_response(sensor, REFERENCE_POINTS, rng)
            for ref, value in zip(REFERENCE_POINTS, raw):
                rows.append({"sensor": sensor, "trial": trial,
                             "reference_c": round(float(ref), 2),
                             "raw_c": round(float(value), 2)})
    return rows


def add_spikes(rows, rng, n_spikes=4, max_train_trial=7):
    """Add +/- 8..15 C faults to randomly chosen readings of training trials."""
    candidates = [i for i, r in enumerate(rows) if r["trial"] <= max_train_trial]
    chosen = rng.choice(candidates, size=n_spikes, replace=False)
    for k, idx in enumerate(chosen):
        size = rng.uniform(8.0, 15.0) * (1 if k % 2 == 0 else -1)
        rows[idx]["raw_c"] = round(rows[idx]["raw_c"] + size, 2)
    return sorted(int(i) for i in chosen)


def invalid_rows():
    """Rows that the validation stage MUST reject."""
    return [
        {"sensor": "A", "trial": 3, "reference_c": 45.0, "raw_c": ""},        # blank reading
        {"sensor": "B", "trial": 4, "reference_c": 60.0, "raw_c": 999.0},     # sensor fault code
        {"sensor": "", "trial": 2, "reference_c": 30.0, "raw_c": 31.2},       # missing sensor id
        {"sensor": "A", "trial": 5, "reference_c": "abc", "raw_c": 52.0},     # non-numeric reference
        {"sensor": "B", "trial": 0, "reference_c": 25.0, "raw_c": 26.4},      # trial must be >= 1
    ]


def main():
    rng = np.random.default_rng(SEED)
    rows = build_valid_rows(rng)
    spike_positions = add_spikes(rows, rng)

    # insert the invalid rows at reproducible random positions
    for bad in invalid_rows():
        rows.insert(int(rng.integers(0, len(rows))), bad)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["sensor", "trial", "reference_c", "raw_c"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")
    print(f"  valid rows      : {len(rows) - len(invalid_rows())}")
    print(f"  invalid rows    : {len(invalid_rows())}")
    print(f"  spike faults    : {len(spike_positions)}")
    print("NOTE: this data is SIMULATED (seed = %d)." % SEED)


if __name__ == "__main__":
    main()
