import os
import json
import numpy as np
import pandas as pd
from typing import List, Dict, Any
from sklearn.metrics import log_loss

# Import features and models
from features import compute_features_for_date, build_training_dataset
from models import PlattCalibratedEnsemble, FEATURE_COLS

REBALANCE_DATES = [
    "2023-05-30",
    "2023-11-30",
    "2024-05-30",
    "2024-11-30",
    "2025-05-30",
    "2025-11-30",
    "2026-05-30"
]

def run_backtest():
    print("Starting walk-forward validation backtest...")
    
    # We will evaluate on the last 5 rebalance dates
    test_dates = REBALANCE_DATES[2:]
    
    results = []
    all_feature_importances = []
    
    for i, test_date in enumerate(test_dates):
        # Training dates are all dates before test_date
        train_dates = REBALANCE_DATES[:REBALANCE_DATES.index(test_date)]
        print(f"\nFold {i+1}: Testing on {test_date} | Training on {train_dates}")
        
        # Build training set
        df_train = build_training_dataset(train_dates)
        if df_train.empty:
            print(f"Skipping fold for {test_date} due to empty training data.")
            continue
            
        X_train = df_train[FEATURE_COLS]
        y_train = df_train["current_constituent"]
        
        # Build test set
        df_test = compute_features_for_date(test_date)
        if df_test.empty:
            print(f"Skipping fold for {test_date} due to empty test data.")
            continue
            
        X_test = df_test[FEATURE_COLS]
        y_test = df_test["current_constituent"]
        
        # Train model
        model = PlattCalibratedEnsemble()
        model.fit(X_train, y_train)
        
        # Predict
        probs = model.predict_calibrated_probability(X_test)
        df_eval = df_test.copy()
        df_eval["pred_prob"] = probs
        
        # Sort by predicted probability descending
        df_eval_sorted = df_eval.sort_values(by="pred_prob", ascending=False).reset_index(drop=True)
        
        # Calculate metrics
        loss = log_loss(y_test, probs)
        
        # Precision @ 5
        top_5 = df_eval_sorted.head(5)
        p_at_5 = top_5["current_constituent"].mean()
        
        # Precision @ 10
        top_10 = df_eval_sorted.head(10)
        p_at_10 = top_10["current_constituent"].mean()
        
        # Recall @ 10 (fraction of actual constituents in top 10)
        total_actual = y_test.sum()
        actual_in_top_10 = top_10["current_constituent"].sum()
        recall_at_10 = actual_in_top_10 / total_actual if total_actual > 0 else 0.0
        
        # Feature importances
        fi = model.get_feature_importances()
        all_feature_importances.append(fi)
        
        results.append({
            "test_date": test_date,
            "train_dates": train_dates,
            "log_loss": loss,
            "precision_at_5": p_at_5,
            "precision_at_10": p_at_10,
            "recall_at_10": recall_at_10,
            "total_actual": total_actual,
            "predictions": df_eval_sorted[["ticker", "current_constituent", "pred_prob", "market_cap_rank", "rs_momentum_score"]].to_dict(orient="records")
        })
        
        print(f"  Log-Loss: {loss:.4f}")
        print(f"  Precision@5: {p_at_5:.2%}")
        print(f"  Precision@10: {p_at_10:.2%}")
        print(f"  Recall@10: {recall_at_10:.2%}")

    # Calculate average metrics
    avg_loss = np.mean([r["log_loss"] for r in results])
    avg_p_at_5 = np.mean([r["precision_at_5"] for r in results])
    avg_p_at_10 = np.mean([r["precision_at_10"] for r in results])
    avg_recall = np.mean([r["recall_at_10"] for r in results])
    
    print("\n" + "="*40)
    print("BACKTEST SUMMARY")
    print(f"Average Log-Loss: {avg_loss:.4f}")
    print(f"Average Precision@5: {avg_p_at_5:.2%}")
    print(f"Average Precision@10: {avg_p_at_10:.2%}")
    print(f"Average Recall@10: {avg_recall:.2%}")
    print("="*40)
    
    # Calculate average feature importance
    avg_fi = {}
    for col in FEATURE_COLS:
        avg_fi[col] = np.mean([fi[col] for fi in all_feature_importances])
    sorted_fi = sorted(avg_fi.items(), key=lambda x: x[1], reverse=True)
    
    # Generate Markdown Report
    report_lines = [
        "# Walk-Forward Validation Backtest Report",
        "",
        "This report evaluates the predictive performance of the Platt Calibrated Ensemble model (Random Forest & Gradient Boosting) for predicting Nifty Momentum Index reconstitution.",
        "",
        "## Performance Summary",
        "",
        "| Metric | Average Score | Description |",
        "| :--- | :--- | :--- |",
        f"| **Log-Loss** | {avg_loss:.4f} | Calibrated probability error (lower is better) |",
        f"| **Precision @ 5** | {avg_p_at_5:.2%} | Fraction of top 5 predictions that are included |",
        f"| **Precision @ 10** | {avg_p_at_10:.2%} | Fraction of top 10 predictions that are included |",
        f"| **Recall @ 10** | {avg_recall:.2%} | Fraction of actual index constituents captured in top 10 predictions |",
        "",
        "## Feature Importances",
        "",
        "The relative contribution of each technical and fundamental factor used in the prediction ensemble:",
        "",
        "| Factor | Importance | Description |",
    ]
    
    for factor, val in sorted_fi:
        report_lines.append(f"| `{factor}` | {val:.2%} | Feature importance score |")
        
    report_lines.extend([
        "",
        "## Fold-by-Fold Analysis",
        ""
    ])
    
    for r in results:
        report_lines.extend([
            f"### Evaluation Date: {r['test_date']}",
            "",
            f"- **Training Period:** {', '.join(r['train_dates'])}",
            f"- **Log-Loss:** {r['log_loss']:.4f}",
            f"- **Precision @ 5:** {r['precision_at_5']:.2%}",
            f"- **Precision @ 10:** {r['precision_at_10']:.2%}",
            f"- **Recall @ 10:** {r['recall_at_10']:.2%}",
            f"- **Actual Constituents Count:** {r['total_actual']}",
            "",
            "#### Top 10 Predictions:",
            "",
            "| Rank | Ticker | Predicted Likelihood | Actual Constituent | Momentum Score | Market Cap Rank |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |"
        ])
        for idx, pred in enumerate(r["predictions"][:10]):
            actual_str = "Yes" if pred["current_constituent"] == 1 else "No"
            report_lines.append(
                f"| {idx+1} | **{pred['ticker']}** | {pred['pred_prob']:.2%} | {actual_str} | {pred['rs_momentum_score']:.2f} | {pred['market_cap_rank']} |"
            )
        report_lines.append("")
        
    report_content = "\n".join(report_lines)
    
    # Write to web application public directory
    os.makedirs("apps/web/public", exist_ok=True)
    report_path = "apps/web/public/backtest_report.md"
    with open(report_path, "w") as f:
        f.write(report_content)
        
    print(f"Successfully generated backtest report at: {report_path}")

if __name__ == "__main__":
    run_backtest()
