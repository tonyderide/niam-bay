#!/usr/bin/env python3
"""Patch morning_brief_v2.py: fix REPO_ROOT, add ADA/LINK to GRID_RANGES and PAIRS_KRAKEN."""
fp = '/home/ubuntu/morning_brief_v2.py'
with open(fp) as f:
    s = f.read()

# 1. Fix REPO_ROOT: parent.parent -> parent
old_root = 'REPO_ROOT = pathlib.Path(__file__).parent.parent'
new_root = 'REPO_ROOT = pathlib.Path(__file__).parent'
if old_root in s:
    s = s.replace(old_root, new_root)
    print('[1/3] REPO_ROOT fixed')
else:
    print('[1/3] REPO_ROOT not found')

# 2. Add LINK, ADA to GRID_RANGES (Compounder config: SOL/LINK/ADA/DOT)
old_ranges = '''GRID_RANGES = {
    "PF_XXBTZUSD": (70000, 110000, 90000),
    "PF_XETHZUSD": (1800,  3500,   2600),
    "PF_SOLUSD":   (100,   250,    170),
    "PF_DOTUSD":   (4.0,   12.0,   7.5),
}'''
new_ranges = '''GRID_RANGES = {
    "PF_XXBTZUSD": (70000, 110000, 90000),
    "PF_XETHZUSD": (1800,  3500,   2600),
    "PF_SOLUSD":   (80,    100,    89),
    "PF_DOTUSD":   (1.20,  1.40,   1.30),
    "PF_LINKUSD":  (9.0,   10.5,   9.7),
    "PF_ADAUSD":   (0.23,  0.27,   0.255),
}'''
if old_ranges in s:
    s = s.replace(old_ranges, new_ranges)
    print('[2/3] GRID_RANGES updated with LINK/ADA + corrected SOL/DOT')
else:
    print('[2/3] GRID_RANGES not found')

# 3. Add LINK, ADA to PAIRS_KRAKEN (the market prices lookup)
old_pairs = '''    "DOT":  "DOTUSD",
}'''
new_pairs = '''    "DOT":  "DOTUSD",
    "LINK": "LINKUSD",
    "ADA":  "ADAUSD",
}'''
# Only replace the specific DOT trailing, not other matches
if old_pairs in s:
    s = s.replace(old_pairs, new_pairs, 1)
    print('[3/3] PAIRS_KRAKEN updated')
else:
    print('[3/3] PAIRS_KRAKEN not found')

with open(fp, 'w') as f:
    f.write(s)
print('done')
