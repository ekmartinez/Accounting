import numpy as np
import numpy_financial as npf
from typing import NamedTuple, Optional, Union

class Stack:
    """
    A simple last-in-first-out (LIFO) stack used internally by RPNEngine
    to hold operands and intermediate results during expression evaluation.
    """

    def __init__(self):
        self.stack = list()

    def push(self, func):
        """
        Pushes a value onto the top of the stack.

        Parameters:
            func: the value to push (typically a float, but may be a
                  list[float] for array operands like cash flow arrays).
        """
        self.stack.append(func)

    def pop(self):
        """
        Removes and returns the value at the top of the stack (the most
        recently pushed item).

        Raises:
            IndexError if the stack is empty.
        """
        return self.stack.pop()

    def peek(self):
        """
        Returns the value at the top of the stack (the most recently
        pushed item) WITHOUT removing it. Stack size is unchanged.

        Raises:
            IndexError if the stack is empty.
        """
        return self.stack[-1]

    def size_of(self):
        """Returns the number of items currently on the stack."""
        return len(self.stack)

class MathOps:
    """
    General-purpose mathematical operations available to the RPN engine.
    These methods are self-contained and can be used independently of
    RPNEngine/Stack.
    """

    def add(self, second_operand, first_operand):
        """
        Returns the sum of two numbers.
        add(second_operand, first_operand)
        first_operand = int, float — the value typed first
        second_operand = int, float — the value typed second
        """
        return first_operand + second_operand

    def subtract(self, second_operand, first_operand):
        """
        Returns the difference of two numbers.
        subtract(second_operand, first_operand)
        first_operand = int, float — the value typed first (minuend)
        second_operand = int, float — the value typed second (subtrahend)
        """
        return first_operand - second_operand

    def multiply(self, second_factor, first_factor):
        """
        Returns the product of two numbers.
        multiply(second_factor, first_factor)
        first_factor = int, float — the value typed first
        second_factor = int, float — the value typed second
        """
        return first_factor * second_factor

    def divide(self, divisor, dividend):
        """
        Returns the quotient of two numbers.
        divide(divisor, dividend)
        divisor = int, float — the value typed second (denominator)
        dividend = int, float — the value typed first (numerator)

        Raises ZeroDivisionError if divisor is 0 (caught and converted
        to RPNError by RPNEngine).
        """
        return dividend / divisor

    def power(self, exponent, base):
        """
        Returns base raised to the power of exponent.
        power(exponent, base)
        exponent = int, float — the value typed second
        base = int, float — the value typed first
        """
        return np.power(base, exponent)

    def modulus(self, x, y):
        """
        Returns the remainder of y divided by x.
        modulus(x, y)
        x = int, float — the value typed second (divisor)
        y = int, float — the value typed first (dividend)
        """
        return y % x

    def sqrt(self, x):
        """
        Returns the square root of x.
        Raises RPNError if x is negative.
        """
        if x < 0:
            raise RPNError("Error: cannot take square root of a negative number")
        return np.sqrt(x)

    def square(self, x):
        """Returns x squared (x ** 2)."""
        return np.square(x)

    def reciprocal(self, x):
        """
        Returns 1/x.
        Raises RPNError if x is 0.
        """
        if x == 0:
            raise RPNError("Error: cannot take reciprocal of zero")
        return np.reciprocal(x)

    def absolute(self, x):
        """Returns the absolute value of x."""
        return np.absolute(x)

    def log(self, x):
        """
        Returns the base-10 logarithm of x.
        Raises RPNError if x is zero or negative.
        """
        if x <= 0:
            raise RPNError("Error: logarithm undefined for non-positive numbers")
        return np.log10(x)

    def log_natural(self, x):
        """
        Returns the natural logarithm (base e) of x.
        Raises RPNError if x is zero or negative.
        """
        if x <= 0:
            raise RPNError("Error: logarithm undefined for non-positive numbers")
        return np.log(x)

    def pi(self):
        """Returns the mathematical constant pi."""
        return np.pi

    def e(self):
        """Returns the mathematical constant e (Euler's number)."""
        return 2.7182818284590452353602874713527

