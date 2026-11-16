# Sensor Calibration Comparison

**Subject:** Python Programming Laboratory (B.Tech, ECE, Section B) — Institute of Engineering & Management, Kolkata
**Project option:** #7 Sensor calibration comparison (Ten Group Capstone Project Options)

A Python program that compares raw temperature-sensor readings against a trusted
reference thermometer, learns a correction (offset, linear, quadratic), and checks
**on held-out trials** whether the correction really reduces the error. It also
studies two failure cases: extrapolation outside the calibrated range and spike faults.

> **Data notice:** the included dataset `data/simulated_sensor_readings.csv` is
> **SIMULATED** (fixed random seed 2026, produced by `generate_data.py`). It is *not*
> a measurement from real sensors, and all results are simulation results.

## How the six course outcomes are covered

| CO | Where in the code |
|----|-------------------|
| CO1 functions & control flow | `parse_float`, `is_valid_reading`, `validate_row`, `residual_outlier_mask` in `calibration.py` |
| CO2 data structures & file I/O | dicts/lists/tuples/sets, `csv.DictReader`, text log `outputs/rejected_rows.txt` |
| CO3 classes & objects | `CalibrationRun` (special methods `__init__`, `__len__`, `__getitem__`, `__iter__`) and `Calibrator` |
| CO4 NumPy | `np.polyfit`, `np.polyval`, vectorised MAE / RMSE / bias, MAD outlier rule |
| CO5 Pandas + CSV/JSON | DataFrame, `groupby` summaries, train/test split, CSV + JSON outputs |
| CO6 Matplotlib + interpretation | four labelled figures in `outputs/`, written discussion in the report |

**Why the special methods:** `__len__` gives the number of paired readings, `__getitem__`
lets a run be indexed/sliced like a sequence, `__iter__` allows `for ref, raw in run:`,
and `__init__` guarantees no invalid (empty / unequal-length) run can exist.

## Files

```
generate_data.py          creates the simulated CSV (reproducible)
calibration.py            validation, CSV loading, CalibrationRun, Calibrator, metrics
analysis.py               Pandas summaries, held-out evaluation, failure-case experiments
plotting.py               Matplotlib figures
main.py                   runs the whole pipeline
test_calibration.py       23 unit tests (unittest)
data/                     input CSV (simulated)
outputs/                  figures, result tables (CSV/JSON), rejected-rows log, test log
report/                   project report (PDF) and the script that builds it
```

## How to run

```bash
pip install -r requirements.txt     # numpy, pandas, matplotlib
python generate_data.py             # (optional) recreate the simulated CSV
python main.py                      # run the full analysis, saves everything to outputs/
python -m unittest -v               # run the tests
```
Using your own data: `python main.py --data your_file.csv` (columns exactly:
`sensor, trial, reference_c, raw_c`, temperatures in °C).

## Method in brief

1. Read and validate each CSV row; invalid rows are skipped and logged.
2. Group valid rows into `CalibrationRun` objects (one per sensor and trial).
3. Split by **whole trials**: trials 1–7 train, trials 8–10 are held out (no leakage).
4. Fit `offset`, `linear` and `quadratic` corrections with NumPy.
5. Compare bias, MAE, RMSE and maximum error on the held-out trials.
6. Failure cases: (a) train on ≤ 50 °C and test above 50 °C; (b) plain vs outlier-trimmed fit.

## Main findings (simulation)

* Sensor A (straight-line error): `linear` is best (held-out RMSE 1.29 → 0.60 °C); `quadratic` adds nothing.
* Sensor B (curved error): `quadratic` is best (2.12 → 0.39 °C); `linear` leaves a U-shaped residual.
* Extrapolation can fail badly: one spike at the edge of the training range made the quadratic fit
  for Sensor B reach 17.1 °C RMSE outside the training range; trimming that spike reduced it to 0.45 °C.
* Results come from one simulated dataset with 3 held-out trials, so they illustrate the method; they
  are not proof about real sensors.

## Team and individual contributions  *(fill in before submitting)*

| Member               | Roll no. | Contribution                                                                                      |
|----------------------|----------|---------------------------------------------------------------------------------------------------|
| 1. Rudranil Banerjee |328       |Project ideation, sensor setup, and simulated reading generation                                   |
| 2. Soham Banerjee    |320       |Data cleaning and calibration model fitting                                                        |
| 3. Sayan Ghosh       |330       |Error metric calculation and failure-case analysis                                                 |
| 4. Ratnandip Mondal  |317       |Pipeline integration , graph plotting and GitHub setup                                             |
| 5. Swapnil Dutta     |300       |Running and verifying all 23 unit tests, compiling the project report, and reviewing final results.|