import numpy as np
import pandas as pd
from pathlib import Path

RANDOM_SEED = 42
rng = np.random.default_rng(RANDOM_SEED)

DATA_PATH = Path("data/raw")
DATA_PATH.mkdir(parents=True, exist_ok=True)


def generate_customers(n_customers: int) -> pd.DataFrame:
    customers = pd.DataFrame({
        "customer_id": np.arange(1, n_customers + 1),
        "age": rng.integers(21, 75, n_customers),
        "tenure_months": rng.integers(0, 120, n_customers),
        "income_band": rng.choice(["LOW", "MID", "HIGH"], n_customers, p=[0.35, 0.45, 0.20]),
        "region": rng.choice(["SOUTH", "MIDWEST", "NORTHEAST", "WEST"], n_customers),
    })

    income_map = customers["income_band"].map({"LOW": -0.7, "MID": 0.0, "HIGH": 0.8}).to_numpy()
    tenure_z = (customers["tenure_months"] - customers["tenure_months"].mean()) / customers["tenure_months"].std()

    risk_latent = -0.5 * income_map - 0.1 * tenure_z + rng.normal(0, 0.9, n_customers)
    risk_score = np.clip(650 + (-risk_latent * 70) + rng.normal(0, 35, n_customers), 300, 850)

    customers["risk_score"] = risk_score.round().astype(int)

    return customers


def generate_campaigns(n_campaigns: int) -> pd.DataFrame:
    campaigns = pd.DataFrame({
        "campaign_id": np.arange(1, n_campaigns + 1),
        "start_date": pd.date_range("2025-01-01", periods=n_campaigns, freq="7D"),
    })

    campaigns["end_date"] = campaigns["start_date"] + pd.Timedelta(days=6)
    campaigns["offer_type"] = rng.choice(
        ["APR_PROMO", "CLI", "CASHBACK", "BNPL_PROMO"],
        n_campaigns,
        p=[0.30, 0.20, 0.30, 0.20]
    )

    campaigns["channel"] = rng.choice(
        ["EMAIL", "APP", "SMS"],
        n_campaigns,
        p=[0.55, 0.30, 0.15]
    )

    campaigns["cost_per_contact"] = rng.uniform(0.02, 0.18, n_campaigns).round(3)

    return campaigns


def generate_exposures(customers: pd.DataFrame, campaigns: pd.DataFrame) -> pd.DataFrame:
    rows = []
    n_customers = len(customers)

    # latent propensity based on income + tenure
    income_map = customers["income_band"].map({"LOW": -0.7, "MID": 0.0, "HIGH": 0.8}).to_numpy()
    tenure_z = (customers["tenure_months"] - customers["tenure_months"].mean()) / customers["tenure_months"].std()
    propensity = 0.3 * income_map + 0.2 * tenure_z + rng.normal(0, 0.8, n_customers)

    for _, c in campaigns.iterrows():
        n = int(rng.integers(3000, 9000))
        cust_ids = rng.choice(customers["customer_id"], size=n, replace=False)
        treatment = rng.binomial(1, 0.5, size=n)

        cust_idx = cust_ids - 1
        base = 1 / (1 + np.exp(-(propensity[cust_idx] - 0.3)))

        offer_boost = {
            "APR_PROMO": 0.08,
            "CLI": 0.04,
            "CASHBACK": 0.06,
            "BNPL_PROMO": 0.05
        }[c["offer_type"]]

        channel_boost = {"EMAIL": 0.02, "APP": 0.03, "SMS": 0.01}[c["channel"]]
        lift = 0.02

        p_open = np.clip(base + offer_boost + channel_boost + treatment * lift, 0, 0.85)

        opened = rng.binomial(1, p_open)
        converted = rng.binomial(1, np.clip(0.20 * opened, 0, 1))
        p_opt_out = 0.01 + 0.01 * (c["channel"] == "SMS")  # 1% baseline, 2% for SMS
        opt_out = rng.binomial(1, p_opt_out, size=n)
        send_dates = c["start_date"] + pd.to_timedelta(rng.integers(0, 7, size=n), unit="D")

        rows.append(pd.DataFrame({
            "campaign_id": c["campaign_id"],
            "customer_id": cust_ids,
            "send_date": send_dates,
            "treatment": treatment,
            "opened": opened,
            "converted": converted,
            "opt_out": opt_out
        }))
    print("Opt-out sample:", opt_out[:20])
    print("Opt-out rate for this campaign:", opt_out.mean())
    return pd.concat(rows, ignore_index=True)