class ProbabilityOps:
    """
    Combinatorics and probability-related operations. These methods
    are self-contained and can be used independently of
    RPNEngine/Stack.
    """

    def factorial(self, x):
        """
        Returns x! (x factorial): the product of all positive integers
        up to and including x. By convention, 0! = 1.

        Raises RPNError if x is not a whole number, or if x is negative.
        """
        if x != int(x):
            raise RPNError(f"factorial expects a whole number, got {x}")
        if x < 0:
            raise RPNError("factorial is not defined for negative numbers")

        x = int(x)
        result = 1
        for factor in range(2, x + 1):
            result *= factor
        return float(result)

    def permutation(self, r, n):
        """
        Returns nPr: the number of ways to arrange r items chosen from
        a set of n distinct items, where order matters.

        permutation(r, n)
        n = int, float — the value typed first (size of the full set)
        r = int, float — the value typed second (number of items chosen)

        Formula: n! / (n - r)!

        Raises RPNError (via factorial) if r > n, since that produces
        a negative argument to factorial.
        """
        return self.factorial(n) / self.factorial(n - r)

    def combination(self, r, n):
        """
        Returns nCr: the number of ways to choose r items from a set
        of n distinct items, where order does NOT matter.

        combination(r, n)
        n = int, float — the value typed first (size of the full set)
        r = int, float — the value typed second (number of items chosen)

        Formula: n! / (r! * (n - r)!)

        Raises RPNError (via factorial) if r > n, since that produces
        a negative argument to factorial.
        """
        return self.factorial(n) / (self.factorial(r) * (self.factorial(n - r)))

class StatisticsOps:
    """
    Descriptive statistics operations, operating on an array (list of
    floats) rather than individual scalar values. These methods are
    self-contained and can be used independently of RPNEngine/Stack.

    All methods validate that cf is non-empty; the sample variants
    (stdev, var) additionally require at least 2 elements, since their
    formulas divide by (n - 1).
    """

    def _check_not_empty(self, cf):
        """Raises RPNError if cf has no elements."""
        if len(cf) == 0:
            raise RPNError("Error: statistics functions require a non-empty array")

    def _check_min_size(self, cf, minimum):
        """Raises RPNError if cf has fewer than `minimum` elements."""
        self._check_not_empty(cf)
        if len(cf) < minimum:
            raise RPNError(
                f"Error: this function requires at least {minimum} values, got {len(cf)}"
            )

    def mean(self, cf):
        """Returns the arithmetic mean of the values in cf."""
        self._check_not_empty(cf)
        return np.mean(cf)

    def median(self, cf):
        """Returns the median (middle value) of the values in cf."""
        self._check_not_empty(cf)
        return np.median(cf)

    def stdev(self, cf):
        """
        Returns the sample standard deviation of the values in cf
        (denominator n - 1). Requires at least 2 elements.

        Raises RPNError if cf has fewer than 2 elements.
        """
        self._check_min_size(cf, 2)
        return np.std(cf, ddof=1)

    def stdevp(self, cf):
        """
        Returns the population standard deviation of the values in cf
        (denominator n).

        Raises RPNError if cf is empty.
        """
        self._check_not_empty(cf)
        return np.std(cf, ddof=0)

    def var(self, cf):
        """
        Returns the sample variance of the values in cf
        (denominator n - 1). Requires at least 2 elements.

        Raises RPNError if cf has fewer than 2 elements.
        """
        self._check_min_size(cf, 2)
        return np.var(cf, ddof=1)

    def varp(self, cf):
        """
        Returns the population variance of the values in cf
        (denominator n).

        Raises RPNError if cf is empty.
        """
        self._check_not_empty(cf)
        return np.var(cf, ddof=0)

    def min(self, cf):
        """Returns the smallest value in cf."""
        self._check_not_empty(cf)
        return np.min(cf)

    def max(self, cf):
        """Returns the largest value in cf."""
        self._check_not_empty(cf)
        return np.max(cf)

