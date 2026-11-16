"""
test_calibration.py
===================
Automated tests. Run with:   python -m unittest -v
"""

import os
import tempfile
import unittest

import numpy as np

import analysis
import calibration as cal


class TestValidation(unittest.TestCase):
    def test_parse_float_good_and_bad(self):
        self.assertEqual(cal.parse_float(" 12.5 "), 12.5)
        self.assertIsNone(cal.parse_float(""))
        self.assertIsNone(cal.parse_float("abc"))
        self.assertIsNone(cal.parse_float("nan"))
        self.assertIsNone(cal.parse_float(None))

    def test_is_valid_reading_range(self):
        self.assertTrue(cal.is_valid_reading(25.0))
        self.assertFalse(cal.is_valid_reading(999.0))     # fault code
        self.assertFalse(cal.is_valid_reading(None))

    def test_validate_row_accepts_good_row(self):
        row = {"sensor": "A", "trial": "2", "reference_c": "40", "raw_c": "41.2"}
        record, reason = cal.validate_row(row)
        self.assertEqual(reason, "")
        self.assertEqual(record["trial"], 2)
        self.assertAlmostEqual(record["raw_c"], 41.2)

    def test_validate_row_rejects_bad_rows(self):
        bad_rows = [
            {"sensor": "", "trial": "1", "reference_c": "40", "raw_c": "41"},
            {"sensor": "A", "trial": "0", "reference_c": "40", "raw_c": "41"},
            {"sensor": "A", "trial": "1.5", "reference_c": "40", "raw_c": "41"},
            {"sensor": "A", "trial": "1", "reference_c": "abc", "raw_c": "41"},
            {"sensor": "A", "trial": "1", "reference_c": "40", "raw_c": ""},
            {"sensor": "A", "trial": "1", "reference_c": "40", "raw_c": "999"},
        ]
        for row in bad_rows:
            record, reason = cal.validate_row(row)
            self.assertIsNone(record, msg=str(row))
            self.assertNotEqual(reason, "")


class TestLoadCsv(unittest.TestCase):
    def test_load_csv_counts_valid_and_rejected(self):
        text = ("sensor,trial,reference_c,raw_c\n"
                "A,1,20,21.0\n"
                "A,1,25,\n"            # blank raw -> rejected
                "B,1,30,31.5\n")
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "t.csv")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text)
            records, rejected = cal.load_csv(path)
        self.assertEqual(len(records), 2)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["line"], 3)      # header is line 1

    def test_missing_column_raises(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "t.csv")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("sensor,trial,reference_c\nA,1,20\n")
            with self.assertRaises(ValueError):
                cal.load_csv(path)


class TestCalibrationRun(unittest.TestCase):
    def setUp(self):
        self.run = cal.CalibrationRun("A", 1, [10, 20, 30], [11, 22, 33])

    def test_len(self):
        self.assertEqual(len(self.run), 3)

    def test_getitem_index_and_slice(self):
        self.assertEqual(self.run[1], (20.0, 22.0))
        self.assertEqual(self.run[0:2], [(10.0, 11.0), (20.0, 22.0)])

    def test_iter(self):
        self.assertEqual(list(self.run), [(10.0, 11.0), (20.0, 22.0), (30.0, 33.0)])

    def test_errors_and_mean_error(self):
        np.testing.assert_allclose(self.run.errors(), [1, 2, 3])
        self.assertAlmostEqual(self.run.mean_error(), 2.0)

    def test_invalid_construction(self):
        with self.assertRaises(ValueError):
            cal.CalibrationRun("A", 1, [1, 2], [1])
        with self.assertRaises(ValueError):
            cal.CalibrationRun("A", 1, [], [])

    def test_group_into_runs(self):
        records = [
            {"sensor": "A", "trial": 1, "reference_c": 10.0, "raw_c": 11.0},
            {"sensor": "A", "trial": 2, "reference_c": 10.0, "raw_c": 12.0},
            {"sensor": "A", "trial": 1, "reference_c": 20.0, "raw_c": 21.0},
        ]
        runs = cal.group_into_runs(records)
        self.assertEqual([len(r) for r in runs], [2, 1])


