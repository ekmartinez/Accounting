# Accounting Helpers

Helper classes for solving Intermediate Accounting textbook problems in Jupyter
Notebooks. Built incrementally, problem by problem — this file is the running
reference for what exists so far. Update it whenever a method is added or changed.

## Files

- `ledger.py` — the `Ledger` and `TrialBalance` classes.
- `helpers.py` — a grab-bag file: notebook-level formatting functions for
  `Ledger`/`TrialBalance` (`format_ledger_table`, `format_trial_balance_table`),
  plus other standalone utilities not tied to either class
  (`months_elapsed`, `asset_amortization`).

## Setup (top of every notebook)

```python
from ledger import Ledger, TrialBalance
from helpers import format_ledger_table, format_trial_balance_table
import pandas as pd
from IPython.display import display, HTML
```

---

## `Ledger`

Records journal entries as a flat list of line dictionaries
(`date`, `account`, `debit`, `credit`, plus auto-added `txn_id` and
`description`). Validates that every entry balances before storing it.

```python
ledger = Ledger()

txn_id = ledger.add_entry(
    [
        {"date": "2024-05-01", "account": "Cash", "debit": 4000, "credit": 0},
        {"date": "2024-05-01", "account": "Common Stock", "debit": 0, "credit": 4000},
    ],
    description="Issued common stock for cash",
)
# Prints: Saved transaction id 1 — Issued common stock for cash
# Returns the auto-assigned transaction id (also usable later to reference this entry)
```

**Methods**

| Method | Purpose |
|---|---|
| `add_entry(lines, description=None)` | Post a journal entry (one or more lines). Rejects it if debits ≠ credits. Auto-assigns and prints a `txn_id`. |
| `delete_transaction(txn_id)` | Remove all lines belonging to one transaction — e.g., to fix a duplicate. |
| `print_transaction(txn_id=None)` | Print the full ledger (omit `txn_id`) or just one transaction, grouped, with the description shown once at the end of each entry's lines. |
| `to_table()` | Return the ledger as a plain pandas DataFrame (`txn_id, date, account, debit, credit, description`). |
| `reset()` | Clear all entries and restart the id counter at 1. Prefer creating a **new** `Ledger()` per exercise instead — reserve `reset()` for redoing the *same* exercise from scratch. |

**Naming convention:** give each exercise's ledger a distinct variable name
(e.g., `blue_ledger`, `wanda_ledger`) — never the bare name `ledger` once you
have more than one exercise active in the same notebook session. Reusing a
generic name across exercises is the single most common source of bugs
we've hit so far (silently applying one company's corrections to another's
trial balance).

---

## `TrialBalance`

Stores account balances (`debit`, `credit`, `type` per account). Two
different ways to correct a balance, because textbook errors come in two
different flavors:

- **Clerical errors** (footing/transposition mistakes, no real transaction
  behind them) → `adjust_account()` / `set_account()`.
- **Real posted transactions with the wrong amount/accounts** → post a
  correcting entry to a `Ledger`, then fold it in with `apply_ledger()`.

```python
tb = TrialBalance()
tb.add_account("Cash", debit=4800, account_type="asset")
tb.add_account("Accounts Payable", credit=4500, account_type="liability")
# ... one add_account() call per line in the given trial balance
```

**Methods**

| Method | Purpose |
|---|---|
| `add_account(account, debit=0, credit=0, account_type=None)` | Add a new account or overwrite an existing one with a starting balance. |
| `adjust_account(account, debit_change=0, credit_change=0)` | Incremental correction for a clerical error (e.g., a footing understated by $100). Account must already exist. |
| `set_account(account, debit=0, credit=0)` | Overwrite an account's balance directly — used when you're told the correct final balance outright (e.g., a transposition fix). Account must already exist. |
| `remove_account(account)` | Delete an account entirely. |
| `apply_ledger(ledger, account_types=None)` | Fold every line of a `Ledger` into this trial balance's totals. Any account not already present gets added automatically — pass `account_types={"New Account": "asset"}` to label it correctly when that happens. |
| `totals()` | Return `(total_debit, total_credit)` — raw, unnetted. |
| `is_balanced()` | `True` if total debits equal total credits. |
| `to_table(include_total=True, include_difference=False, net=True)` | Return the trial balance as a DataFrame. `net=True` (default) collapses each account to a single balance on its larger side — the standard "final" view. `net=False` shows raw, unnetted debit/credit columns — useful mid-problem while auditing footing errors, since those errors are defined in terms of a specific column, not a net balance. |
| `from_dataframe(df, account_col=..., debit_col=None, credit_col=None, amount_col=None, type_col=None)` | *(classmethod)* Build a `TrialBalance` from a spreadsheet/DataFrame. Accepts either one signed `amount_col`, or a separate `debit_col`/`credit_col` pair — not both. |
| `reset()` | Clear all accounts. Same caveat as `Ledger.reset()` — prefer a new `TrialBalance()` per exercise. |

