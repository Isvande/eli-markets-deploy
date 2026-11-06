# Test the pricing calculations
import math
import pytest
 
from app.compute import cost, price_yes, trade_cost, trade_cost_cents
 
 
@pytest.mark.parametrize("shares", [0, 250])
def test_equal_shares_mean_fifty_percent(shares):
    assert price_yes(shares, shares) == pytest.approx(0.5)
 
 
@pytest.mark.parametrize("q_yes, q_no", [(10, 0), (0, 37), (500, 120)])
def test_yes_and_no_prices_add_up_to_one(q_yes, q_no):
    assert price_yes(q_yes, q_no) + price_yes(q_no, q_yes) == pytest.approx(1.0)
 
 
def test_more_yes_shares_means_higher_yes_price():
    assert price_yes(100, 0) > price_yes(50, 0) > price_yes(0, 0)
 
 
def test_known_price_value():
    assert price_yes(100, 0) == pytest.approx(math.e / (1 + math.e))
 
 
def test_lopsided_market_price_goes_to_zero_or_one_without_crashing():
    assert price_yes(1_000_000, 0) == pytest.approx(1.0)
    assert price_yes(0, 1_000_000) == pytest.approx(0.0)
 
 
def test_smaller_b_moves_the_price_more():
    assert price_yes(50, 0, b=10) > price_yes(50, 0, b=100)
 
 
@pytest.mark.parametrize("q_yes, q_no, side, shares", [(0, 0, "yes", 10), (40, 15, "no", 25), (300, 50, "yes", 1)])
def test_trade_cost_matches_cost_function_difference(q_yes, q_no, side, shares):
    after_yes = q_yes + (shares if side == "yes" else 0)
    after_no = q_no + (shares if side == "no" else 0)
    expected = cost(after_yes, after_no) - cost(q_yes, q_no)
    assert trade_cost(q_yes, q_no, side, shares) == pytest.approx(expected)
 
 
def test_known_trade_cost_value():
    assert trade_cost(0, 0, "yes", 100) == pytest.approx(100 * math.log((math.e + 1) / 2))
 
 
def test_yes_and_no_are_symmetric():
    assert trade_cost(80, 20, "yes", 10) == pytest.approx(trade_cost(20, 80, "no", 10))
 
 
def test_cost_is_between_price_before_and_price_after():
    shares = 50
    total = trade_cost(20, 10, "yes", shares)
    assert shares * price_yes(20, 10) < total < shares * price_yes(20 + shares, 10)
 
 
def test_splitting_a_trade_costs_the_same_as_one_big_trade():
    one_trade = trade_cost(0, 0, "yes", 100)
    two_trades = trade_cost(0, 0, "yes", 60) + trade_cost(60, 0, "yes", 40)
    assert two_trades == pytest.approx(one_trade)
 
 
def test_buying_the_cheap_side_costs_less():
    assert trade_cost(200, 0, "no", 10) < trade_cost(200, 0, "yes", 10)
 
 
def test_huge_trade_does_not_overflow():
    assert trade_cost(0, 0, "yes", 10_000_000) == pytest.approx(10_000_000 - 100 * math.log(2))
 
 
# ("yes", 3) costs 156.37 cents, so rounding to nearest would undercharge
@pytest.mark.parametrize("side, shares", [("yes", 3), ("no", 7), ("yes", 333)])
def test_cents_round_up_so_the_market_never_undercharges(side, shares):
    exact_cents = trade_cost(12, 5, side, shares) * 100
    charged = trade_cost_cents(12, 5, side, shares)
    assert isinstance(charged, int)
    assert exact_cents <= charged < exact_cents + 1
 
 
def test_one_share_in_new_market_costs_51_cents():
    assert trade_cost_cents(0, 0, "yes", 1) == 51
 
 
@pytest.mark.parametrize("side", ["maybe", "YES", "", None])
def test_rejects_invalid_side(side):
    with pytest.raises(ValueError):
        trade_cost(0, 0, side, 10)
 
 
@pytest.mark.parametrize("shares", [0, -5, 2.5, "10", True, None])
def test_rejects_invalid_share_counts(shares):
    with pytest.raises(ValueError):
        trade_cost(0, 0, "yes", shares)
 
 
@pytest.mark.parametrize("q_yes, q_no, b", [(-1, 0, 100), (0, -1, 100), (0, 0, 0), (0, 0, -100)])
def test_rejects_negative_quantities_and_bad_liquidity(q_yes, q_no, b):
    with pytest.raises(ValueError):
        price_yes(q_yes, q_no, b)
    with pytest.raises(ValueError):
        cost(q_yes, q_no, b)
 
 
@pytest.mark.parametrize("bad", [math.nan, math.inf])
def test_rejects_nan_and_infinity(bad):
    with pytest.raises(ValueError):
        price_yes(bad, 0)
    with pytest.raises(ValueError):
        trade_cost(0, 0, "yes", 10, b=bad)