"""
calibration.py
==============
Core library of the Sensor Calibration Comparison project.

Course-outcome map
------------------
CO1  functions + control flow : parse_float, is_valid_reading, validate_row, ...
CO2  data structures + files  : dict / list / set / tuple, csv.DictReader, text log
CO3  classes and objects      : CalibrationRun (special methods), Calibrator
CO4  NumPy                    : polyfit / polyval / vectorised error metrics
(CO5 Pandas is in analysis.py, CO6 Matplotlib is in plotting.py)
"""

import csv
import math

import numpy as np

# --------------------------------------------------------------------------
# Constants (valid operating range of the temperature sensors, in Celsius)
# --------------------------------------------------------------------------
REQUIRED_COLUMNS = ("sensor", "trial", "reference_c", "raw_c")
TEMP_MIN = -40.0
TEMP_MAX = 125.0


# --------------------------------------------------------------------------
# CO1: small functions with control flow
# --------------------------------------------------------------------------
def parse_float(text):
    """Convert text to float. Return None if it is blank or not a number."""
    if text is None:
        return None
    text = str(text).strip()
    if text == "":
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    if math.isnan(value) or math.isinf(value):
        return None
    return value


def is_valid_reading(value, low=TEMP_MIN, high=TEMP_MAX):
    """A reading is valid if it is a finite number inside the sensor range."""
    if value is None:
        return False
    return low <= value <= high


def parse_trial(text):
    """Trial numbers must be whole numbers >= 1. Return int or None."""
    number = parse_float(text)
    if number is None or number != int(number) or number < 1:
        return None
    return int(number)


def validate_row(row):
    """
    Validate one CSV row (a dict).
    Returns (record, reason):
      * record is a clean dict when the row is valid, otherwise None
      * reason is "" when valid, otherwise a short explanation
    """
    sensor = str(row.get("sensor", "") or "").strip()
    if sensor == "":
        return None, "missing sensor id"

    trial = parse_trial(row.get("trial"))
    if trial is None:
        return None, "trial must be a whole number >= 1"

    reference = parse_float(row.get("reference_c"))
    if reference is None:
        return None, "reference value missing or not numeric"
    if not is_valid_reading(reference):
        return None, "reference value outside valid range"

    raw = parse_float(row.get("raw_c"))
    if raw is None:
        return None, "raw reading missing or not numeric"
    if not is_valid_reading(raw):
        return None, "raw reading outside valid range (sensor fault?)"

    record = {"sensor": sensor, "trial": trial,
              "reference_c": reference, "raw_c": raw}
    return record, ""


def load_csv(path):
    """
    CO2 (file handling): read a CSV file with csv.DictReader.
    Returns (records, rejected)
      records  : list of clean dicts
      rejected : list of dicts {line, reason, row} for every invalid row
    """
    records = []
    rejected = []
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = set(REQUIRED_COLUMNS) - set(reader.fieldnames or [])
        if missing:
            raise ValueError("CSV is missing columns: " + ", ".join(sorted(missing)))
        for line_no, row in enumerate(reader, start=2):   # line 1 is the header
            record, reason = validate_row(row)
            if record is None:
                rejected.append({"line": line_no, "reason": reason, "row": dict(row)})
            else:
                records.append(record)
    return records, rejected


def write_rejected_log(rejected, path):
    """CO2: write rejected rows to a plain text log file."""
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("Rejected rows (line number, reason, original row)\n")
        for item in rejected:
            handle.write(f"line {item['line']}: {item['reason']} -> {item['row']}\n")
        if not rejected:
            handle.write("(none)\n")


# --------------------------------------------------------------------------
# Error metrics (CO4: vectorised NumPy)
# --------------------------------------------------------------------------
def bias(error):
    """Mean error (positive = sensor reads too high)."""
    return float(np.mean(error))


def mae(error):
    """Mean absolute error."""
    return float(np.mean(np.abs(error)))


def rmse(error):
    """Root-mean-square error."""
    return float(np.sqrt(np.mean(np.square(error))))


def max_abs_error(error):
    """Largest absolute error."""
    return float(np.max(np.abs(error)))


def residual_outlier_mask(residuals, k=3.5):
    """
    Robust outlier rule using the median absolute deviation (MAD).
    A residual is flagged when it is more than k robust standard deviations
    away from the median residual. Returns a boolean NumPy array.
    """
    residuals = np.asarray(residuals, dtype=float)
    centre = np.median(residuals)
    mad = np.median(np.abs(residuals - centre))
    sigma = 1.4826 * mad            # MAD -> standard deviation (for normal data)
    if sigma == 0:
        return np.zeros(residuals.shape, dtype=bool)
    return np.abs(residuals - centre) > k * sigma


