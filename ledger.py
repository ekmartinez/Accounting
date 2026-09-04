class Ledger:
    """A simple helper to record and display journal entries for accounting problems."""

    def __init__(self):
        self.entries = []

    def add_entry(self, entry):
        """
        Add a journal entry to the ledger.
        Expects a dict like: {"date": ..., "account": ..., "debit": 0, "credit": 0}
        """
        required_keys = {"date", "account", "debit", "credit"}
        if not required_keys.issubset(entry):
            missing = required_keys - entry.keys()
            raise ValueError(f"Entry is missing required keys: {missing}")
        self.entries.append(entry)

    def print_ledger(self):
        """Print all journal entries in a readable, aligned format."""
        if not self.entries:
            print("No entries recorded yet.")
            return

        print(f"{'Date':<12}{'Account':<25}{'Debit':>10}{'Credit':>10}")
        print("-" * 57)
        for e in self.entries:
            debit = e["debit"] if e["debit"] else ""
            credit = e["credit"] if e["credit"] else ""
            print(f"{str(e['date']):<12}{e['account']:<25}{str(debit):>10}{str(credit):>10}")
