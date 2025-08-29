#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-08-29 18:44:03 (ywatanabe)"
# File: /home/ywatanabe/proj/screen-manager/examples/script_with_cipdb.py
# ----------------------------------------
from __future__ import annotations
import os
__FILE__ = (
    "./examples/script_with_cipdb.py"
)
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------

import cipdb


def main():
    try:
        return 1 / 0
    except Exception as e:
        print(e)
        cipdb.set_trace(id="zero-division")


main()

# EOF
