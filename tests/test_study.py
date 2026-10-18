import unittest

from portfolio_construction_study.study import ASSETS, analyze, generate_returns


class PortfolioStudyTests(unittest.TestCase):
    def test_reproducible_and_weights_are_valid(self):
        self.assertEqual(generate_returns(5, 80), generate_returns(5, 80))
        _, metrics = analyze(generate_returns(5, 80), lookback=30)
        weights = metrics["weights"]["inverse_vol"]
        self.assertAlmostEqual(sum(weights.values()), 1.0)
        self.assertLessEqual(max(weights.values()), 0.60 + 1e-12)
        self.assertEqual(set(weights), set(ASSETS))
        self.assertIn("historical_cvar_95_daily", metrics["strategies"]["inverse_vol"])
        self.assertIn("maximum_drawdown", metrics["strategies"]["equal_weight"])

    def test_outputs_only_after_estimation_window(self):
        rows, _ = analyze(generate_returns(count=50), lookback=30)
        self.assertEqual(len(rows), 20)
        self.assertEqual(set(rows[0]), {"date", "equal_weight", "inverse_vol"})

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            analyze(generate_returns(count=40), lookback=40)
        with self.assertRaises(ValueError):
            analyze(generate_returns(count=50), lookback=20, max_weight=0.1)


if __name__ == "__main__":
    unittest.main()
