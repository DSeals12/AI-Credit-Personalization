import pandas as pd
from pathlib import Path

DATA_PATH = Path("data/raw")
OUT_PATH = Path("data/processed")
OUT_PATH.mkdir(parents=True, exist_ok=True)


def build_customer_month_features():
    customers = pd.read_csv(DATA_PATH / "customers.csv")
    accounts = pd.read_csv(DATA_PATH / "accounts.csv")
    monthly = pd.read_csv(DATA_PATH / "monthly_outcomes.csv")

    # Merge static + account data
    base = (
        customers
        .merge(accounts, on="customer_id", how="left")
        .merge(monthly, on="customer_id", how="left")
    )

    # Convert month to datetime
    base["month"] = pd.to_datetime(base["month"])

    # Rolling spend features (lagged so no leakage)
    base = base.sort_values(["customer_id", "month"])

    base["spend_lag_1"] = base.groupby("customer_id")["spend"].shift(1)
    base["spend_lag_3_avg"] = (
        base.groupby("customer_id")["spend"]
        .rolling(3)
        .mean()
        .reset_index(level=0, drop=True)
        .shift(1)
    )

    # Rolling delinquency
    base["dq_lag_1"] = base.groupby("customer_id")["delinquency_flag"].shift(1)
    base["dq_rolling_3"] = (
        base.groupby("customer_id")["delinquency_flag"]
        .rolling(3)
        .mean()
        .reset_index(level=0, drop=True)
        .shift(1)
    )

    # Utilization stability
    base["high_util_flag"] = (base["utilization"] > 0.80).astype(int)

    # Value proxy (future 3-month spend, shifted backward)
    base["future_3mo_spend"] = (
        base.groupby("customer_id")["spend"]
        .rolling(3)
        .sum()
        .reset_index(level=0, drop=True)
        .shift(-3)
    )

    # Risk proxy
    base["future_chargeoff_flag"] = (
        base.groupby("customer_id")["chargeoff_proxy"]
        .shift(-1)
    )

    # Drop rows with missing lags (first months)
    base = base.dropna(subset=["spend_lag_1", "future_3mo_spend"])

    base.to_csv(OUT_PATH / "customer_month_features.csv", index=False)

    print("Feature table built successfully.")


if __name__ == "__main__":
    build_customer_month_features()