class TestMetrics(unittest.TestCase):
    def test_metrics_on_known_values(self):
        err = np.array([3.0, -4.0])
        self.assertAlmostEqual(cal.bias(err), -0.5)
        self.assertAlmostEqual(cal.mae(err), 3.5)
        self.assertAlmostEqual(cal.rmse(err), np.sqrt(12.5))
        self.assertAlmostEqual(cal.max_abs_error(err), 4.0)

    def test_outlier_mask_flags_spike(self):
        residuals = np.array([0.1, -0.1, 0.05, -0.05, 0.0, 12.0])
        mask = cal.residual_outlier_mask(residuals)
        self.assertEqual(mask.tolist(), [False] * 5 + [True])


class TestCalibrator(unittest.TestCase):
    def setUp(self):
        self.ref = np.linspace(20, 80, 13)

    def test_linear_recovers_exact_gain_and_offset(self):
        raw = 1.05 * self.ref - 2.0                      # noiseless sensor
        model = cal.Calibrator("linear").fit(raw, self.ref)
        np.testing.assert_allclose(model.predict(raw), self.ref, atol=1e-8)

    def test_offset_removes_constant_error(self):
        raw = self.ref + 1.5
        model = cal.Calibrator("offset").fit(raw, self.ref)
        np.testing.assert_allclose(model.predict(raw), self.ref, atol=1e-8)

    def test_quadratic_recovers_curved_sensor(self):
        raw = self.ref + 0.003 * (self.ref - 50) ** 2 + 1.0
        quad = cal.Calibrator("quadratic").fit(raw, self.ref)
        lin = cal.Calibrator("linear").fit(raw, self.ref)
        e_quad = cal.rmse(quad.predict(raw) - self.ref)
        e_lin = cal.rmse(lin.predict(raw) - self.ref)
        # the exact inverse of a quadratic is not a quadratic, so we do not expect
        # zero error - but the quadratic must be small and clearly better than linear
        self.assertLess(e_quad, 0.15)
        self.assertLess(e_quad, 0.5 * e_lin)

    def test_trim_resists_a_spike(self):
        raw = 1.02 * self.ref - 1.0
        raw[6] += 15.0                                   # one spike fault
        plain = cal.Calibrator("linear").fit(raw, self.ref)
        trimmed = cal.Calibrator("linear", trim=True).fit(raw, self.ref)
        good = np.delete(np.arange(raw.size), 6)
        e_plain = cal.rmse(plain.predict(raw[good]) - self.ref[good])
        e_trim = cal.rmse(trimmed.predict(raw[good]) - self.ref[good])
        self.assertEqual(trimmed.n_trimmed, 1)
        self.assertLess(e_trim, e_plain)

    def test_error_handling(self):
        with self.assertRaises(ValueError):
            cal.Calibrator("cubic")
        with self.assertRaises(RuntimeError):
            cal.Calibrator("linear").predict([1, 2, 3])
        with self.assertRaises(ValueError):
            cal.Calibrator("quadratic").fit([1, 2], [1, 2])   # too few points


class TestPipelineOnSampleData(unittest.TestCase):
    """Uses the real simulated CSV; checks the headline claims of the report."""

    @classmethod
    def setUpClass(cls):
        records, rejected = cal.load_csv(os.path.join("data", "simulated_sensor_readings.csv"))
        cls.records, cls.rejected = records, rejected
        df = analysis.runs_to_dataframe(cal.group_into_runs(records))
        cls.train, cls.test, _ = analysis.split_trials(df)
        cls.fitted = analysis.fit_calibrators(cls.train)
        cls.results = analysis.evaluate_methods(cls.test, cls.fitted)

    def test_row_counts(self):
        self.assertEqual(len(self.records), 260)
        self.assertEqual(len(self.rejected), 5)

    def test_no_trial_is_in_both_train_and_test(self):
        self.assertFalse(set(self.train["trial"]) & set(self.test["trial"]))

    def _rmse(self, sensor, method):
        row = self.results[(self.results["sensor"] == sensor) & (self.results["method"] == method)]
        return float(row["rmse"].iloc[0])

    def test_every_correction_improves_on_no_correction(self):
        for sensor in ("A", "B"):
            for method in ("offset", "linear", "quadratic"):
                self.assertLess(self._rmse(sensor, method), self._rmse(sensor, "none"))

    def test_best_methods(self):
        best = analysis.best_method_per_sensor(self.results)
        self.assertEqual(best["B"], "quadratic")
        self.assertIn(best["A"], ("linear", "quadratic"))


if __name__ == "__main__":
    unittest.main()
