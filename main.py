"""
main.py
=======
Runs the complete Sensor Calibration Comparison pipeline.

    python main.py                       # uses data/simulated_sensor_readings.csv
    python main.py --data my_file.csv    # use your own CSV (same 4 columns)
    python main.py --out my_outputs      # choose the output folder

Pipeline
--------
 1. read + validate the CSV           (calibration.load_csv)
 2. build CalibrationRun objects      (calibration.group_into_runs)
 3. flatten to a Pandas DataFrame     (analysis.runs_to_dataframe)
 4. summarise trials and sensors      (Pandas groupby)
 5. split into training / held-out trials
 6. fit offset, linear, quadratic corrections (NumPy polyfit)
 7. evaluate on held-out data + two failure-case experiments
 8. draw figures and save CSV / JSON / text outputs
"""

import argparse
import os

import analysis
import calibration
import generate_data
import plotting

DEFAULT_DATA = os.path.join("data", "simulated_sensor_readings.csv")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Sensor calibration comparison")
    parser.add_argument("--data", default=DEFAULT_DATA, help="input CSV file")
    parser.add_argument("--out", default="outputs", help="output folder")
    return parser.parse_args()


def run_pipeline(data_path, out_dir):
    """Run everything and return a dictionary with the main results."""
    os.makedirs(out_dir, exist_ok=True)

    # 1-2. read, validate, create objects
    records, rejected = calibration.load_csv(data_path)
    calibration.write_rejected_log(rejected, os.path.join(out_dir, "rejected_rows.txt"))
    runs = calibration.group_into_runs(records)

    # 3-4. Pandas tables
    df = analysis.runs_to_dataframe(runs)
    trial_summary = analysis.summarise_trials(df)
    sensor_summary = analysis.summarise_sensors(df)

    # 5-6. split and fit
    train_df, test_df, train_trials = analysis.split_trials(df)
    fitted = analysis.fit_calibrators(train_df)

    # 7. evaluate
    results = analysis.evaluate_methods(test_df, fitted)
    best = analysis.best_method_per_sensor(results)
    extrapolation = analysis.extrapolation_experiment(train_df, test_df)
    spikes = analysis.spike_experiment(train_df, test_df)

    # 8. save tables
    trial_summary.to_csv(os.path.join(out_dir, "trial_summary.csv"), index=False)
    sensor_summary.to_csv(os.path.join(out_dir, "sensor_summary.csv"), index=False)
    results.to_csv(os.path.join(out_dir, "heldout_results.csv"), index=False)
    extrapolation.to_csv(os.path.join(out_dir, "extrapolation_results.csv"), index=False)
    spikes.to_csv(os.path.join(out_dir, "spike_results.csv"), index=False)

    # figures
    plotting.plot_raw_vs_reference(train_df, test_df, fitted, best,
                                   os.path.join(out_dir, "fig1_raw_vs_reference.png"))
    plotting.plot_error_histograms(test_df, fitted, best,
                                   os.path.join(out_dir, "fig2_error_histograms.png"))
    plotting.plot_method_comparison(results, os.path.join(out_dir, "fig3_method_comparison.png"))
    plotting.plot_residuals(test_df, fitted, os.path.join(out_dir, "fig4_residuals.png"))

    formulas = {f"{s}/{m}": cal.describe() for (s, m), cal in sorted(fitted.items())}
    payload = {
        "input_rows": len(records) + len(rejected),
        "valid_rows": len(records),
        "rejected_rows": len(rejected),
        "rejected_reasons": [r["reason"] for r in rejected],
        "runs": len(runs),
        "train_trials": [int(t) for t in train_trials],
        "train_readings": int(len(train_df)),
        "test_readings": int(len(test_df)),
        "sensor_summary": sensor_summary.to_dict(orient="records"),
        "heldout_results": results.to_dict(orient="records"),
        "best_method": best,
        "formulas": formulas,
        "extrapolation": extrapolation.to_dict(orient="records"),
        "spike_experiment": spikes.to_dict(orient="records"),
    }
    analysis.save_results(os.path.join(out_dir, "results.json"), payload)
    return payload, trial_summary, sensor_summary, results, extrapolation, spikes


def main():
    args = parse_arguments()
    if not os.path.exists(args.data):
        print(f"{args.data} not found - generating the simulated dataset first.")
        generate_data.main()

    payload, trials, sensors, results, extra, spikes = run_pipeline(args.data, args.out)

    print("\n=== INPUT CHECK ===")
    print(f"rows read: {payload['input_rows']} | valid: {payload['valid_rows']} "
          f"| rejected: {payload['rejected_rows']} | runs: {payload['runs']}")
    print("\n=== RAW SENSOR ERRORS (before calibration) ===")
    print(sensors.to_string(index=False))
    print(f"\nTraining trials: {payload['train_trials']}  "
          f"({payload['train_readings']} readings) | "
          f"held-out readings: {payload['test_readings']}")
    print("\n=== HELD-OUT EVALUATION (lower error = better) ===")
    print(results.to_string(index=False))
    print("\nBest method per sensor:", payload["best_method"])
    print("\n=== FITTED CORRECTIONS ===")
    for name, text in payload["formulas"].items():
        print(f"  {name:<14} {text}")
    print("\n=== EXTRAPOLATION TEST (train <= 50 C, test > 50 C) ===")
    print(extra.to_string(index=False))
    print("\n=== SPIKE-FAULT TEST ===")
    print(spikes.to_string(index=False))
    print(f"\nAll outputs saved in the '{args.out}' folder.")


if __name__ == "__main__":
    main()
