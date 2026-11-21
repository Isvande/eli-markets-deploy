def odds_points(start, end, trades, current_price):
    """SVG polyline points for the yes price over time, as a step line in a 600 by 200 box.

    trades are (traded_at, price_before, price_after) in time order.
    """
    span = (end - start).total_seconds() or 1

    def point(when, price):
        share = min(max((when - start).total_seconds() / span, 0), 1)
        return f"{share * 600:.1f},{(1 - float(price)) * 200:.1f}"

    price = float(trades[0][1]) if trades else current_price
    points = [point(start, price)]
    for when, _before, after in trades:
        points.append(point(when, price))
        price = float(after)
        points.append(point(when, price))
    points.append(point(end, price))
    return " ".join(points)
