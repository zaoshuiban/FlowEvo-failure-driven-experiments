import sys
from decimal import Decimal, getcontext

getcontext().prec = 100
EPS = Decimal('1e-70')

def main():
    data = sys.stdin.read().split()
    if not data:
        return

    vals = [Decimal(data[i]) for i in range(3)]
    logs = [v.ln() for v in vals]

    # (base_index, exponent_type, first_inner_index, second_inner_index, output_name)
    # T: base^(u^v), ln(exponent) = v * ln(u)
    # P: (base^u)^v = base^(u*v), ln(exponent) = ln(u) + ln(v)
    specs = [
        (0, 'T', 1, 2, "x^y^z"),
        (0, 'T', 2, 1, "x^z^y"),
        (0, 'P', 1, 2, "(x^y)^z"),
        (0, 'P', 2, 1, "(x^z)^y"),
        (1, 'T', 0, 2, "y^x^z"),
        (1, 'T', 2, 0, "y^z^x"),
        (1, 'P', 0, 2, "(y^x)^z"),
        (1, 'P', 2, 0, "(y^z)^x"),
        (2, 'T', 0, 1, "z^x^y"),
        (2, 'T', 1, 0, "z^y^x"),
        (2, 'P', 0, 1, "(z^x)^y"),
        (2, 'P', 1, 0, "(z^y)^x")
    ]

    def log_exponent(typ, u, v):
        if typ == 'T':
            return logs[u] * vals[v]
        return logs[u] + logs[v]

    one = Decimal(1)

    if any(v > one for v in vals):
        best_score = None
        best_idx = 0

        for i, (b, typ, u, v, name) in enumerate(specs):
            if vals[b] <= one:
                continue

            ln_e = log_exponent(typ, u, v)
            score = ln_e + logs[b].ln()

            if best_score is None or score > best_score + EPS:
                best_score = score
                best_idx = i

        print(specs[best_idx][4])

    elif any(v == one for v in vals):
        for b, typ, u, v, name in specs:
            if vals[b] == one:
                print(name)
                return

    else:
        best_score = None
        best_idx = 0

        for i, (b, typ, u, v, name) in enumerate(specs):
            ln_e = log_exponent(typ, u, v)
            neg_ln_base = -logs[b]
            score = ln_e + neg_ln_base.ln()

            if best_score is None or score < best_score - EPS:
                best_score = score
                best_idx = i

        print(specs[best_idx][4])


if __name__ == "__main__":
    main()