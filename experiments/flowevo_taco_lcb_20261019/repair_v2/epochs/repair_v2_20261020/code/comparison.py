"""Typed comparisons: float tolerances are opt-in, never global."""
from decimal import Decimal, InvalidOperation, localcontext


def number_equal(actual, expected, policy):
    try:
        with localcontext() as ctx:
            ctx.prec = 200
            a, b = Decimal(str(actual)), Decimal(str(expected))
            if not (a.is_finite() and b.is_finite()):
                return False
            epsilon = Decimal(policy["epsilon"])
            bound = epsilon if policy["error_mode"] == "absolute" else epsilon * max(Decimal(1), abs(b))
            return abs(a - b) < bound if policy.get("strict") else abs(a - b) <= bound
    except (InvalidOperation, ValueError, TypeError):
        return False


def structured_equal(actual, expected, policy):
    if isinstance(expected, bool):
        return isinstance(actual, bool) and actual == expected
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(
            structured_equal(a, b, policy) for a, b in zip(actual, expected))
    if isinstance(expected, dict):
        return isinstance(actual, dict) and set(actual) == set(expected) and all(
            structured_equal(actual[k], v, policy) for k, v in expected.items())
    if expected is None:
        return actual is None
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        if isinstance(actual, bool) or not isinstance(actual, (int, float)):
            return False
        if policy.get("epsilon"):
            return number_equal(actual, expected, policy)
        # Python's numeric equality must not silently round a large int to float.
        return type(actual) is type(expected) and actual == expected
    return type(actual) is type(expected) and actual == expected


def stdio_equal(actual, expected, policy):
    a, b = actual.split(), expected.split()
    if len(a) != len(b):
        return False
    if policy.get("epsilon"):
        if policy.get("negative_one_sentinel") and b == ["-1"]:
            return a == b
        return all(number_equal(x, y, policy) for x, y in zip(a, b))
    if policy.get("case_insensitive"):
        return [x.casefold() for x in a] == [x.casefold() for x in b]
    return a == b


def normalize_legacy(dataset, raw_code, metadata=None):
    """Dataset result codes differ. Metadata refines -4, never guesses PASS."""
    metadata = metadata or {}
    if raw_code is True or raw_code == 1:
        return "PASS"
    if dataset == "lcb":
        status = {0: "WRONG_ANSWER", -2: "WRONG_ANSWER", -3: "TIME_LIMIT", -4: "EXECUTION_ERROR"}.get(raw_code, "EVALUATOR_ERROR")
        if raw_code == -4:
            msg = (metadata.get("error", "") + metadata.get("error_message", "")).lower()
            if "syntaxerror" in msg or "invalid syntax" in msg:
                return "COMPILE_ERROR"
            if "runtime error" in msg:
                return "RUNTIME_ERROR"
        return status
    return {0: "WRONG_ANSWER", -1: "TIME_LIMIT", -2: "LOAD_ERROR", -3: "RUNTIME_ERROR", -4: "COMPILE_ERROR"}.get(raw_code, "EVALUATOR_ERROR")


PUBLIC_FEEDBACK = {
    "PASS": "All valid tests passed.", "WRONG_ANSWER": "Wrong answer on a valid test.",
    "TIME_LIMIT": "Time limit exceeded.", "RUNTIME_ERROR": "Candidate runtime error.",
    "COMPILE_ERROR": "Candidate syntax or compilation error.", "NO_COMPLETE_CODE": "No complete executable code was produced.",
    "INVALID_TEST": "Evaluation suspended: invalid test data.",
    "REFERENCE_DISPUTE": "Evaluation suspended: reference output is disputed.",
    "CHECKER_UNSUPPORTED": "Evaluation suspended: required answer checker is unavailable.",
    "PROTOCOL_UNSUPPORTED": "Evaluation suspended: task protocol is unsupported.",
    "EVALUATOR_ERROR": "Evaluation infrastructure failed; this is not a candidate failure.",
}


def solver_feedback(verdict):
    # Whitelist only. Never forward hidden inputs, expected values or raw traceback.
    status = verdict["status"]
    return {"status": status, "feedback": PUBLIC_FEEDBACK.get(status, "Candidate execution failed.")}
