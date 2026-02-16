# Data Dictionary

## customers

**Grain:** 1 row per customer

| Column Name     | Data Type | Description |
|----------------|----------|-------------|
| customer_id    | int      | Unique customer identifier |
| age            | int      | Customer age in years |
| tenure_months  | int      | Months since first account open |
| income_band    | category | LOW / MID / HIGH income bucket |
| risk_score     | int      | Simulated credit risk score (300–850) |
| region         | category | Geographic region of customer |

## campaigns

**Grain:** 1 row per customer

| Column Name        | Data Type | Description |
|--------------------|-----------|-------------|
| campaign_id        | int       | Campaign ID |
| offer_type         | category  | APR_PROMO / CLI / etc |
| channel            | category  | EMAIL / APP / SMS |
| cost_per_contact   | float     | Marketing cost per touch |

## campaign_exposures

**Grain:** 1 row per customer

| Column Name     | Data Type | Description |
|----------------|------------|-------------|
| campaign_id    | int        | Campaign identifier |
| customer_id    | int        | Customer |
| treatment      | int        | 1 = treatment, 0 = control |
| opened         | category   | Email/app opened |
| converted      | category   | Conversion flag |
| opt_out        | category   | Unsubscribe indicator |