class TVMOps:
    """
    Time Value of Money operations, backed by numpy_financial. These
    methods are self-contained and can be used independently of
    RPNEngine/Stack, aside from receiving an explicit annuity-mode
    flag (ann) from the caller rather than holding any state of their
    own.

    Exception: effective_rate relies on a compounding-frequency value
    that, at the RPN dispatch layer, is pulled from the engine's
    self.periods_per_year setting rather than being typed explicitly
    — see that method's docstring for details.
    """

    def pv(self, rate, nper, pmt, fv, ann):
        """
        Returns the present value of a series of future cash flows.

        pv(rate, nper, pmt, fv, ann)
        rate = periodic interest rate, as a decimal
        nper = number of periods
        pmt = periodic payment amount
        fv = future value
        ann = annuity mode, "begin" or "end"

        Raises RPNError if the underlying calculation produces a
        non-finite (NaN/inf) result.
        """
        with np.errstate(divide='ignore', invalid='ignore'):
            result = npf.pv(rate, nper, pmt, fv, ann)
        if not np.isfinite(result):
            raise RPNError("Error: pv calculation produced an invalid result")
        return result

    def fv(self, rate, nper, pmt, pv, ann):
        """
        Returns the future value of a series of cash flows.

        fv(rate, nper, pmt, pv, ann)
        rate = periodic interest rate, as a decimal
        nper = number of periods
        pmt = periodic payment amount
        pv = present value
        ann = annuity mode, "begin" or "end"

        Raises RPNError if the underlying calculation produces a
        non-finite (NaN/inf) result.
        """
        with np.errstate(divide='ignore', invalid='ignore'):
            results = npf.fv(rate, nper, pmt, pv, ann)
        if not np.isfinite(results):
            raise RPNError("Error: fv calculation produced an invalid result")
        return results

    def pmt(self, rate, nper, pv, fv, ann):
        """
        Returns the periodic payment required to amortize a loan or
        reach a savings goal.

        pmt(rate, nper, pv, fv, ann)
        rate = periodic interest rate, as a decimal
        nper = number of periods
        pv = present value
        fv = future value
        ann = annuity mode, "begin" or "end"

        Raises RPNError if the underlying calculation produces a
        non-finite (NaN/inf) result.
        """
        with np.errstate(divide='ignore', invalid='ignore'):
            results = npf.pmt(rate, nper, pv, fv, ann)
        if not np.isfinite(results):
            raise RPNError("Error: payment calculation produced an invalid result")
        return results

    def rate(self, nper, pmt, pv, fv, ann):
        """
        Returns the periodic interest rate implied by the given cash
        flows. Solved iteratively; may not converge for all inputs.

        rate(nper, pmt, pv, fv, ann)
        nper = number of periods
        pmt = periodic payment amount
        pv = present value
        fv = future value
        ann = annuity mode, "begin" or "end"

        Raises RPNError if the underlying calculation produces a
        non-finite (NaN/inf) result.
        """
        with np.errstate(divide='ignore', invalid='ignore'):
            results = npf.rate(nper, pmt, pv, fv, ann)
        if not np.isfinite(results):
            raise RPNError("Error: rate calculation produced an invalid result")
        return results

    def nper(self, rate, pmt, pv, fv, ann):
        """
        Returns the number of periods required, given a rate and cash
        flows.

        nper(rate, pmt, pv, fv, ann)
        rate = periodic interest rate, as a decimal
        pmt = periodic payment amount
        pv = present value
        fv = future value
        ann = annuity mode, "begin" or "end"

        Raises RPNError if the underlying calculation produces a
        non-finite (NaN/inf) result.
        """
        with np.errstate(divide='ignore', invalid='ignore'):
            results = npf.nper(rate, pmt, pv, fv, ann)
        if not np.isfinite(results):
            raise RPNError("Error: periods calculation produced an invalid result")
        return results

    def effective_rate(self, rate, cmp):
        """
        Returns the effective annual rate (EAR) given a nominal annual
        rate and a number of compounding periods per year.

        Formula: (1 + rate/cmp)^cmp - 1

        IMPORTANT: at the RPN dispatch layer, `cmp` is NOT typed by
        the user — it is pulled automatically from the engine's
        current self.periods_per_year setting (set via annual/
        semiannual/quarterly/monthly/daily). Only the nominal rate is
        typed:

            0.08 ear   → EAR using whatever compounding mode is
                         currently active (default: annual, meaning
                         periods_per_year = 1)

        This means ear's result depends on session state set earlier
        in the same expression sequence, not just on what's typed in
        this specific call. Confirm (or explicitly set) the current
        compounding mode before relying on this function.
        """
        return ((1 + (rate / cmp)) ** cmp) - 1

    def real_rate(self, inflation, rate):
        """
        Returns the inflation-adjusted (real) rate of return, via the
        Fisher equation.

        Call order: rate inflation rr → e.g. "0.08 0.03 rr" for an 8%
        nominal rate and 3% inflation. Matches the rate-first
        convention used by pv/fv/pmt/nper elsewhere in this
        calculator.
        """
        return ((1 + rate) / (1 + inflation)) - 1

    def percentage_change(self, latest, prior):
        """
        Returns the percentage change from a prior value to a latest
        value, expressed as a decimal fraction (e.g. 0.10 for a 10%
        increase), consistent with how rates are represented elsewhere
        in this calculator.

        Call order: prior latest %chg → e.g. "100 110 %chg" for a
        change from 100 to 110.
        """
        return (latest - prior) / prior

