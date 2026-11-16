"""
plotting.py
===========
Matplotlib figures (CO6). Every figure has a title, axis labels with units
and a legend. The non-interactive "Agg" backend is used so that the program
works on any computer, with or without a display.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SENSOR_NAMES = {"A": "Sensor A (analog, linear error)",
                "B": "Sensor B (thermistor-like, curved error)"}
COLOURS = {"raw": "#c0392b", "corrected": "#1f6f50", "ideal": "#555555"}


def plot_raw_vs_reference(train_df, test_df, fitted, best, path):
    """
    Figure 1: raw reading versus reference temperature, with the ideal y = x
    line and the best correction curve, for each sensor.
    """
    sensors = sorted(train_df["sensor"].unique())
    fig, axes = plt.subplots(1, len(sensors), figsize=(10, 4.2), sharey=False)
    for ax, sensor in zip(np.atleast_1d(axes), sensors):
        tr = train_df[train_df["sensor"] == sensor]
        te = test_df[test_df["sensor"] == sensor]
        lo = min(tr["reference_c"].min(), tr["raw_c"].min()) - 3
        hi = max(tr["reference_c"].max(), te["raw_c"].max()) + 3
        ax.scatter(tr["reference_c"], tr["raw_c"], s=14, alpha=0.55,
                   color="#2e6da4", label="Training readings")
        ax.scatter(te["reference_c"], te["raw_c"], s=18, marker="s",
                   color="#e08e0b", label="Held-out readings")
        ax.plot([lo, hi], [lo, hi], "--", color=COLOURS["ideal"], label="Ideal (raw = reference)")
        # curve: the best method maps raw -> corrected; to show it against
        # reference we plot raw readings that the sensor would give versus
        # corrected output (which should lie on y = x).
        cal = fitted[(sensor, best[sensor])]
        raw_grid = np.linspace(lo, hi, 200)
        ax.plot(cal.predict(raw_grid), raw_grid, color=COLOURS["corrected"], lw=2,
                label=f"Inverse of {best[sensor]} correction")
        ax.set_title(SENSOR_NAMES.get(sensor, sensor), fontsize=10)
        ax.set_xlabel("Reference temperature (°C)")
        ax.set_ylabel("Raw sensor reading (°C)")
        ax.set_xlim(lo, hi)
        ax.grid(alpha=0.25)
        ax.legend(fontsize=7.5, loc="upper left")
    fig.suptitle("Raw sensor readings versus reference thermometer", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_error_histograms(test_df, fitted, best, path):
    """Figure 2: error histograms on held-out data, before and after correction."""
    sensors = sorted(test_df["sensor"].unique())
    fig, axes = plt.subplots(1, len(sensors), figsize=(10, 4.0))
    for ax, sensor in zip(np.atleast_1d(axes), sensors):
        part = test_df[test_df["sensor"] == sensor]
        raw_err = part["raw_c"] - part["reference_c"]
        corrected = fitted[(sensor, best[sensor])].predict(part["raw_c"].to_numpy())
        fixed_err = corrected - part["reference_c"].to_numpy()
        edges = np.linspace(min(raw_err.min(), fixed_err.min()) - 0.2,
                            max(raw_err.max(), fixed_err.max()) + 0.2, 25)
        ax.hist(raw_err, bins=edges, alpha=0.7, color=COLOURS["raw"],
                label=f"Before (RMSE {np.sqrt(np.mean(raw_err ** 2)):.2f} °C)")
        ax.hist(fixed_err, bins=edges, alpha=0.7, color=COLOURS["corrected"],
                label=f"After, {best[sensor]} (RMSE {np.sqrt(np.mean(fixed_err ** 2)):.2f} °C)")
        ax.axvline(0, color="black", lw=0.8)
        ax.set_title(SENSOR_NAMES.get(sensor, sensor), fontsize=10)
        ax.set_xlabel("Error = reading − reference (°C)")
        ax.set_ylabel("Number of held-out readings")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.25)
    fig.suptitle("Held-out error distribution before and after calibration", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_method_comparison(results, path):
    """Figure 3: grouped bar chart of held-out RMSE for each method and sensor."""
    methods = ["none", "offset", "linear", "quadratic"]
    sensors = sorted(results["sensor"].unique())
    width = 0.8 / len(methods)
    x = np.arange(len(sensors))
    palette = ["#7f8c8d", "#2e6da4", "#1f6f50", "#8e44ad"]
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    for i, method in enumerate(methods):
        values = [float(results[(results["sensor"] == s) & (results["method"] == method)]["rmse"].iloc[0])
                  for s in sensors]
        bars = ax.bar(x + (i - 1.5) * width, values, width, label=method, color=palette[i])
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, val + 0.03, f"{val:.2f}",
                    ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([f"Sensor {s}" for s in sensors])
    ax.set_ylabel("Held-out RMSE (°C)")
    ax.set_xlabel("Sensor")
    ax.set_title("Which correction method works best? (lower is better)", fontsize=11)
    ax.set_ylim(0, ax.get_ylim()[1] * 1.22)
    ax.legend(title="Method", ncol=4, loc="upper center", fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_residuals(test_df, fitted, path):
    """
    Figure 4: residual error versus reference temperature for the linear and
    quadratic corrections. A curved pattern shows that a model is too simple.
    """
    sensors = sorted(test_df["sensor"].unique())
    fig, axes = plt.subplots(1, len(sensors), figsize=(10, 4.0), sharey=True)
    for ax, sensor in zip(np.atleast_1d(axes), sensors):
        part = test_df[test_df["sensor"] == sensor]
        ref = part["reference_c"].to_numpy()
        raw = part["raw_c"].to_numpy()
        for method, colour, marker in (("linear", "#2e6da4", "o"), ("quadratic", "#8e44ad", "^")):
            resid = fitted[(sensor, method)].predict(raw) - ref
            ax.scatter(ref, resid, s=18, alpha=0.7, color=colour, marker=marker,
                       label=f"{method} correction")
        ax.axhline(0, color="black", lw=0.8)
        ax.set_title(SENSOR_NAMES.get(sensor, sensor), fontsize=10)
        ax.set_xlabel("Reference temperature (°C)")
        ax.set_ylabel("Residual after correction (°C)")
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8)
    fig.suptitle("Residual error on held-out readings", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
