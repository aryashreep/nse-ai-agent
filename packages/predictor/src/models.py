import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

FEATURE_COLS = [
    "rs_12m", "rs_6m", "rs_3m", "rs_momentum_score",
    "volume_ratio_3m", "ema_200_distance_pct",
    "roce", "roe", "debt_to_equity", "market_cap_rank",
    "was_added_prev"
]

class PlattCalibratedEnsemble:
    def __init__(self):
        # Base models
        self.rf = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=5)
        self.gb = GradientBoostingClassifier(n_estimators=50, random_state=42, max_depth=3)
        # Calibrator (Platt scaling)
        self.calibrator = LogisticRegression(C=1.0)
        self.is_trained = False

    def fit(self, X: pd.DataFrame, y: pd.Series):
        """Fits the base ensemble models and the Platt scaling calibrator."""
        # Clean features
        X_clean = X[FEATURE_COLS]
        
        # Fit base models
        self.rf.fit(X_clean, y)
        self.gb.fit(X_clean, y)
        
        # Platt scaling: generate out-of-bag predictions for training data
        # To avoid overfitting, we use the average of the raw predict_proba from both classifiers
        probs_rf = self.rf.predict_proba(X_clean)[:, 1]
        probs_gb = self.gb.predict_proba(X_clean)[:, 1]
        probs_ensemble = (probs_rf + probs_gb) / 2.0
        
        # Fit calibrator on ensemble probabilities vs actual labels
        # Reshape to 2D array as required by sklearn
        X_calib = probs_ensemble.reshape(-1, 1)
        self.calibrator.fit(X_calib, y)
        
        self.is_trained = True

    def predict_calibrated_probability(self, X: pd.DataFrame) -> np.ndarray:
        """Returns calibrated probabilities (0-1) of index inclusion."""
        if not self.is_trained:
            raise ValueError("Model is not trained yet!")
            
        X_clean = X[FEATURE_COLS]
        
        # Predict base probabilities
        probs_rf = self.rf.predict_proba(X_clean)[:, 1]
        probs_gb = self.gb.predict_proba(X_clean)[:, 1]
        probs_ensemble = (probs_rf + probs_gb) / 2.0
        
        # Apply Platt calibration
        X_calib = probs_ensemble.reshape(-1, 1)
        calibrated_probs = self.calibrator.predict_proba(X_calib)[:, 1]
        return calibrated_probs

    def get_feature_importances(self) -> Dict[str, float]:
        """Returns the average feature importances across the base models."""
        if not self.is_trained:
            return {}
            
        fi_rf = self.rf.feature_importances_
        fi_gb = self.gb.feature_importances_
        fi_avg = (fi_rf + fi_gb) / 2.0
        
        return {col: float(val) for col, val in zip(FEATURE_COLS, fi_avg)}
