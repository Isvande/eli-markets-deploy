import math


def _validate(q_yes, q_no, b):
    if not all(math.isfinite(x) for x in (q_yes, q_no, b)):
        raise ValueError("quantities and liquidity must be finite")
    if q_yes < 0 or q_no < 0 or b <= 0:
        raise ValueError("quantities must be nonnegative and liquidity positive")


def price_yes(q_yes, q_no, b=100):
    _validate(q_yes, q_no, b)
    difference = (q_yes - q_no) / b
    if difference >= 0:
        return 1 / (1 + math.exp(-difference))
    exp_difference = math.exp(difference)
    return exp_difference / (1 + exp_difference)


def cost(q_yes, q_no, b=100):
    _validate(q_yes, q_no, b)
    return max(q_yes, q_no) + b * math.log1p(math.exp(-abs(q_yes - q_no) / b))


def trade_cost(q_yes, q_no, side, shares, b=100):
    _validate(q_yes, q_no, b)
    if side not in ("yes", "no"):
        raise ValueError("side must be 'yes' or 'no'")
    if isinstance(shares, bool) or not isinstance(shares, int) or shares <= 0:
        raise ValueError("shares must be a positive integer")
    p = price_yes(q_yes, q_no, b) if side == "yes" else price_yes(q_no, q_yes, b)
    x = shares / b
    if x < 50:
        return b * math.log1p(p * math.expm1(x))
    if p == 0:
        diff = (q_no - q_yes) / b if side == "yes" else (q_yes - q_no) / b
        log_p = -max(diff, 0) - math.log1p(math.exp(-abs(diff)))
    else:
        log_p = math.log(p)
    a = log_p + x
    log_other = math.log1p(-p) if p < 1 else -math.inf
    high = max(a, log_other)
    return b * (high + math.log1p(math.exp(min(a, log_other) - high)))


def trade_cost_cents(q_yes, q_no, side, shares, b=100):
    return math.ceil(trade_cost(q_yes, q_no, side, shares, b) * 100)


def payout_cents(shares_yes, shares_no, outcome):
    if outcome not in ("yes", "no"):
        raise ValueError("outcome must be 'yes' or 'no'")
    if shares_yes < 0 or shares_no < 0:
        raise ValueError("shares must be nonnegative")
    return (shares_yes if outcome == "yes" else shares_no) * 100


def brier(probability, outcome):
    if not 0 <= probability <= 1:
        raise ValueError("probability must be between 0 and 1")
    if outcome not in ("yes", "no"):
        raise ValueError("outcome must be 'yes' or 'no'")
    return (probability - (1 if outcome == "yes" else 0)) ** 2


def mean_brier(forecasts):
    if not forecasts:
        return None
    return sum(brier(probability, outcome) for probability, outcome in forecasts) / len(forecasts)
