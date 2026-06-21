# Walk-Forward Validation Backtest Report

This report evaluates the predictive performance of the Platt Calibrated Ensemble model (Random Forest & Gradient Boosting) for predicting Nifty Momentum Index reconstitution.

## Performance Summary

| Metric | Average Score | Description |
| :--- | :--- | :--- |
| **Log-Loss** | 0.2997 | Calibrated probability error (lower is better) |
| **Precision @ 5** | 95.00% | Fraction of top 5 predictions that are included |
| **Precision @ 10** | 75.00% | Fraction of top 10 predictions that are included |
| **Recall @ 10** | 93.75% | Fraction of actual index constituents captured in top 10 predictions |

## Feature Importances

The relative contribution of each technical and fundamental factor used in the prediction ensemble:

| Factor | Importance | Description |
| `was_added_prev` | 45.19% | Feature importance score |
| `debt_to_equity` | 9.14% | Feature importance score |
| `volume_ratio_3m` | 8.68% | Feature importance score |
| `rs_3m` | 7.48% | Feature importance score |
| `rs_12m` | 5.99% | Feature importance score |
| `roce` | 5.06% | Feature importance score |
| `rs_momentum_score` | 4.99% | Feature importance score |
| `market_cap_rank` | 4.74% | Feature importance score |
| `roe` | 4.24% | Feature importance score |
| `ema_200_distance_pct` | 2.55% | Feature importance score |
| `rs_6m` | 1.94% | Feature importance score |

## Fold-by-Fold Analysis

### Evaluation Date: 2024-11-30

- **Training Period:** 2023-05-30, 2023-11-30, 2024-05-30
- **Log-Loss:** 0.5349
- **Precision @ 5:** 80.00%
- **Precision @ 10:** 60.00%
- **Recall @ 10:** 75.00%
- **Actual Constituents Count:** 8

#### Top 10 Predictions:

| Rank | Ticker | Predicted Likelihood | Actual Constituent | Momentum Score | Market Cap Rank |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **RELIANCE** | 65.01% | Yes | 18.37 | 1 |
| 2 | **HDFCBANK** | 62.40% | No | -5.67 | 2 |
| 3 | **BRITANNIA** | 61.33% | Yes | 14.27 | 18 |
| 4 | **TATAMOTORS** | 61.33% | Yes | 13.02 | 4 |
| 5 | **ICICIBANK** | 61.33% | Yes | -7.23 | 6 |
| 6 | **ONGC** | 60.26% | Yes | -24.66 | 11 |
| 7 | **ITC** | 59.17% | No | 19.92 | 5 |
| 8 | **M&M** | 56.97% | Yes | 1.84 | 13 |
| 9 | **TCS** | 43.21% | No | 14.59 | 3 |
| 10 | **WIPRO** | 34.31% | No | 14.07 | 16 |

### Evaluation Date: 2025-05-30

- **Training Period:** 2023-05-30, 2023-11-30, 2024-05-30, 2024-11-30
- **Log-Loss:** 0.3255
- **Precision @ 5:** 100.00%
- **Precision @ 10:** 80.00%
- **Recall @ 10:** 100.00%
- **Actual Constituents Count:** 8

#### Top 10 Predictions:

| Rank | Ticker | Predicted Likelihood | Actual Constituent | Momentum Score | Market Cap Rank |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **TATAMOTORS** | 77.76% | Yes | 35.14 | 3 |
| 2 | **RELIANCE** | 76.03% | Yes | 25.79 | 2 |
| 3 | **ICICIBANK** | 75.94% | Yes | 0.69 | 4 |
| 4 | **HINDUNILVR** | 74.01% | Yes | -11.11 | 7 |
| 5 | **BRITANNIA** | 73.13% | Yes | 6.83 | 17 |
| 6 | **ONGC** | 71.87% | Yes | -23.49 | 11 |
| 7 | **M&M** | 70.78% | Yes | -6.11 | 12 |
| 8 | **NTPC** | 69.22% | Yes | -6.40 | 16 |
| 9 | **MARUTI** | 55.72% | No | 20.48 | 14 |
| 10 | **ITC** | 52.87% | No | 9.84 | 5 |

### Evaluation Date: 2025-11-30

- **Training Period:** 2023-05-30, 2023-11-30, 2024-05-30, 2024-11-30, 2025-05-30
- **Log-Loss:** 0.2001
- **Precision @ 5:** 100.00%
- **Precision @ 10:** 80.00%
- **Recall @ 10:** 100.00%
- **Actual Constituents Count:** 8

#### Top 10 Predictions:

| Rank | Ticker | Predicted Likelihood | Actual Constituent | Momentum Score | Market Cap Rank |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **RELIANCE** | 84.32% | Yes | 35.67 | 1 |
| 2 | **BRITANNIA** | 81.48% | Yes | 22.22 | 16 |
| 3 | **ICICIBANK** | 79.50% | Yes | 21.14 | 3 |
| 4 | **TATAMOTORS** | 79.45% | Yes | -3.16 | 4 |
| 5 | **NTPC** | 79.13% | Yes | -0.66 | 15 |
| 6 | **ONGC** | 78.35% | Yes | 8.28 | 12 |
| 7 | **HINDUNILVR** | 76.86% | Yes | -20.25 | 6 |
| 8 | **M&M** | 76.77% | Yes | 10.28 | 11 |
| 9 | **INFY** | 33.17% | No | 24.87 | 8 |
| 10 | **WIPRO** | 19.43% | No | -3.18 | 18 |

### Evaluation Date: 2026-05-30

- **Training Period:** 2023-05-30, 2023-11-30, 2024-05-30, 2024-11-30, 2025-05-30, 2025-11-30
- **Log-Loss:** 0.1384
- **Precision @ 5:** 100.00%
- **Precision @ 10:** 80.00%
- **Recall @ 10:** 100.00%
- **Actual Constituents Count:** 8

#### Top 10 Predictions:

| Rank | Ticker | Predicted Likelihood | Actual Constituent | Momentum Score | Market Cap Rank |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **RELIANCE** | 86.52% | Yes | 20.28 | 1 |
| 2 | **ONGC** | 86.04% | Yes | 31.32 | 12 |
| 3 | **HINDUNILVR** | 85.96% | Yes | -14.27 | 8 |
| 4 | **NTPC** | 85.10% | Yes | 11.74 | 13 |
| 5 | **BRITANNIA** | 84.38% | Yes | -2.83 | 16 |
| 6 | **ICICIBANK** | 84.17% | Yes | 13.41 | 3 |
| 7 | **TATAMOTORS** | 83.71% | Yes | -18.88 | 4 |
| 8 | **M&M** | 82.40% | Yes | 52.54 | 9 |
| 9 | **TCS** | 14.42% | No | 5.47 | 6 |
| 10 | **INFY** | 14.17% | No | 6.41 | 7 |
