#!/bin/sh
source ~/.bashrc
python3 acc.py run $@ >> ../logs/info.log
