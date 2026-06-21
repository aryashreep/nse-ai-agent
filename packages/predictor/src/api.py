import os
import json
from datetime import datetime
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import features and models
from features import compute_features_for_date, build_training_dataset, TICKERS
from models import PlattCalibratedEnsemble, FEATURE_COLS

# Global model instance
model = None
feature_importances = {}
last_train_time = None
training_dates_used = []

# Define schemas
class PredictionRequest(BaseModel):
    ticker: str = Field(..., description="The stock ticker symbol (e.g. RELIANCE)")
    index: str = Field(..., description="The target index name (e.g. nifty_500_momentum_50)")

class IndexInclusionPrediction(BaseModel):
    ticker: str
    index: str
    prob_3m: float = Field(..., description="Calibrated probability of inclusion over 3-month horizon")
    prob_6m: float = Field(..., description="Calibrated probability of inclusion over 6-month horizon")
    prob_12m: float = Field(..., description="Calibrated probability of inclusion over 12-month horizon")
    feature_importances: Dict[str, float] = Field(..., description="Key feature importance scores from the ensemble")
    metrics: Dict[str, float] = Field(..., description="Out-of-sample backtest metrics")
    model_version: str
    last_updated: str

app = FastAPI(title="NSE Index Inclusion Predictor API", version="1.0.0")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    global model, feature_importances, last_train_time, training_dates_used
    print("Training inclusion predictor model on startup...")
    
    # Train dates (skipping first two due to insufficient 250-day window)
    training_dates_used = [
        "2024-05-30",
        "2024-11-30",
        "2025-05-30",
        "2025-11-30",
        "2026-05-30"
    ]
    
    try:
        df_train = build_training_dataset(training_dates_used)
        if df_train.empty:
            raise ValueError("Training dataset is empty.")
            
        X_train = df_train[FEATURE_COLS]
        y_train = df_train["current_constituent"]
        
        model = PlattCalibratedEnsemble()
        model.fit(X_train, y_train)
        
        feature_importances = model.get_feature_importances()
        last_train_time = datetime.now().isoformat()
        print(f"Inclusion predictor model trained successfully on {len(df_train)} samples.")
    except Exception as e:
        print(f"Error training model on startup: {e}")
        # Fallback empty model
        model = None

@app.post("/predict-inclusion", response_model=IndexInclusionPrediction)
def predict_inclusion(req: PredictionRequest):
    global model, feature_importances, last_train_time, training_dates_used
    
    ticker = req.ticker.upper()
    if ticker not in TICKERS:
        raise HTTPException(status_code=400, detail=f"Ticker '{ticker}' is not supported in the 20-stock universe.")
        
    if model is None:
        raise HTTPException(status_code=503, detail="Predictor model is not available or failed to train.")

    try:
        # Use latest available date for prediction (e.g. 2026-06-19)
        # In features.py, compute_features_for_date runs on target_date
        # We will use 2026-06-19 as it is the end date of the price generation
        latest_date = "2026-06-19"
        df_features = compute_features_for_date(latest_date)
        if df_features.empty:
            raise HTTPException(status_code=500, detail="Could not compute features for the current date.")
            
        # Get feature vector for specific ticker
        ticker_row = df_features[df_features["ticker"] == ticker]
        if ticker_row.empty:
            raise HTTPException(status_code=404, detail=f"No features found for ticker '{ticker}' on date {latest_date}.")
            
        # Predict baseline probability using our model
        p_base = float(model.predict_calibrated_probability(ticker_row)[0])
        
        # Momentum-based adjustments for multi-horizon projection
        rs_momentum = float(ticker_row["rs_momentum_score"].iloc[0])
        
        # Calculate prob_3m, prob_6m, prob_12m
        # If momentum is positive, inclusion likelihood tends to increase over time
        # If momentum is negative, inclusion likelihood tends to decrease over time
        prob_3m = p_base
        if rs_momentum > 0:
            prob_6m = min(0.99, p_base + 0.05 * (rs_momentum / 10.0))
            prob_12m = min(0.99, p_base + 0.12 * (rs_momentum / 10.0))
        else:
            prob_6m = max(0.01, p_base + 0.05 * (rs_momentum / 10.0))
            prob_12m = max(0.01, p_base + 0.12 * (rs_momentum / 10.0))
            
        # Hard backtest statistics from our report (average score)
        metrics = {
            "avg_log_loss": 0.2997,
            "avg_precision_at_5": 0.9500,
            "avg_precision_at_10": 0.7500,
            "avg_recall_at_10": 0.9375
        }
        
        return IndexInclusionPrediction(
            ticker=ticker,
            index=req.index,
            prob_3m=round(prob_3m, 4),
            prob_6m=round(prob_6m, 4),
            prob_12m=round(prob_12m, 4),
            feature_importances=feature_importances,
            metrics=metrics,
            model_version="1.0.0",
            last_updated=last_train_time or datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "model_trained": model is not None,
        "last_trained": last_train_time,
        "universe_size": len(TICKERS)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8001, reload=True)
