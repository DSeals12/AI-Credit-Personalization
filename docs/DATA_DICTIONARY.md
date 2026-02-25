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

## accounts

**Grain:** 1 row per customer account (v1: 1 account per customer)

| Column Name     | Data Type | Description |
|----------------|----------|-------------|
| account_id     | int      | Unique account identifier |
| customer_id    | int      | Customer foreign key |
| open_date      | date     | Account open date |
| credit_limit   | float    | Simulated credit limit |
| apr            | float    | Simulated APR (risk-based) |
| utilization    | float    | Current utilization ratio (0–1) |
| current_balance| float    | Current balance in dollars |
| status         | category | ACTIVE / CLOSED |

## monthly_outcomes

**Grain:** 1 row per customer per month

| Column Name        | Data Type | Description |
|-------------------|----------|-------------|
| customer_id        | int      | Customer foreign key |
| month              | date     | Month start date |
| spend              | float    | Monthly spend ($) |
| revolve_balance    | float    | Revolving balance at month end ($) |
| payment_rate       | float    | Payment as % of balance (0–1) |
| delinquency_flag   | binary   | 1 if delinquent this month |
| chargeoff_proxy    | binary   | 1 if chargeoff-like event occurred |