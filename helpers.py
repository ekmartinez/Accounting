import pandas as pd
from datetime import date

def months_elapsed(payment_date: date, entry_date: date) -> int:
    """Used to get the number of months elapsed"""
    return (entry_date.year - payment_date.year) * 12 + (entry_date.month - payment_date.month) + 1 

def format_ledger_table(ledger, currency=True):
    """
    Takes a Ledger, returns a formatted DataFrame with a TOTAL row,
    ready to display with display(HTML(...)).
    Set currency=False to keep raw numbers (e.g., for further calculations).
    """
    table = ledger.to_table()

    totals = pd.DataFrame([{
        "txn_id": "",
        "date": "",
        "account": "TOTAL",
        "debit": table["debit"].sum(),
        "credit": table["credit"].sum(),
        "description": "",
    }])
    table_with_total = pd.concat([table, totals], ignore_index=True)

    if currency:
        table_with_total["debit"] = table_with_total["debit"].apply(
            lambda x: f"{x:,.2f}" if x != "" and x != 0 else ""
        )
        table_with_total["credit"] = table_with_total["credit"].apply(
            lambda x: f"{x:,.2f}" if x != "" and x != 0 else ""
        )

    table_with_total.columns = [col.replace("_", " ").title() for col in table_with_total.columns]

    return table_with_total

def format_trial_balance_table(tb, currency=True, include_difference=True, net=True):
    table = tb.to_table(include_total=True, include_difference=include_difference, net=net)

    if currency:
        table["debit"] = table["debit"].apply(lambda x: f"{x:,.2f}" if x != "" and x != 0 else "")
        table["credit"] = table["credit"].apply(lambda x: f"{x:,.2f}" if x != "" and x != 0 else "")

    table.columns = [col.replace("_", " ").title() for col in table.columns]
    return table

def asset_amortization(start_date, periods, cost, timing="MS"):
    """
    Build a straight-line amortization schedule for month-end closings.

    Parameters
    ----------
    start_date : str (YYYY-MM-DD)
        Date the asset was acquired / coverage began. Also the schedule's
        first row, showing the un-amortized starting balance (no expense
        recognized yet).
    periods : int
        Useful life of the asset, in months.
    cost : float
        Original cost (or carrying value) of the asset being amortized.
    timing : str, default "MS"
        Pandas date offset alias for how each *subsequent* period's closing
        date is labeled.
        "MS" = each period's date is the following month's start.
        "ME" = each period's date is that period's own month-end — matches
               problems phrased as a month-end adjusted trial balance, e.g.
               "as of January 31".

    Returns
    -------
    pandas.DataFrame
        Columns: Date, Amortization, Amortized Balance.
        Row 0 = start_date, Amortization = 0.
        Rows 1..periods = one period's straight-line amortization each.
    """
    start_ts = pd.Timestamp(start_date)

    # Generate periods+1 candidate dates from start_date at the requested
    # frequency. If start_date already sits on that frequency's anchor
    # (e.g. a month-start date with timing="MS"), the first candidate IS
    # start_date, and these periods+1 dates are exactly what we want.
    # Otherwise (e.g. timing="ME", where a month-start start_date doesn't
    # sit on a month-end) the first candidate rolls forward past start_date
    # — so keep start_date as row 0 and take the next `periods` candidates.
    candidates = pd.date_range(start=start_date, periods=periods + 1, freq=timing)

    if candidates[0] == start_ts:
        date_range = candidates
    else:
        date_range = pd.DatetimeIndex([start_ts]).append(candidates[:periods])

    period_expense = cost / periods
    amortization = [0] + [period_expense] * periods
    amortized_balance = [cost - period_expense * i for i in range(periods + 1)]

    df = pd.DataFrame({
        "Date": date_range,
        "Amortization": amortization,
        "Amortized Balance": amortized_balance,
    })
    return df

def format_amortization_table(df, currency=True):
    """
    Takes the DataFrame returned by asset_amortization(), returns a display
    copy: plain dates (no time component) and currency-formatted amounts.
    Set currency=False to keep raw numbers.
    """
    display_df = df.copy()
    display_df["Date"] = display_df["Date"].dt.date

    if currency:
        display_df["Amortization"] = display_df["Amortization"].apply(lambda x: f"{x:,.2f}")
        display_df["Amortized Balance"] = display_df["Amortized Balance"].apply(lambda x: f"{x:,.2f}")

    return display_df
