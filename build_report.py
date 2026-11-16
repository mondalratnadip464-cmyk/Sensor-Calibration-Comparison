"""
build_report.py
===============
Builds report/Sensor_Calibration_Report.pdf in the same structure as the
department's sample report. All numbers are read from outputs/results.json and
the CSV tables, so the report always matches the program output.

1. Fill in the TEAM section below.
2. Run   python main.py            (creates outputs/)
3. Run   python report/build_report.py
Needs:  pip install reportlab
"""

import json
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)
from PIL import Image as PILImage

# ----------------------------------------------------------------------------
# FILL THESE IN (leave a list empty to get blank lines on the cover page)
# ----------------------------------------------------------------------------
TEAM_NAMES = ["Rudranil Banerjee", "Soham Banerjee", "Sayan Ghosh", "Ratnadip Mondal", "Swapnil Dutta"]            # e.g. ["Name One", "Name Two"]  (maximum 5)
ROLL_NOS = "328, 320, 330, 317, 300"  # e.g. "12345, 12346"
ENROLLMENT_NOS = "12025052003349, 12025052003341, 12025052003351, 12025052003338, 12025052003321"  # e.g. "12025052003349, 12025052003341"
SUBMITTED_TO = "Prof. Indranil Basu"          # e.g. "Prof. Name Surname"
DATE_OF_SUBMISSION = "20 November 2026"    # e.g. "20 November 2026"
# ----------------------------------------------------------------------------

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")
LOGO = os.path.join(ROOT, "assets", "iem_logo.png")
PDF_PATH = os.path.join(ROOT, "report", "Sensor_Calibration_Report.pdf")
PROJECT_TITLE = "SENSOR CALIBRATION COMPARISON"
NAVY = colors.HexColor("#1F3864")

with open(os.path.join(OUT, "results.json"), encoding="utf-8") as handle:
    R = json.load(handle)

HS = {(r["sensor"], r["method"]): r for r in R["heldout_results"]}
EX = {(r["sensor"], r["method"]): r for r in R["extrapolation"]}
SP = {(r["sensor"], r["fit"]): r for r in R["spike_experiment"]}
SS = {r["sensor"]: r for r in R["sensor_summary"]}
FORM = R["formulas"]


def f2(x):
    return f"{x:.2f}"


# ----------------------------------------------------------------------------
# Styles
# ----------------------------------------------------------------------------
body = ParagraphStyle("body", fontName="Times-Roman", fontSize=10.5, leading=14.2,
                      alignment=TA_JUSTIFY, spaceAfter=6)
h1 = ParagraphStyle("h1", fontName="Times-Bold", fontSize=15, leading=19, textColor=NAVY,
                    spaceBefore=12, spaceAfter=6, keepWithNext=1)
h2 = ParagraphStyle("h2", fontName="Times-Bold", fontSize=11.5, leading=15, textColor=NAVY,
                    spaceBefore=8, spaceAfter=4, keepWithNext=1)
bullet = ParagraphStyle("bullet", parent=body, leftIndent=18, bulletIndent=6, spaceAfter=2)
caption = ParagraphStyle("caption", fontName="Times-Italic", fontSize=9.5, leading=12,
                         alignment=TA_CENTER, spaceAfter=8)
cell = ParagraphStyle("cell", fontName="Times-Roman", fontSize=9.2, leading=11.2)
cellb = ParagraphStyle("cellb", parent=cell, fontName="Times-Bold")
code = ParagraphStyle("code", fontName="Courier", fontSize=8.8, leading=11,
                      leftIndent=14, spaceAfter=6)


def P(text, style=body):
    return Paragraph(text, style)


def bullets(items):
    return [Paragraph(t, bullet, bulletText="\u2022") for t in items]