# --------------------------------------------------------------------------
# CO3: classes and objects
# --------------------------------------------------------------------------
class CalibrationRun:
    """
    One trial of one sensor: paired (reference, raw) readings.

    Special methods and why they are used
    -------------------------------------
    __init__ : checks the two arrays have the same non-zero length, so an
               invalid run can never exist.
    __len__  : len(run) is the number of paired readings; this lets the code
               write  `if len(run) < 3`  instead of reaching inside the object.
    __getitem__ : run[i] returns the pair (reference, raw) at position i and
               run[a:b] returns a list of pairs, so a run behaves like a
               sequence of measurements.
    __iter__ : lets us write  `for ref, raw in run:`  directly.
    """

    def __init__(self, sensor, trial, reference, raw):
        reference = np.asarray(reference, dtype=float)
        raw = np.asarray(raw, dtype=float)
        if reference.shape != raw.shape or reference.ndim != 1:
            raise ValueError("reference and raw must be 1-D arrays of equal length")
        if reference.size == 0:
            raise ValueError("a calibration run needs at least one reading")
        self.sensor = sensor
        self.trial = trial
        self.reference = reference
        self.raw = raw

    def __len__(self):
        return int(self.reference.size)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return list(zip(self.reference[index].tolist(), self.raw[index].tolist()))
        return float(self.reference[index]), float(self.raw[index])

    def __iter__(self):
        for ref, raw in zip(self.reference, self.raw):
            yield float(ref), float(raw)

    def __repr__(self):
        return (f"CalibrationRun(sensor={self.sensor!r}, trial={self.trial}, "
                f"n={len(self)})")

    def errors(self):
        """Raw error = raw - reference (NumPy array)."""
        return self.raw - self.reference

    def mean_error(self):
        return bias(self.errors())

    def to_dict(self):
        return {"sensor": self.sensor, "trial": self.trial, "n": len(self),
                "mean_error": self.mean_error(),
                "rmse": rmse(self.errors())}


def group_into_runs(records):
    """
    Group clean records into CalibrationRun objects, one per (sensor, trial).
    Uses a dictionary of lists (CO2) and returns runs sorted by sensor, trial.
    """
    buckets = {}
    for rec in records:
        key = (rec["sensor"], rec["trial"])
        buckets.setdefault(key, {"reference": [], "raw": []})
        buckets[key]["reference"].append(rec["reference_c"])
        buckets[key]["raw"].append(rec["raw_c"])
    runs = []
    for (sensor, trial) in sorted(buckets):
        data = buckets[(sensor, trial)]
        runs.append(CalibrationRun(sensor, trial, data["reference"], data["raw"]))
    return runs


class Calibrator:
    """
    Learns a correction  corrected = f(raw)  from training data.

    method = "offset"    : corrected = raw + b            (remove mean error)
    method = "linear"    : corrected = a*raw + b          (gain + offset)
    method = "quadratic" : corrected = a*raw^2 + b*raw + c (gain, offset, curvature)

    trim = True repeats the fit after removing readings whose residual is
    flagged by the robust MAD rule (protects against spike faults).
    """

    METHODS = ("offset", "linear", "quadratic")
    MIN_POINTS = {"offset": 1, "linear": 2, "quadratic": 3}

    def __init__(self, method="linear", trim=False):
        if method not in self.METHODS:
            raise ValueError(f"method must be one of {self.METHODS}")
        self.method = method
        self.trim = trim
        self.coefficients = None     # highest power first, as used by np.polyval
        self.n_trimmed = 0

    def _fit_once(self, raw, reference):
        if self.method == "offset":
            return np.array([1.0, float(np.mean(reference - raw))])
        degree = 1 if self.method == "linear" else 2
        return np.polyfit(raw, reference, degree)

    def fit(self, raw, reference):
        raw = np.asarray(raw, dtype=float)
        reference = np.asarray(reference, dtype=float)
        if raw.shape != reference.shape:
            raise ValueError("raw and reference must have the same shape")
        if raw.size < self.MIN_POINTS[self.method]:
            raise ValueError(f"{self.method} fit needs at least "
                             f"{self.MIN_POINTS[self.method]} points")
        coefficients = self._fit_once(raw, reference)
        self.n_trimmed = 0
        if self.trim:
            residuals = reference - np.polyval(coefficients, raw)
            outliers = residual_outlier_mask(residuals)
            self.n_trimmed = int(outliers.sum())
            keep = ~outliers
            if self.n_trimmed > 0 and keep.sum() >= self.MIN_POINTS[self.method]:
                coefficients = self._fit_once(raw[keep], reference[keep])
        self.coefficients = coefficients
        return self

    def predict(self, raw):
        if self.coefficients is None:
            raise RuntimeError("call fit() before predict()")
        return np.polyval(self.coefficients, np.asarray(raw, dtype=float))

    def label(self):
        return self.method + ("+trim" if self.trim else "")

    def describe(self):
        """Human-readable formula of the fitted correction."""
        if self.coefficients is None:
            return f"{self.label()} (not fitted)"
        c = self.coefficients
        if self.method == "quadratic":
            return f"corrected = {c[0]:.5f}*raw^2 + {c[1]:.4f}*raw + {c[2]:.3f}"
        return f"corrected = {c[0]:.4f}*raw + {c[1]:.3f}"
