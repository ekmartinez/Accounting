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

def asset_amortization(start_date, periods, cost, timming): 
    """ Returns an amortization table for mont-end closings
            Args
            start_date: YYYY-MM-DD
            periods: Usefull life of the asset in months
            cost: Cost of the asset
            timming: "MS" for month start, "ME" for month end 
    """ 

    date_range = pd.date_range(start_date, periods=periods, freq=timming)
    expense = cost / periods
    amortized_balance = [cost]
    amortization = [0]

    for period in range(periods):
        amortization.append(cost / periods)
        amortized_balance.append(cost - expense)
        cost -= expense

    data = {
        "Date": date_range,
        "Amortization": amortization,
        "Amortized Balance": amortized_balance
    }

    df = pd.DataFrame(data)

    return df
