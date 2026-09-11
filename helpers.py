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
        Date the asset amortization begins. This is also the schedule's
        first row, showing the un-amortized starting balance.
    periods : int
        Useful life of the asset, in months.
    cost : float
        Original cost (or carrying value) of the asset being amortized.
    timing : str, default "MS"
        Pandas date offset alias for the schedule's cadence.
        "MS" = month start, "ME" = month end.

    Returns
    -------
    pandas.DataFrame
        Columns: Date, Amortization, Amortized Balance.
        Row 0 is the starting balance (Amortization = 0); each of the
        following `periods` rows applies one period's straight-line
        amortization.
    """
    # periods + 1 dates: one row for the starting balance, plus one row
    # per amortization period — matches the two lists below.
    date_range = pd.date_range(start=start_date, periods=periods + 1, freq=timing)

    period_expense = cost / periods

    # Row 0 has no amortization yet; every following row expenses one period's share.
    amortization = [0] + [period_expense] * periods

    # Computed directly from i (rather than repeatedly subtracting in a loop)
    # to avoid floating-point rounding drift building up over many periods.
    amortized_balance = [cost - period_expense * i for i in range(periods + 1)]

    df = pd.DataFrame({
        "Date": date_range,
        "Amortization": amortization,
        "Amortized Balance": amortized_balance,
    })

    return df
