#!/usr/bin/env python2
# Report pairs in FR RF orientations

# USAGE: samtools view -h repeats.bam | ./sam2inverted_repeats.py | samtools view -Sbu - | samtools view -Sb - repeats.inverted

import sys

for l in sys.stdin:
    ldata = l.split()
    if l.startswith('@') or not int(ldata[1]) & 16 and not int(ldata[1]) & 32:
        sys.stdout.write(l)
        