class BondOps:
    """
    Bond pricing and yield operations. price_of_bond and
    yield_to_maturity are thin wrappers around TVMOps (numpy_financial
    under the hood); current_yield is a simple standalone formula.

    All three methods take the coupon as an annual RATE (e.g. 0.08),
    not a pre-converted dollar amount, and perform the
    rate-to-dollar conversion (coupon_rate * face) internally. This
    means all three are self-contained and can be called directly,
    with a consistent interface, independently of RPNEngine.
    """

    def price_of_bond(self, ytm, tm, cpn_rate, face, ann):
        """
        Returns the price of a bond: the present value of its coupon
        payments plus the present value of its face value at
        maturity, discounted at the given yield to maturity.

        price_of_bond(ytm, tm, cpn_rate, face, ann)
        ytm = periodic yield to maturity, as a decimal
        tm = number of periods to maturity
        cpn_rate = annual coupon rate, as a decimal (e.g. 0.08)
        face = face/par value
        ann = annuity mode, "begin" or "end"

        Converts cpn_rate to a periodic dollar coupon internally
        (cpn_rate * face), consistent with current_yield's interface.

        Internally negates the result of TVMOps.pv, which by
        convention returns a negative value for positive cash inflows
        (representing "cash paid out today"). Negating it here
        expresses bond price as a conventional positive amount a
        buyer would pay, matching standard bond-quoting convention.

        Raises RPNError (via TVMOps.pv) if the underlying calculation
        produces a non-finite result.
        """
        tvm = TVMOps()
        cpn = cpn_rate * face
        return -tvm.pv(ytm, tm, cpn, face, ann)

    def yield_to_maturity(self, tm, cpn_rate, price, face, ann):
        """
        Returns the yield to maturity (YTM) of a bond: the periodic
        discount rate that makes the present value of its remaining
        cash flows equal to its current market price. Solved
        iteratively; may not converge for all inputs.

        yield_to_maturity(tm, cpn_rate, price, face, ann)
        tm = number of periods to maturity
        cpn_rate = annual coupon rate, as a decimal (e.g. 0.08)
        price = current market price of the bond
        face = face/par value
        ann = annuity mode, "begin" or "end"

        Converts cpn_rate to a periodic dollar coupon internally
        (cpn_rate * face), consistent with current_yield's interface.

        `price` is negated before being passed to TVMOps.rate as pv,
        so that it represents "cash paid out today" against the
        positive coupon/face cash flows received later.

        Raises RPNError (via TVMOps.rate) if the underlying
        calculation produces a non-finite result.
        """
        tvm = TVMOps()
        cpn = cpn_rate * face
        return tvm.rate(tm, cpn, -price, face, ann)

    def current_yield(self, cpn_rate, face, price):
        """
        Returns current yield: annual dollar coupon / current price.

        current_yield(cpn_rate, face, price)
        cpn_rate = annual coupon rate, as a decimal (e.g. 0.08)
        face = face/par value (e.g. 1000)
        price = current market price of the bond

        Unlike price_of_bond/yield_to_maturity, this method takes the
        coupon as a RATE directly (not a pre-converted dollar amount)
        and performs the rate-to-dollar conversion internally.
        """
        annual_coupon = face * cpn_rate
        return annual_coupon / price

