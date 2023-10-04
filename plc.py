#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import multiprocessing as mp

if mp.get_start_method() != "spawn":
    print(f"MP start method is {mp.get_start_method().__repr__()}, setting to 'spawn'")
    mp.set_start_method("spawn", force=True)

if __name__ == "__main__":
    mp.freeze_support()

    from plc import plc

    sys.exit(plc.main())  # type: ignore