def generate_accounts(customers: pd.DataFrame) -> pd.DataFrame:
    n = len(customers)

    # Create 1 account per customer (v1)
    account_id = np.arange(1, n + 1)

    # Risk-based APR: higher risk_score => lower APR
    # Map risk_score (300-850) to APR ~ [0.16, 0.34] with noise
    risk_norm = (customers["risk_score"].to_numpy() - 300) / (850 - 300)  # 0..1
    apr = np.clip(0.34 - 0.18 * risk_norm + rng.normal(0, 0.015, n), 0.12, 0.40)

    # Credit limit driven by income + risk
    income_mult = customers["income_band"].map({"LOW": 0.7, "MID": 1.0, "HIGH": 1.5}).to_numpy()
    base_limit = 1500 + 6500 * risk_norm  # $1.5k to ~$8k baseline from risk
    credit_limit = np.clip(base_limit * income_mult + rng.normal(0, 500, n), 500, 25000)

    # Utilization correlates negatively with risk score (riskier customers tend to run higher util)
    util = np.clip(0.65 - 0.45 * risk_norm + rng.normal(0, 0.10, n), 0.0, 0.99)

    current_balance = credit_limit * util

    # Open date based on tenure
    open_date = pd.Timestamp("2025-01-01") - pd.to_timedelta(customers["tenure_months"] * 30, unit="D")

    status = rng.choice(["ACTIVE", "CLOSED"], size=n, p=[0.96, 0.04])

    accounts = pd.DataFrame({
        "account_id": account_id,
        "customer_id": customers["customer_id"].to_numpy(),
        "open_date": pd.to_datetime(open_date).dt.date,
        "credit_limit": credit_limit.round(2),
        "apr": apr.round(4),
        "utilization": util.round(4),
        "current_balance": current_balance.round(2),
        "status": status
    })

    return accounts


def generate_monthly_outcomes(customers: pd.DataFrame, accounts: pd.DataFrame, start="2025-01-01", months=12) -> pd.DataFrame:
    # Create 12 months of outcomes for each customer
    month_starts = pd.date_range(start=start, periods=months, freq="MS")

    n = len(customers)

    # Latent traits for value + risk
    income_map = customers["income_band"].map({"LOW": -0.7, "MID": 0.0, "HIGH": 0.8}).to_numpy()
    tenure_z = (customers["tenure_months"] - customers["tenure_months"].mean()) / customers["tenure_months"].std()
    risk_norm = (customers["risk_score"].to_numpy() - 300) / (850 - 300)

    # value latent: income + tenure + some noise
    value_latent = 0.7 * income_map + 0.2 * tenure_z + rng.normal(0, 0.9, n)

    # base monthly spend level tied to value_latent + credit_limit
    credit_limit = accounts["credit_limit"].to_numpy()
    base_spend = np.clip(250 + 220 * (value_latent + 1.2) + 0.10 * credit_limit, 50, 5000)

    # risk latent: inverse of risk_norm plus noise
    risk_latent = (1 - risk_norm) + rng.normal(0, 0.25, n)

    rows = []
    for m in month_starts:
        # mild seasonality: holiday spike Nov/Dec
        season = 1.0
        if m.month in (11, 12):
            season = 1.18
        elif m.month in (1, 2):
            season = 0.95

        spend = np.clip(base_spend * season + rng.normal(0, 120, n), 0, None)

        # revolve balance depends on spend, utilization, and payment behavior
        util = accounts["utilization"].to_numpy()
        # payment_rate: higher risk => lower payment
        payment_rate = np.clip(0.55 + 0.25 * risk_norm - 0.15 * risk_latent + rng.normal(0, 0.08, n), 0.05, 1.0)

        # approximate revolve balance: start from current balance proxy + portion of spend, then subtract payment
        # (v1 simplification, enough for modeling)
        raw_balance = (accounts["current_balance"].to_numpy() * 0.70) + (spend * (0.35 + 0.25 * util))
        revolve_balance = np.clip(raw_balance * (1 - payment_rate), 0, credit_limit)

        # delinquency probability increases with risk_latent and high utilization
        p_dq = np.clip(0.01 + 0.06 * risk_latent + 0.05 * util, 0, 0.35)
        delinquency_flag = rng.binomial(1, p_dq, size=n)

        # chargeoff proxy: rare, mostly when delinquent + high risk
        p_co = np.clip(0.001 + 0.02 * delinquency_flag + 0.02 * (risk_latent > 1.2), 0, 0.08)
        chargeoff_proxy = rng.binomial(1, p_co, size=n)

        rows.append(pd.DataFrame({
            "customer_id": customers["customer_id"].to_numpy(),
            "month": m.date(),
            "spend": spend.round(2),
            "revolve_balance": revolve_balance.round(2),
            "payment_rate": payment_rate.round(4),
            "delinquency_flag": delinquency_flag.astype(int),
            "chargeoff_proxy": chargeoff_proxy.astype(int)
        }))

    return pd.concat(rows, ignore_index=True)

def main():
    customers = generate_customers(25000)
    campaigns = generate_campaigns(40)
    exposures = generate_exposures(customers, campaigns)

    customers.to_csv(DATA_PATH / "customers.csv", index=False)
    campaigns.to_csv(DATA_PATH / "campaigns.csv", index=False)
    exposures.to_csv(DATA_PATH / "campaign_exposures.csv", index=False)

    accounts = generate_accounts(customers)
    monthly = generate_monthly_outcomes(customers, accounts, start="2025-01-01", months=12)

    accounts.to_csv(DATA_PATH / "accounts.csv", index=False)
    monthly.to_csv(DATA_PATH / "monthly_outcomes.csv", index=False)

    print("Data generation complete.")


if __name__ == "__main__":
    main()