class CapitalBudgetingOps:
    """
    Capital budgeting operations, operating on a cash flow array where
    index 0 is the initial investment (expected to be negative) and
    subsequent indices are periodic cash inflows. Several methods
    wrap numpy_financial; others (pv_cash_flows, payback,
    discounted_payback) are hand-implemented.
    """

    def npv(self, rate, cf):
        """
        Returns the net present value of a cash flow array, given a
        periodic discount rate. cf[0] (the initial investment) is
        included undiscounted, per this calculator's cash flow
        convention.

        npv(rate, cf)
        rate = periodic discount rate, as a decimal
        cf = list[float], cf[0] = initial investment (negative)

        Raises RPNError if the underlying calculation produces a
        non-finite (NaN/inf) result (e.g. rate == -1).
        """
        with np.errstate(divide='ignore', invalid='ignore'):
            result = npf.npv(rate, cf)
        if not np.isfinite(result):
            raise RPNError("Error: npv calculation produced an invalid result")
        return result

    def pv_cash_flows(self, rate, cf):
        """
        Returns the present value of a cash flow array's FUTURE
        inflows only (cf[1:]) — cf[0], the initial investment, is
        deliberately excluded, since this method supports
        profitability_index's standard formula:
        PI = PV(future inflows) / |initial investment|.

        pv_cash_flows(rate, cf)
        rate = periodic discount rate, as a decimal
        cf = list[float], cf[0] = initial investment (excluded from
             this calculation)
        """
        pvc = 0
        for k, v in enumerate(cf[1:]):
            pv = v / (1 + rate)**(k+1)
            pvc += pv
        return pvc

    def irr(self, cf):
        """
        Returns the internal rate of return of a cash flow array: the
        periodic discount rate at which its NPV equals zero. Solved
        iteratively; may not converge for all cash flow patterns
        (e.g. no sign change, or multiple sign changes).

        irr(cf)
        cf = list[float], cf[0] = initial investment (negative)

        Raises RPNError if the underlying calculation produces a
        non-finite (NaN/inf) result.
        """
        with np.errstate(divide='ignore', invalid='ignore'):
            result = npf.irr(cf)
        if not np.isfinite(result):
            raise RPNError("Error: irr calculation produced an invalid result")
        return result

    def profitability_index(self, rate, cf):
        """
        Returns the profitability index (PI) of a cash flow array:
        the present value of future inflows divided by the absolute
        value of the initial investment. PI > 1 indicates a
        value-adding project at the given discount rate.

        profitability_index(rate, cf)
        rate = periodic discount rate, as a decimal
        cf = list[float], cf[0] = initial investment (negative)
        """
        return self.pv_cash_flows(rate, cf) / abs(cf[0])

    def payback(self, cf):
        """
        Returns the (undiscounted) payback period: the number of
        periods required for cumulative cash flow to turn
        non-negative.

        payback(cf)
        cf = list[float], cf[0] = initial investment; must be
             negative, or RPNError is raised

        Returns np.inf if the investment is never recovered within
        the given array.
        """
        if cf[0] >= 0:
            raise RPNError("Error: initial investment (first cash flow) must be negative")

        cumulative = np.cumsum(cf)

        for i, v in enumerate(cumulative):
            if v >= 0:
                if cf[i] == 0:
                    return float(i)  # no further inflow that period; payback lands exactly on i
                return (i - 1) + (abs(cumulative[i - 1]) / cf[i])

        return np.inf  # project never recovers its investment

    def discounted_payback(self, rate, cf):
        """
        Returns the discounted payback period: same concept as
        payback, but future cash flows are first discounted to
        present value at the given rate before accumulating. Will
        always be >= the undiscounted payback period for the same
        cash flows.

        discounted_payback(rate, cf)
        rate = periodic discount rate, as a decimal
        cf = list[float], cf[0] = initial investment (negative)

        Internally reuses payback() after discounting cf[1:] and
        re-prepending the original, undiscounted cf[0] — since a
        time-0 cash flow is not discounted (discount factor = 1).
        """
        discounted_cf = list()
        for k, v in enumerate(cf[1:]):
            pv = v / (1 + rate)**(k+1)
            discounted_cf.append(pv)

        discounted_pb = self.payback([cf[0]] + discounted_cf)

        return discounted_pb

class RPNError(Exception):
    """
    Raised for any error condition specific to evaluating an RPN
    expression or calculator operation — e.g. division by zero,
    malformed input, invalid domain for a math function, or a
    calculation that produced a non-finite (NaN/inf) result.

    This is the one exception type the calculator's callers (CLI,
    and eventually the GUI) need to catch to handle all
    calculator-level errors uniformly and present a clean message to
    the user, rather than letting a raw Python exception (IndexError,
    ZeroDivisionError, TypeError, etc.) propagate and crash the
    program.

    Lower-level components (e.g. Stack) intentionally do NOT raise
    RPNError directly — they raise plain Python exceptions
    (IndexError, etc.), which RPNEngine.evaluate_rpn() catches and
    translates into RPNError. This keeps RPNError's dependency
    confined to the RPN/dispatch layer rather than leaking into
    generic, reusable components.
    """
    pass

class RPNResult(NamedTuple):
    """
    Result of RPNEngine.safe_evaluate(): a self-describing pairing of
    success/failure with the corresponding value, so a caller never
    has to guess what a bare return value means.
    """
    ok: bool
    value: Optional[Union[float, str]]

