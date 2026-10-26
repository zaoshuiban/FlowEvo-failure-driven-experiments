"""Offline research scoring adapters; never imports or changes a frozen S20-A module."""
import re,math
from decimal import Decimal,InvalidOperation
VERSION='external-scorer-v2'

def accepts(dataset,expected,actual,case_insensitive=False):
    if not isinstance(expected,str) or not isinstance(actual,str):return False
    if dataset=='lcb':
        # Pinned official grade_stdio: stripped lines, then exact Decimal vectors.
        a=[x.strip() for x in actual.strip().split('\n')];b=[x.strip() for x in expected.strip().split('\n')]
        if len(a)!=len(b):return False
        for x,y in zip(a,b):
            if x==y:continue
            try:
                dx=[Decimal(t) for t in x.split()];dy=[Decimal(t) for t in y.split()]
                if not all(v.is_finite() for v in dx+dy) or dx!=dy:return False
            except InvalidOperation:return False
        return True
    a=actual.split();b=expected.split()
    if len(a)!=len(b):return False
    if dataset=='cc':
        # Official ASCII case normalization, numeric absolute tolerance 1e-5.
        # Declared safety correction: integer expectations stay exact, including >2**53.
        for x,y in zip(a,b):
            ascii_lower=str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')
            if x.translate(ascii_lower)==y.translate(ascii_lower):continue
            numeric=r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?'
            if not re.fullmatch(numeric,x) or not re.fullmatch(numeric,y):return False
            try:
                dx,dy=Decimal(x),Decimal(y)
                if not dx.is_finite() or not dy.is_finite():return False
                if re.fullmatch(r'[+-]?\d+',y):
                    if dx!=dy:return False
                elif not abs(dx-dy)<Decimal('0.00001'):return False
            except InvalidOperation:return False
        return True
    # APPS official IO, order/multiplicity-preserving research comparator.
    # Deliberately not the legacy set/allclose fallback.
    return ([x.lower() for x in a]==[x.lower() for x in b]) if case_insensitive else a==b
