#!/usr/bin/env bash

rm plc.log

#./sc.py &
../rplc.py --debug 1 --system_config="$PWD/default_plc.cfg"