def table(rows, widths, header=True, align_numbers=False):
    data = []
    for r_index, row in enumerate(rows):
        style = cellb if (header and r_index == 0) else cell
        data.append([Paragraph(str(c), style) for c in row])
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1 if header else 0)
    commands = [("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
    if header:
        commands.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF7")))
    t.setStyle(TableStyle(commands))
    return [t, Spacer(1, 7)]


def figure(filename, caption_text, width_cm=16.0):
    path = os.path.join(OUT, filename)
    w, h = PILImage.open(path).size
    img = Image(path, width=width_cm * cm, height=width_cm * cm * h / w)
    return [img, P(caption_text, caption)]


# ----------------------------------------------------------------------------
# Cover page and page furniture (drawn on the canvas)
# ----------------------------------------------------------------------------
def draw_cover(canvas, doc):
    width, height = A4
    canvas.saveState()
    canvas.setLineWidth(3.2)
    canvas.rect(28, 28, width - 56, height - 56)
    canvas.setLineWidth(1)
    canvas.rect(35, 35, width - 70, height - 70)

    logo_w = 150
    with PILImage.open(LOGO) as im:
        lw, lh = im.size
    canvas.drawImage(LOGO, (width - logo_w) / 2, height - 60 - logo_w * lh / lw, width=logo_w,
                     height=logo_w * lh / lw, mask="auto")

    canvas.setFont("Times-Bold", 22)
    canvas.drawCentredString(width / 2, height - 255, "INSTITUTE OF ENGINEERING &")
    canvas.drawCentredString(width / 2, height - 284, "MANAGEMENT, KOLKATA")

    x0 = 55

    def label_value(y, label, value):
        canvas.setFont("Times-Bold", 11.5)
        canvas.drawString(x0, y, label)
        label_w = canvas.stringWidth(label, "Times-Bold", 11.5)
        canvas.setFont("Times-Roman", 11.5)
        canvas.drawString(x0 + label_w + 6, y, value)

    def blank_line(y, label, value, line_len):
        canvas.setFont("Times-Bold", 11.5)
        canvas.drawString(x0, y, label)
        label_w = canvas.stringWidth(label, "Times-Bold", 11.5)
        start = x0 + label_w + 6
        canvas.setFont("Times-Roman", 11.5)
        if value:
            canvas.drawString(start + 2, y + 2, value)
        canvas.line(start, y - 2, start + line_len, y - 2)

    y = height - 350
    label_value(y, "COURSE TITLE:", "BACHELOR OF TECHNOLOGY")
    y -= 38
    label_value(y, "SUBJECT:", "PYTHON PROGRAMMING LABORATORY")
    y -= 38
    label_value(y, "PROJECT TITLE:", PROJECT_TITLE)
    y -= 42

    # names: 2 on the first row, 3 on the second row
    canvas.setFont("Times-Bold", 11.5)
    canvas.drawString(x0, y, "NAME:")
    slots = [(x0 + 68, y, 115), (x0 + 225, y, 115)]
    row2 = y - 26
    slots += [(x0 + 22, row2, 100), (x0 + 175, row2, 100), (x0 + 325, row2, 100)]
    for index, (sx, sy, length) in enumerate(slots):
        canvas.setFont("Times-Roman", 11.5)
        canvas.drawString(sx - 15, sy, f"{index + 1}.")
        canvas.line(sx, sy - 2, sx + length, sy - 2)
        if index < len(TEAM_NAMES):
            canvas.drawString(sx + 2, sy + 2, TEAM_NAMES[index])
    y = row2 - 40
    blank_line(y, "ROLL NO:", ROLL_NOS, 220)
    y -= 38
    blank_line(y, "ENROLLMENT NO:", ENROLLMENT_NOS, 230)
    y -= 38
    label_value(y, "SECTION:", "B")
    y -= 38
    blank_line(y, "SUBMITTED TO:", SUBMITTED_TO, 220)
    y -= 38
    label_value(y, "DEPARTMENT NAME:", "ELECTRONICS AND COMMUNICATION ENGINEERING")
    y -= 38
    label_value(y, "ACADEMIC SESSION:", "2026-2027")
    y -= 38
    blank_line(y, "DATE OF SUBMISSION:", DATE_OF_SUBMISSION, 150)
    canvas.restoreState()


def draw_page(canvas, doc):
    width, height = A4
    canvas.saveState()
    canvas.setFont("Times-Roman", 8)
    canvas.setFillColor(colors.HexColor("#6b7280"))
    canvas.drawRightString(width - 2 * cm, height - 1.3 * cm, PROJECT_TITLE)
    canvas.setFillColor(colors.black)
    canvas.setFont("Times-Roman", 8.5)
    canvas.drawCentredString(width / 2, 1.2 * cm,
                             f"Department of Electronics and Communication Engineering  |  Page {doc.page}")
    canvas.restoreState()


# ----------------------------------------------------------------------------
# Content
# ----------------------------------------------------------------------------
def build_story():
    s = [PageBreak()]          # page 1 (cover) is drawn on the canvas

    a_none, a_lin = HS[("A", "none")]["rmse"], HS[("A", "linear")]["rmse"]
    b_none, b_quad = HS[("B", "none")]["rmse"], HS[("B", "quadratic")]["rmse"]

    # ---- Abstract -----------------------------------------------------------
    s += [P("Abstract", h1)]
    s.append(P(
        "This project develops a Python program that compares raw temperature readings from two "
        "sensors with a trusted reference thermometer, learns a correction for each sensor, and "
        "tests whether the correction really reduces the error on trials that were not used for "
        "fitting. It combines procedural functions, dictionaries and CSV handling, object-oriented "
        "programming, NumPy curve fitting, Pandas summaries and Matplotlib figures."))
    s.append(P(
        f"The demonstration dataset is <b>simulated</b> with a fixed random seed and is not a "
        f"measurement from real sensors. From {R['input_rows']} input rows, {R['valid_rows']} pass "
        f"validation and {R['rejected_rows']} are rejected. Trials {R['train_trials'][0]}-"
        f"{R['train_trials'][-1]} are used for fitting and the remaining trials are held out. On the "
        f"held-out readings, a linear correction reduces the RMSE of Sensor A from {f2(a_none)} to "
        f"{f2(a_lin)} \u00b0C, and a quadratic correction reduces the RMSE of Sensor B from "
        f"{f2(b_none)} to {f2(b_quad)} \u00b0C. Two failure cases are also analysed: extrapolation "
        f"outside the calibrated range and spike faults in the training data. The results show "
        f"that the best correction model depends on the sensor's error shape and that an "
        f"over-flexible model can fail badly when it is used outside its training range."))
    s += [P("Keywords", h1),
          P("Sensor calibration; offset and gain error; polynomial fitting; held-out evaluation; "
            "outlier trimming; Python; NumPy; Pandas; Matplotlib; CSV.")]
    s += [P("Table of Contents", h1)]
    toc = ["1. Introduction", "2. Problem Statement and Objectives", "3. Software and System Requirements",
           "4. System Design and Methodology", "5. Implementation of Major Modules",
           "6. Results and Discussion", "7. Testing and Validation", "8. Limitations and Future Scope",
           "9. Conclusion", "10. References", "11. Appendix: CSV Format, Execution and Contributions"]
    s += [P(t, ParagraphStyle("toc", parent=body, leftIndent=6, spaceAfter=3, alignment=0)) for t in toc]
    s.append(PageBreak())

    # ---- 1 Introduction -----------------------------------------------------
    s += [P("1. Introduction", h1)]
    s.append(P(
        "Electronic sensors rarely report the true value of the quantity they measure. Typical "
        "imperfections are an <b>offset</b> (a constant error), a <b>gain error</b> (an error that "
        "grows with the measured value) and <b>non-linearity</b> (a curved response). Calibration "
        "compares the sensor with a trusted reference over a range of known values and then "
        "derives a mathematical correction that is applied to later readings."))
    s.append(P(
        "A correction that looks excellent on the data used to build it can still perform poorly "
        "on new data. This project therefore focuses on one question: <i>does the correction "
        "improve the error on held-out trials, and which correction model is the most appropriate?</i> "
        "The program reads paired readings from a CSV file, validates them, stores each trial as an "
        "object, fits three candidate corrections, compares them on unseen trials, and draws "
        "labelled figures for interpretation."))
    s.append(P(
        "<b>Data notice.</b> The included readings are generated by a mathematical procedure "
        "(generate_data.py, seed 2026). All numerical results are therefore examples of the program's "
        "behaviour and not empirical findings about real sensors. The program also accepts a user's "
        "own CSV file with the same four columns."))

    # ---- 2 Problem statement ------------------------------------------------
    s += [P("2. Problem Statement and Objectives", h1)]
    s.append(P(
        "Problem statement: Compare raw sensor measurements against known reference values. Validate "
        "paired readings; store runs in CSV; implement a CalibrationRun class; use NumPy to estimate "
        "offset, scale and error; use Pandas to summarise repeated trials; plot raw and corrected "
        "scatter and error histograms; and evaluate whether the correction improves error on "
        "held-out samples, discussing limitations."))
    s.append(P("The principal objectives are:"))
    s += bullets([
        "Validate paired (reference, raw) readings and reject missing, non-numeric and out-of-range values.",
        "Read and write structured data as CSV, JSON and a plain-text rejected-rows log.",
        "Represent each trial with a CalibrationRun class that supports len(), indexing and iteration.",
        "Estimate offset, linear (gain + offset) and quadratic corrections with NumPy and compute bias, MAE, RMSE and maximum error.",
        "Summarise repeated trials with Pandas group-by operations and split the data by whole trials.",
        "Plot raw-versus-reference scatter, error histograms, a method comparison and residual plots.",
        "Analyse failure cases (extrapolation, spike faults) and state the limitations honestly.",
    ])

    # ---- 3 Software ---------------------------------------------------------
    s += [P("3. Software and System Requirements", h1)]
    s += table([
        ["Component", "Purpose"],
        ["Python 3 (3.10 or later)", "Core program execution"],
        ["csv, math, os, json, argparse", "CSV handling, validation, file paths, JSON output, command-line options"],
        ["NumPy", "Arrays, polynomial fitting (polyfit/polyval), vectorised error metrics, MAD outlier rule"],
        ["Pandas", "DataFrames, group-by summaries, train/test split, CSV export"],
        ["Matplotlib", "Scatter plots, histograms, bar chart and residual plots"],
        ["unittest", "Automated tests (part of the standard library)"],
        ["Git and GitHub", "Version control and submission"],
    ], [6.0, 10.5])
    s.append(P("The program runs on any desktop with Python and the three third-party libraries "
               "(numpy, pandas, matplotlib). It uses the non-interactive Matplotlib backend, so no "
               "display is needed."))

    # ---- 4 Design -----------------------------------------------------------
    s += [P("4. System Design and Methodology", h1), P("4.1 Input data and schema", h2)]
    s.append(P(
        "Each record has four fields: <b>sensor</b> (identifier such as A or B), <b>trial</b> "
        "(whole number, 1 or more), <b>reference_c</b> (reference temperature in \u00b0C) and "
        "<b>raw_c</b> (the sensor's reading in \u00b0C). A row is valid when the sensor id is "
        "non-empty, the trial is a whole number of at least 1, and both temperatures are finite "
        "numbers within the sensor range of -40 to 125 \u00b0C. Invalid rows are skipped and "
        "written to outputs/rejected_rows.txt with the line number and reason."))
    s += [P("4.2 Data preparation (simulation)", h2)]
    s.append(P(
        "Reference temperatures run from 20 to 80 \u00b0C in 5 \u00b0C steps (13 points) and each "
        "sensor is tested in 10 trials. Sensor A is simulated with a gain of 1.04, an offset of "
        "-3.0 \u00b0C and noise of 0.35 \u00b0C (a straight-line error). Sensor B is simulated with "
        "a gain of 0.98, an offset of +1.2 \u00b0C, a curvature term and noise of 0.30 \u00b0C "
        "(a curved error). Five deliberately invalid rows and four spike faults of 8 to 15 \u00b0C "
        "are added. The spikes are placed only in the training trials so that the effect of "
        "contaminated calibration data can be studied in a controlled way."))
    s += [P("4.3 Analysis workflow", h2)]
    for i, step in enumerate([
            "Read the CSV with csv.DictReader and validate each row.",
            "Group valid records into CalibrationRun objects, one per sensor and trial.",
            "Flatten the runs into a Pandas DataFrame and compute the raw error (reading - reference).",
            "Summarise the repeated trials and sensors with group-by operations.",
            f"Split by whole trials: trials {R['train_trials'][0]}-{R['train_trials'][-1]} for training, "
            "the others held out (no reading of a test trial is used for fitting).",
            "Fit offset, linear and quadratic corrections for each sensor using only the training data.",
            "Evaluate on the held-out readings, run the two failure-case experiments, save tables and figures."], 1):
        s.append(P(f"{i}. {step}", ParagraphStyle("step", parent=body, leftIndent=14, spaceAfter=1.5)))
    s += [P("4.4 Correction models and error measures", h2)]
    s.append(P(
        "The correction maps a raw reading to a corrected value. <b>Offset:</b> corrected = raw + b, "
        "where b is the mean of (reference - raw). <b>Linear:</b> corrected = a x raw + b, fitted by "
        "least squares. <b>Quadratic:</b> corrected = a x raw<super>2</super> + b x raw + c. The "
        "error of a reading is (value - reference). The program reports <b>bias</b> (mean error), "
        "<b>MAE</b> (mean absolute error), <b>RMSE</b> (root-mean-square error) and the "
        "<b>maximum absolute error</b>. The improvement is the percentage reduction of RMSE "
        "compared with using no correction."))
    s.append(P(
        "To protect the fit against spike faults, an optional trimming step flags a training point when its "
        "residual is more than 3.5 robust standard deviations from the median residual, where the robust "
        "standard deviation is 1.4826 times the median absolute deviation (MAD). The fit is then repeated "
        "without the flagged points. The median-based rule is used because the ordinary mean and standard "
        "deviation are themselves distorted by the outliers."))

    # ---- 5 Implementation ---------------------------------------------------
    s += [P("5. Implementation of Major Modules", h1)]
    s += table([
        ["Module / function", "Functionality"],
        ["calibration.py: parse_float(), is_valid_reading(), parse_trial(), validate_row()", "Row validation with clear rejection reasons"],
        ["calibration.py: load_csv(), write_rejected_log()", "CSV import with DictReader; text log of rejected rows"],
        ["calibration.py: CalibrationRun, group_into_runs()", "Object-oriented storage of one trial; grouping with a dictionary of lists"],
        ["calibration.py: Calibrator (fit, predict, describe)", "Offset, linear and quadratic corrections with optional trimming"],
        ["calibration.py: bias(), mae(), rmse(), max_abs_error(), residual_outlier_mask()", "Vectorised NumPy error measures and robust outlier rule"],
        ["analysis.py: runs_to_dataframe(), summarise_trials(), summarise_sensors()", "Pandas tables and group-by summaries"],
        ["analysis.py: split_trials(), fit_calibrators(), evaluate_methods()", "Leak-free split by trial; held-out evaluation"],
        ["analysis.py: extrapolation_experiment(), spike_experiment()", "Failure-case experiments"],
        ["plotting.py: four plot functions", "Embedded, labelled Matplotlib figures"],
        ["main.py: run_pipeline()", "End-to-end pipeline and saved outputs"],
        ["generate_data.py, test_calibration.py", "Reproducible simulated data; 23 automated tests"],
    ], [8.6, 7.9])
    s += [P("5.1 The CalibrationRun class and its special methods", h2)]
    s += table([
        ["Special method", "What it does", "Why it is used"],
        ["__init__", "Converts inputs to float arrays; checks equal non-zero length", "An invalid or empty run can never exist"],
        ["__len__", "Number of paired readings", "Allows len(run) in checks instead of reaching into the object"],
        ["__getitem__", "run[i] gives (reference, raw); run[a:b] gives a list of pairs", "A run behaves like a sequence of measurements"],
        ["__iter__", "Yields (reference, raw) pairs", "Allows  for ref, raw in run  and is used when building the DataFrame"],
    ], [3.0, 6.5, 7.0])
    s.append(P(
        "The Calibrator class stores the fitted polynomial coefficients. All three methods use the same "
        "storage and prediction code (np.polyval): the offset model is the polynomial [1, b], so the "
        "model choice changes only how the coefficients are found."))

    # ---- 6 Results ----------------------------------------------------------
    s += [P("6. Results and Discussion", h1), P("6.1 Data quality and raw sensor errors", h2)]
    s.append(P("The following results were computed from the fixed-seed simulated dataset. They will differ "
               "if another CSV is used."))
    s += table([
        ["Indicator", "Observed value"],
        ["Input rows", R["input_rows"]], ["Valid records", R["valid_rows"]],
        ["Rejected rows", R["rejected_rows"]], ["Calibration runs (sensor x trial)", R["runs"]],
        ["Training trials", f"{R['train_trials'][0]}-{R['train_trials'][-1]} ({R['train_readings']} readings)"],
        ["Held-out readings", R["test_readings"]],
    ], [8.0, 8.5])
    s += table([
        ["Sensor", "Readings", "Mean error (\u00b0C)", "Std. dev. (\u00b0C)", "Min error (\u00b0C)", "Max error (\u00b0C)"],
        *[[k, SS[k]["readings"], f2(SS[k]["mean_error"]), f2(SS[k]["std_error"]),
           f2(SS[k]["min_error"]), f2(SS[k]["max_error"])] for k in ("A", "B")],
    ], [2.2, 2.4, 3.0, 3.0, 3.0, 2.9])
    s.append(P("The second table summarises the uncorrected errors over all valid readings. The extreme values "
               "include the injected spike faults, which are visible as isolated points in Figure 1."))
    s += figure("fig1_raw_vs_reference.png",
                "Figure 1. Raw readings versus reference temperature, with the ideal line and the best correction.")

    s += [P("6.2 Held-out evaluation of the correction methods", h2)]
    rows = [["Sensor", "Method", "Bias (\u00b0C)", "MAE (\u00b0C)", "RMSE (\u00b0C)", "Max |error| (\u00b0C)", "RMSE reduction"]]
    for sensor in ("A", "B"):
        for method in ("none", "offset", "linear", "quadratic"):
            r = HS[(sensor, method)]
            rows.append([sensor, method, f2(r["bias"]), f2(r["mae"]), f2(r["rmse"]), f2(r["max_abs"]),
                         "-" if method == "none" else f"{r['improvement_pct']:.1f}%"])
    s += table(rows, [1.5, 2.4, 2.2, 2.2, 2.4, 3.0, 2.8])
    s += figure("fig2_error_histograms.png", "Figure 2. Error distribution on held-out readings before and after the best correction.")
    s += figure("fig3_method_comparison.png", "Figure 3. Held-out RMSE for each method and sensor (lower is better).", 12.5)
    s.append(P(
        f"<b>Sensor A.</b> The offset correction removes the bias and lowers the RMSE from {f2(a_none)} to "
        f"{f2(HS[('A', 'offset')]['rmse'])} \u00b0C, but the error still changes with temperature. The linear "
        f"correction (gain and offset) reduces the RMSE further to {f2(a_lin)} \u00b0C. The quadratic correction "
        f"({f2(HS[('A', 'quadratic')]['rmse'])} \u00b0C) is no better, so the simpler linear model is the "
        f"appropriate choice for this sensor."))
    s.append(P(
        f"<b>Sensor B.</b> Offset and linear corrections reach only about {f2(HS[('B', 'linear')]['rmse'])} \u00b0C "
        f"because the error is curved. The quadratic correction reduces the RMSE from {f2(b_none)} to {f2(b_quad)} \u00b0C "
        f"({HS[('B', 'quadratic')]['improvement_pct']:.1f}% reduction). The residual plot (Figure 4) shows why: the linear residuals "
        f"form a U-shape, which is the typical sign of a model that is too simple, while the quadratic residuals are scattered "
        f"around zero. For Sensor A the linear residuals show a gentle downward trend; the spike experiment in Section 6.4 "
        f"indicates that the injected faults contribute to this trend."))
    s += figure("fig4_residuals.png", "Figure 4. Residual error after linear and quadratic correction on held-out readings.")
    s += table([
        ["Sensor / model", "Fitted correction (raw reading to corrected value)"],
        *[[k, FORM[k].replace("corrected = ", "").replace("^2", "<super>2</super>").replace("+ -", "- ")] for k in
          ("A/offset", "A/linear", "A/quadratic", "B/offset", "B/linear", "B/quadratic")],
    ], [4.0, 12.5])

    s += [P("6.3 Failure case 1: extrapolation outside the calibrated range", h2)]
    s.append(P("Here each model is trained only on training readings with a reference of at most 50 \u00b0C "
               "and tested on held-out readings above 50 \u00b0C. This imitates calibrating a sensor on part of its range "
               "and then using it elsewhere."))
    rows = [["Sensor", "Method", "RMSE (\u00b0C)", "Max |error| (\u00b0C)"]]
    for sensor in ("A", "B"):
        for method in ("none", "offset", "linear", "quadratic", "quadratic+trim"):
            r = EX[(sensor, method)]
            rows.append([sensor, method, f2(r["rmse"]), f2(r["max_abs"])])
    s += table(rows, [2.2, 4.0, 4.0, 4.5])
    s.append(P(
        f"The results are sobering. For Sensor B the quadratic model reaches an RMSE of {f2(EX[('B', 'quadratic')]['rmse'])} \u00b0C, "
        f"far worse than using no correction ({f2(EX[('B', 'none')]['rmse'])} \u00b0C). Refitting the same model after trimming one "
        f"flagged point reduces the RMSE to {f2(EX[('B', 'quadratic+trim')]['rmse'])} \u00b0C. This suggests that a single spike "
        f"(+13.55 \u00b0C at 50 \u00b0C, trial 2), which sits at the edge of the training range, was responsible: a flexible curve "
        f"fitted to half of its range extrapolates such a point into a large error. For Sensor A, the offset learned from the lower "
        f"half ({f2(EX[('A', 'offset')]['rmse'])} \u00b0C) is worse than no correction ({f2(EX[('A', 'none')]['rmse'])} \u00b0C), because "
        f"the true error changes sign across the range. A correction should therefore only be used inside the range in which it "
        f"was calibrated."))

    s += [P("6.4 Failure case 2: spike faults in the training data", h2)]
    rows = [["Sensor", "Fit", "Training points trimmed", "Held-out RMSE (\u00b0C)", "Held-out max |error| (\u00b0C)"]]
    for sensor in ("A", "B"):
        for fit in ("linear", "linear+trim"):
            r = SP[(sensor, fit)]
            rows.append([sensor, fit, r["trimmed_points"], f2(r["test_rmse"]), f2(r["test_max_abs"])])
    s += table(rows, [2.0, 3.2, 4.0, 3.6, 3.7])
    s.append(P(
        f"For Sensor A the trimmed linear fit lowers the held-out RMSE from {f2(SP[('A', 'linear')]['test_rmse'])} to "
        f"{f2(SP[('A', 'linear+trim')]['test_rmse'])} \u00b0C after removing {SP[('A', 'linear+trim')]['trimmed_points']} suspect points, "
        f"so a few faulty readings noticeably distorted the ordinary least-squares line. For Sensor B, trimming has almost no effect on "
        f"the linear model because its main limitation is the curved response, not the spike. The MAD rule flags statistical extremes; "
        f"a flagged reading is not automatically a mistake, so removed points should be inspected and reported."))

    s += [P("6.5 Evaluation of the design choices", h2)]
    s += bullets([
        "<b>Splitting by whole trials</b> prevents a test reading from being fitted by a training reading of the same trial.",
        "<b>Choosing the model by held-out RMSE</b> avoids rewarding a model merely for flexibility; the quadratic model "
        "is chosen for Sensor B but not for Sensor A, where it gives no benefit.",
        "<b>Offset-only correction</b> is cheap but can only fix a constant error; its benefit for Sensor B is limited.",
        "<b>Trimming</b> helps when the training data contain faults, but needs inspection because it can remove genuine data.",
    ])
    s.append(P(
        "These conclusions come from one simulated dataset with three held-out trials per sensor. They demonstrate "
        "the method but do not prove how the models would behave on real hardware."))

    # ---- 7 Testing ----------------------------------------------------------
    s += [P("7. Testing and Validation", h1)]
    s += table([
        ["Test case", "Expected behaviour", "Observed"],
        ["Blank raw reading", "Row rejected", "Rejected"],
        ["Fault code 999 \u00b0C", "Reading outside range rejected", "Rejected"],
        ["Missing sensor id / trial = 0 / text reference", "Row rejected with a reason", "Rejected (3 rows)"],
        ["CSV with a missing column", "ValueError raised", "Passed"],
        ["CalibrationRun with unequal or empty arrays", "ValueError raised", "Passed"],
        ["len(), run[i], run[a:b], iteration", "Correct values", "Passed"],
        ["Noiseless linear sensor", "Linear fit recovers reference exactly", "Passed"],
        ["Constant-offset sensor", "Offset model removes the error", "Passed"],
        ["Curved sensor", "Quadratic clearly better than linear", "Passed"],
        ["Spike in training data", "Trimmed fit flags 1 point and is more accurate", "Passed"],
        ["Train/test split", "No trial appears in both sets", "Passed"],
        ["Sample dataset", f"{R['valid_rows']} valid, {R['rejected_rows']} rejected; every correction beats no correction", "Passed"],
    ], [5.6, 6.6, 4.3])
    s.append(P("All 23 unit tests pass (python -m unittest -v; log saved in outputs/test_results.txt). "
               "Every figure and table in this report is produced by main.py, and the data are generated with a fixed "
               "seed, so the results can be reproduced exactly."))

    # ---- 8 Limitations ------------------------------------------------------
    s += [P("8. Limitations and Future Scope", h1)]
    s.append(P(
        "Limitations: (i) the observations are simulated; (ii) only two sensors, a 20-80 \u00b0C range and three held-out trials "
        "are used, so the conclusions are indicative; (iii) the calibration ignores drift with time, humidity and self-heating; "
        "(iv) the 3.5 x MAD threshold and the 70/30 split are exploratory choices; (v) the reference thermometer is assumed to be "
        "exact, although in practice it has its own uncertainty."))
    s.append(P(
        "Possible extensions: calibrate real hardware (for example an LM35 or thermistor with a microcontroller) against a "
        "reference thermometer; repeat the experiment with many random seeds to measure how stable the best-model choice is; add "
        "cross-validation across trials; estimate uncertainty intervals for the coefficients; add a cubic or lookup-table model; "
        "and provide a simple graphical interface."))

    # ---- 9 Conclusion -------------------------------------------------------
    s += [P("9. Conclusion", h1)]
    s.append(P(
        "The project delivers a complete, reproducible workflow for comparing sensor calibration methods: validated CSV input, "
        "object-oriented trial storage, NumPy fitting, Pandas summaries, held-out evaluation and labelled figures. On the simulated "
        f"data, the linear correction suited the straight-line error of Sensor A ({f2(a_none)} to {f2(a_lin)} \u00b0C RMSE) and the "
        f"quadratic correction suited the curved error of Sensor B ({f2(b_none)} to {f2(b_quad)} \u00b0C). The failure-case analysis "
        "shows that a correction must be judged on unseen data, must not be trusted outside its calibrated range, and can be damaged by "
        "a few faulty training points. The central conclusion is therefore cautious: calibration helps, but the choice of model and the "
        "quality of the calibration data decide whether it helps safely."))

    # ---- 10 References ------------------------------------------------------
    s += [P("10. References", h1)]
    for ref in [
        "Python Software Foundation. Python 3 Documentation (csv, unittest, argparse). https://docs.python.org/3/",
        "NumPy Developers. NumPy Documentation (numpy.polyfit, numpy.polyval). https://numpy.org/doc/",
        "Pandas Development Team. pandas Documentation. https://pandas.pydata.org/docs/",
        "Matplotlib Development Team. Matplotlib Documentation. https://matplotlib.org/stable/",
        "JCGM 100:2008. Evaluation of measurement data - Guide to the expression of uncertainty in measurement (GUM). BIPM.",
        "Leys, C., Ley, C., Klein, O., Bernard, P. and Licata, L. (2013). Detecting outliers: Do not use standard deviation around "
        "the mean, use absolute deviation around the median. Journal of Experimental Social Psychology, 49(4), 764-766.",
    ]:
        s.append(P(ref, ParagraphStyle("ref", parent=body, alignment=0, spaceAfter=3)))

    # ---- 11 Appendix --------------------------------------------------------
    s += [P("11. Appendix: CSV Format, Execution and Contributions", h1)]
    s.append(P("Required input CSV headers (exact spelling): sensor, trial, reference_c, raw_c. Temperatures are in \u00b0C."))
    s += table([["sensor", "trial", "reference_c", "raw_c"],
                ["A", "1", "20.0", "18.2"], ["A", "1", "25.0", "23.4"], ["B", "1", "20.0", "24.9"]],
               [4.0, 3.0, 4.5, 5.0])
    s.append(P("To run the project:"))
    s += [P("pip install numpy pandas matplotlib", code),
          P("python generate_data.py     # optional: recreate the simulated CSV", code),
          P("python main.py              # full analysis; saves tables and figures to outputs/", code),
          P("python -m unittest -v       # run the 23 tests", code),
          P("python report/build_report.py   # rebuild this report (needs reportlab)", code)]
    s.append(P("Use <font name='Courier'>python main.py --data your_file.csv</font> to analyse a different CSV file. "
               "The repository contains the source code, data, outputs, README and this report."))
    s.append(P("Individual contributions", h2))
    s += table([["Member", "Roll no.", "Contribution"], ["1.", "", ""], ["2.", "", ""], ["3.", "", ""]], [3.0, 3.5, 10.0])
    return s


def main():
    doc = SimpleDocTemplate(PDF_PATH, pagesize=A4, leftMargin=2.2 * cm, rightMargin=2.2 * cm,
                            topMargin=2.0 * cm, bottomMargin=2.0 * cm,
                            title="Sensor Calibration Comparison - Project Report",
                            author="Python Programming Laboratory, IEM Kolkata")
    doc.build(build_story(), onFirstPage=draw_cover, onLaterPages=draw_page)
    print("Report written to", PDF_PATH)


if __name__ == "__main__":
    main()
