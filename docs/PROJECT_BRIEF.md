A. Business problem
    Marketing spend rising; need better targeting/personalization
    Must respect credit risk + compliance + frequency rules

B. Decisions the system will support
    For each customer weekly:
    Should we contact them? (Y/N)
    Which channel? (email/app/sms)
    Which offer? (APR promo / credit line increase / cash-back / BNPL promo)
    Expected outcome: response, spend lift, risk-adjusted value

C. Success metrics 
    Incremental profit per 1,000 contacts (or per $ spend)
    Lift vs control (response rate, conversion, spend)
    Risk-adjusted return (value minus expected losses proxy)
Secondary:
    Unsubscribe/complaint rate proxy
    Contact policy violations (must be 0)

D. Constraints 
    Budget cap per campaign/week
    Contact frequency cap (e.g., <= 2 touches / 30 days)
    Risk threshold (exclude high delinquency probability band)
    Offer eligibility rules (e.g., CLI only if utilization high + on-time)

E. Data outputs
    A scored table: customer_id, week, best_action, expected_value, constraints_triggered
    Experiment-ready segments (for A/B or holdout)