**Typical workflow for a "correct the trial balance" problem:**

```python
# 1. Build the given (possibly incorrect) trial balance
tb = TrialBalance()
tb.add_account(...)
# ...

# 2. View it, confirm it's unbalanced
display(HTML(format_trial_balance_table(tb).to_html(index=False)))
tb.is_balanced()

# 3a. Clerical errors (footings, transpositions) — direct adjustments
tb.adjust_account("Some Account", debit_change=100)
tb.set_account("Some Account", credit=6690)

# 3b. Real transaction errors — post as a proper journal entry, then fold in
corrections = Ledger()
corrections.add_entry([...], description="...")
tb.apply_ledger(corrections, account_types={"New Account": "asset"})

# 4. Re-view, confirm balanced
display(HTML(format_trial_balance_table(tb).to_html(index=False)))
tb.is_balanced()
```

---

## `helpers.py`

### `format_ledger_table(ledger, currency=True)`
Wraps `ledger.to_table()`, adds a `TOTAL` row, formats numbers as currency
(`$1,234.56`) by default, and title-cases the column headers.
Pass `currency=False` to keep raw numbers for further calculation.

```python
display(HTML(format_ledger_table(some_ledger).to_html(index=False)))
```

### `format_trial_balance_table(tb, currency=True, include_difference=True, net=True)`
Same idea, wrapping `tb.to_table()`. Adds `TOTAL` and (by default) a
`DIFFERENCE` row, currency-formats, title-cases headers.

```python
display(HTML(format_trial_balance_table(tb).to_html(index=False)))
```

> Note: the *netting* logic itself lives in `TrialBalance.to_table()`, not
> in this formatter — so `tb.to_table(net=True)` alone (no `helpers.py`
> involved) already returns a clean, netted, numeric DataFrame suitable for
> pandas analysis.

### `months_elapsed(payment_date, entry_date)`
Returns the number of months between two `date` objects (inclusive of the
starting month) — used for proration in adjusting-entry problems (e.g.,
prepaid insurance expiring monthly).

### `asset_amortization(start_date, periods, cost, timing="MS")`
Returns a straight-line amortization schedule as a DataFrame
(`Date, Amortization, Amortized Balance`). Row 0 is `start_date` itself
(Amortization = 0, the acquisition date); each of the following `periods`
rows applies one period's `cost / periods` straight-line amortization,
computed directly per-row (not by repeated subtraction) to avoid rounding
drift.

`timing` controls how each period's row is *dated*, independent of
`start_date`:
- `"ME"` — that period's own month-end date (e.g. `2025-01-31`). **Use this
  for adjusted-trial-balance problems** — they're almost always phrased as
  "as of [month-end date]", so this makes the row you need directly
  searchable by that date.
- `"MS"` (default) — the *following* month's start date (e.g. `2025-02-01`
  for the period ending January). Kept as the default for backward
  compatibility with earlier notebooks, but for new month-end problems,
  pass `timing="ME"` explicitly.

```python
# Matches problems phrased as "adjusted trial balance at January 31" —
# the $2,400 balance row is dated exactly 2025-01-31.
df = asset_amortization("2024-08-01", 12, 4800, timing="ME")
```

> A `format_amortization_table(df, currency=True)` display wrapper (plain
> dates, currency-formatted amounts) has been discussed but not added to
> `helpers.py` yet — kept separate for now since it's a different kind of
> table (a schedule, not a ledger/trial balance).

---

## Known gotchas (things that have actually bitten us)

- **Variable name collisions.** Reusing a generic name like `tb` or `ledger`
  across different exercises in the same notebook session will silently
  apply corrections to the wrong object. Always prefix with the
  exercise/company name.
- **Stale imports after editing `.py` files.** Jupyter only reads a module's
  code the first time it's imported in a session. After editing `ledger.py`
  or `helpers.py`, **restart the kernel** (or use `%load_ext autoreload` /
  `%autoreload 2` at the top of the notebook) before re-running — otherwise
  you'll be running old code with no error to warn you.
- **Multiple copies of the same file on disk.** If edits don't seem to take
  effect even after a restart, check `import ledger; ledger.__file__` to
  confirm which physical file is actually being imported.

---

## Possible future enhancements (not yet built)

- A plain-text `print_table()` for `TrialBalance` (parallel to
  `Ledger.print_transaction()`), for quick console viewing without pandas/HTML.

## Out of scope (decided, not just deferred)

- **Financial statement preparation** (Income Statement, Balance Sheet,
  Statement of Owner's Equity). This would require closing entries
  (temporary vs. permanent accounts), current/long-term classification, and
  multi-period handling — a genuinely separate undertaking, not a small
  add-on. Decision: once a trial balance is corrected and balanced here,
  financial statements are prepared in a spreadsheet instead. Add a markdown
  note + spreadsheet link at the top of any notebook where this comes up.
