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
        opt_out = rng.binomial(1, np.clip(0.003 + 0.003 * (c["channel"] == "SMS"), 0, 0.02))

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

    return pd.concat(rows, ignore_index=True)


def main():
    customers = generate_customers(25000)
    campaigns = generate_campaigns(40)
    exposures = generate_exposures(customers, campaigns)

    customers.to_csv(DATA_PATH / "customers.csv", index=False)
    campaigns.to_csv(DATA_PATH / "campaigns.csv", index=False)
    exposures.to_csv(DATA_PATH / "campaign_exposures.csv", index=False)

    print("Data generation complete.")


if __name__ == "__main__":
    main()
