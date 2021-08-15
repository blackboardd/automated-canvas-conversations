#!/bin/sh
source ~/.bashrc
python3 acc.py run $@ >> info.log
