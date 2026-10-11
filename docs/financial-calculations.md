# Financial calculations

## Authority

The only authoritative FD amount calculation is `backend/app/calculators/fd.py`, reached through `domain/rates.py`. Neither the frontend nor a language model computes maturity. Tests for the formula live in `backend/tests/test_fd_calculator.py`.

## Current formula

For principal `P`, annual rate `r` as a percentage, compounding periods per year `n`, and duration `t` in years:

```text
maturity = P × (1 + (r / 100) / n) ^ (n × t)
interest = maturity − P
t = tenure_months / 12
```

The implementation uses `Decimal` with a local precision of 40 and rounds maturity and interest to two decimal places using `ROUND_HALF_UP`. Response version is `fd-v1`, currency is INR, and a warning says bank-specific day-count and rounding may differ.

## Preconditions

The product calculation requires a positive principal, tenure from 1 to 1200 months, exactly one eligible amount/tenure rate band, `HIGH` verification status, a current conflict-free source, cumulative payout, and a specified positive compounding frequency. Otherwise the calculation returns no amount and a status/reason. It will not extrapolate between slabs, resolve ambiguous overlapping bands, or estimate early-withdrawal maturity.

## Limits

The generic compound-interest implementation is not a bank-specific FD engine. Actual banks may use different day counts, broken-period rules, payout schedules and rounding. Product data must not specify a compounding frequency unless its source supports that convention. Until a bank-specific documented calculator exists, present results as estimates and preserve the warning.

Comparison gains/give-ups are computed from these deterministic maturity amounts and verified conditions; see [comparison and verification](verification-system.md). The frontend displays them but does not recompute them.