class RPNEngine:
    """
    The core RPN calculator engine. Tokenizes a raw expression string,
    evaluates it against a stack using the dispatch table in
    self.operations, and returns a single numeric result (or None, for
    expressions consisting entirely of state-setting tokens like
    'round', 'begin', 'monthly', etc.).

    Holds three pieces of persistent session state that affect
    subsequent calculations without being typed explicitly each time:
      - self.annuity_mode ("begin"/"end") — affects TVM functions
      - self.periods_per_year — affects TVM/bond/ear functions' rate
        and period conversions
      - self.decimal_places — rounds the final returned result, if set

    All *Ops classes (MathOps, TVMOps, etc.) are composed here rather
    than inherited from, and remain independently usable/testable
    without RPNEngine.
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.array = list()  # Colects CF, Stat Data
        self.stack = Stack() # Main stack
        self.annuity_mode = "end"
        self.periods_per_year = 1
        self.decimal_places = None

        tvm = TVMOps()
        math = MathOps()
        bond = BondOps()
        stats = StatisticsOps()
        probability = ProbabilityOps()
        cap_budgeting = CapitalBudgetingOps()

        self.operations = {
            # Output
            "round": (self.set_decimal_places, 1),

            # Annuity mode
            "begin": (self.set_begin, 0),
            "end": (self.set_end, 0),

            # Compounding periods
            "annual": (self.set_annual, 0),
            "semiannual": (self.set_semiannual, 0),
            "quarterly": (self.set_quarterly, 0),
            "monthly": (self.set_monthly, 0),
            "daily": (self.set_daily, 0),

            # Math
            "+": (math.add, 2),
            "-": (math.subtract, 2),
            "*": (math.multiply, 2),
            "/": (math.divide, 2),
            "pow": (math.power, 2),
            "mod": (math.modulus, 2),
            "sqrt": (math.sqrt, 1),
            "square": (math.square, 1),
            "1/x": (math.reciprocal, 1),
            "log": (math.log, 1),
            "ln": (math.log_natural, 1),
            "abs": (math.absolute, 1),
            "pi": (math.pi, 0),
            "e": (math.e, 0),

            # Probability
            "fact": (probability.factorial, 1),
            "nPr": (probability.permutation, 2),
            "nCr": (probability.combination, 2),

            # Statistics
            "mean": (stats.mean, 1),
            "median": (stats.median, 1),
            "stdev": (stats.stdev, 1),
            "stdevp": (stats.stdevp, 1),
            "var": (stats.var, 1),
            "varp": (stats.varp, 1),
            "min": (stats.min, 1),
            "max": (stats.max, 1),

            # Time Value
            "pv": (tvm.pv, 4),
            "fv": (tvm.fv, 4),
            "pmt": (tvm.pmt, 4),
            "rate": (tvm.rate, 4),
            "nper": (tvm.nper, 4),
            "ear": (tvm.effective_rate, 1),
            "rr": (tvm.real_rate, 2),
            "%chg": (tvm.percentage_change, 2),

            # Capital Budgeting
            "npv": (cap_budgeting.npv, 2),
            "pindex": (cap_budgeting.profitability_index, 2),
            "pvc": (cap_budgeting.pv_cash_flows, 2),
            "irr": (cap_budgeting.irr, 1),
            "pb": (cap_budgeting.payback, 1),
            "dpb": (cap_budgeting.discounted_payback, 2),

            # Bonds
            "price": (bond.price_of_bond, 4),
            "ytm": (bond.yield_to_maturity, 4),
            "cy": (bond.current_yield, 3),
        }

    def set_begin(self):
        """Sets annuity mode to 'begin' (payments at start of period)."""
        self.annuity_mode = "begin"
        return None

    def set_end(self):
        """Sets annuity mode to 'end' (payments at end of period) — default."""
        self.annuity_mode = "end"
        return None

    def set_annual(self):
        """Sets compounding periods per year to 1 — default."""
        self.periods_per_year = 1
        return None

    def set_semiannual(self):
        """Sets compounding periods per year to 2."""
        self.periods_per_year = 2
        return None

    def set_quarterly(self):
        """Sets compounding periods per year to 4."""
        self.periods_per_year = 4
        return None

    def set_monthly(self):
        """Sets compounding periods per year to 12."""
        self.periods_per_year = 12
        return None

    def set_daily(self):
        """Sets compounding periods per year to 365."""
        self.periods_per_year = 365
        return None

    def set_decimal_places(self, places):
        """
        Sets the number of decimal places the final result of
        evaluate_rpn() will be rounded to. Applies only to the final
        returned value — intermediate calculations within the same
        expression always use full precision.

        Raises RPNError if places is not a whole number, or is
        outside the 0-8 range.
        """
        if places != int(places):
            raise RPNError(f"Error: decimal places must be a whole number, got {places}")

        if places < 0 or places > 8:
            raise RPNError("Error: decimal places must be a whole number between 0 and 8")

        self.decimal_places = int(places)

        return None

    def tokenizer(self):
        """
        Converts the raw input string into a list of tokens. Supports
        at most one bracketed array group ([...]), which must appear
        at the start of the string; its contents are parsed into a
        list[float] and returned as a single token. Everything after
        the closing bracket (or the entire string, if no array is
        present) is split on whitespace into individual tokens.

        Raises RPNError on missing/mismatched brackets or a
        non-numeric value inside the array.
        """
        s = self.tokens
        array = list()

        if s.startswith("["):
            start = s.find("[")
            end = s.find("]", start)

            if end == -1:
                raise RPNError("Error: missing closing bracket")

            inner = s[start+1:end]
            rest = s[end+1:].strip()

            if "[" in rest or "]" in rest:
                raise RPNError("Error: mismatched brackets")

            try:
                lst = list(map(float, inner.split()))
            except ValueError:
                raise RPNError("Error: invalid number in array")

            array.append(lst)
            for token in rest.split():
                array.append(token)

        elif "]" in s:
            raise RPNError("Error: missing opening bracket")

        else:
            array = s.split()

        return array

    def evaluate_rpn(self):
        """
        Evaluates the tokenized RPN expression and returns a single
        result: a float (optionally rounded per self.decimal_places),
        or None if the expression consisted entirely of state-setting
        tokens (round/begin/end/annual/etc.) with no numeric result
        to return.

        Raises RPNError for empty expressions, unrecognized tokens,
        division by zero, insufficient operands, or a malformed
        expression (more than one value left on the stack at the end).
        """
        self.stack = Stack()
        tokens = self.tokenizer()

        if len(tokens) == 0:
            raise RPNError("Error: empty expression")

        for token in tokens:
            try:
                self.stack.push(float(token))
            except TypeError:
                self.stack.push(token)
            except ValueError:
                if token not in self.operations.keys():
                    raise RPNError(f"Error: unrecognized token: {token}")
                try:
                    p_stack = []
                    for _ in range(self.operations[token][1]):
                        p_stack.append(self.stack.pop())

                    match(self.operations[token][1]):
                        case 0:
                            results = self.operations[token][0]()
                            if results is not None:
                                self.stack.push(results)
                        case 1:
                            if token == "ear":
                                nominal = p_stack[0]
                                compounding = self.periods_per_year
                                self.stack.push(self.operations[token][0](nominal, compounding))
                            else:
                                results = self.operations[token][0](p_stack[0])
                                if results is not None:
                                    self.stack.push(results)
                        case 2:
                            self.stack.push(self.operations[token][0](p_stack[0], p_stack[1]))
                        case 3:
                            if token == "cy":
                                cpn_rate = p_stack[2]   # typed first
                                face = p_stack[1]       # typed second
                                price = p_stack[0]      # typed third
                                self.stack.push(self.operations[token][0](cpn_rate, face, price))
                            else:
                                self.stack.push(self.operations[token][0](p_stack[0], p_stack[1], p_stack[2]))
                        case 4:
                            """
                            Time Value of Money and Bond operations — order matters.

                            Typed order (left to right) and what each function solves for:

                              pv:    rate  nper  pmt      fv       -> pv
                              fv:    rate  nper  pmt      pv       -> fv
                              nper:  rate  pmt   pv       fv       -> nper
                              rate:  nper  pmt   pv       fv       -> rate
                              pmt:   rate  nper  pv       fv       -> pmt
                              price: ytm   tm    cpn_rate face     -> price
                              ytm:   tm    cpn_rate price   face   -> ytm

                            Conversions applied via self.periods_per_year, so that
                            every typed rate is a nominal annual rate and every
                            typed period count (nper/tm) is expressed in years,
                            regardless of the active compounding mode:

                              - typed rate  -> divided by periods_per_year going in
                              - typed years -> multiplied by periods_per_year going in
                              - a returned periodic rate (rate, ytm) is multiplied
                                by periods_per_year going out, to report a nominal
                                annual rate
                              - a returned period count (nper) is divided by
                                periods_per_year going out, to report years

                            This keeps rate/nper/ytm consistent with each other and
                            with how pv/fv/pmt expect their inputs, regardless of
                            which compounding mode (annual/monthly/etc.) is active.

                            For every TVM function I could just do a one liner like this:

                            self.stack.push(self.operations[token][0](p_stack[3],p_stack[2],p_stack[1],p_stack[0]))

                            and it would work given the data entry follow a specific order. However to maintain
                            clarity of what is going on with each function, I wrote an if/else structure that
                            will look repetitive and clumsy, however I believe it is the better choice for understandability
                            and future maintenace.
                            """

                            if token == "pv":
                                rate = p_stack[3] / self.periods_per_year
                                nper = self.periods_per_year * p_stack[2]
                                pmt = p_stack[1]
                                fv = p_stack[0]
                                self.stack.push(self.operations[token][0](rate, nper, pmt, fv, self.annuity_mode))
                            elif token == "fv":
                                rate = p_stack[3] / self.periods_per_year
                                nper = self.periods_per_year * p_stack[2]
                                pmt = p_stack[1]
                                pv = p_stack[0]
                                self.stack.push(self.operations[token][0](rate, nper, pmt, pv, self.annuity_mode))
                            elif token == "nper":
                                rate = p_stack[3] / self.periods_per_year
                                pmt = p_stack[2]
                                pv = p_stack[1]
                                fv = p_stack[0]
                                periods = self.operations[token][0](rate, pmt, pv, fv, self.annuity_mode)
                                self.stack.push(periods / self.periods_per_year)
                            elif token == "rate":
                                nper = self.periods_per_year * p_stack[3]
                                pmt = p_stack[2]
                                pv = p_stack[1]
                                fv = p_stack[0]
                                periodic_rate = self.operations[token][0](nper, pmt, pv, fv, self.annuity_mode)
                                self.stack.push(periodic_rate * self.periods_per_year)
                            elif token == "pmt":
                                rate = p_stack[3] / self.periods_per_year
                                nper = self.periods_per_year * p_stack[2]
                                pv = p_stack[1]
                                fv = p_stack[0]
                                self.stack.push(self.operations[token][0](rate, nper, pv, fv, self.annuity_mode))
                            elif token == "price":
                                ytm = p_stack[3] / self.periods_per_year
                                tm = self.periods_per_year * p_stack[2]
                                cpn_rate = p_stack[1]
                                face = p_stack[0]
                                self.stack.push(self.operations[token][0](ytm, tm, cpn_rate, face, self.annuity_mode))
                            elif token == "ytm":
                                tm = self.periods_per_year * p_stack[3]
                                cpn_rate = p_stack[2]
                                price = p_stack[1]
                                face = p_stack[0]
                                periodic_yield = self.operations[token][0](tm, cpn_rate, price, face, self.annuity_mode)
                                self.stack.push(periodic_yield * self.periods_per_year)

                except ZeroDivisionError:
                    raise RPNError("Error: division by zero")
                except IndexError:
                    raise RPNError("Error: insufficient operands")

        if self.stack.size_of() > 1:
            raise RPNError("Error: malformed expression, stack has >1 item at end")

        if self.stack.size_of() == 0:
            return None

        result = self.stack.stack[0]

        if self.decimal_places is not None:
            result = round(result, self.decimal_places)

        return result

    def safe_evaluate(self):
        """
        Convenience wrapper around evaluate_rpn() for callers (scripts,
        notebooks, simple REPLs) that just want a printable result or
        error message without writing their own try/except.

        Returns an RPNResult:
        - RPNResult(ok=True, value=result) on success (result may be
            None, for pure state-setting expressions like "2 round")
        - RPNResult(ok=False, value=error_message) on failure

        evaluate_rpn() itself still raises RPNError on failure — use it
        directly if you need to handle success/failure with different
        control flow (e.g. a GUI updating different UI elements
        depending on outcome).
        """
        try:
            return RPNResult(True, self.evaluate_rpn())
        except RPNError as e:
            return RPNResult(False, str(e))

if __name__ == "__main__":
    def test_bondops_consistency():
        tests = [
            # --- Regression: same typed inputs and expected results as before the refactor ---
            ("0.10 10 0.08 1000 price", 877.11),
            ("10 0.08 877.11 1000 ytm", 0.10),
            ("0.08 1000 877.11 cy", 0.0912),
        ]

        for expr, expected in tests:
            calc = RPNEngine(expr)
            result = calc.safe_evaluate()
            status = "OK" if result.ok else "ERR"
            print(f"{expr!r:35} -> {result.value!r:45} (expected: {expected!r}, status: {status})")

    test_bondops_consistency()
