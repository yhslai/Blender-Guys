import bpy
import math
import os
import sys

def angles_to_str(theta, phi):
    return f"{theta}, {phi}"

def parse_angles(s: str):
    lhs, _, rhs = s.partition(",")
    try:
        return float(lhs), float(rhs)
    except ValueError:
        return math.nan, math.nan

def greater_or_close(a, b):
    return a > b or math.isclose(a, b)

def less_or_close(a, b):
    return a < b or math.isclose(a, b)