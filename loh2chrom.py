#!/usr/bin/env python2
"""Generate chromosome characteristics plot for testing for meiosis-associated 
recombination. 

USAGE: loh2chrom.py ../../ref/CANOR.chromosomes.fa.fai Ch_T3_7318.bam.gatk.homo.100bp.cov_flt.bed
"""

import os, sys
import numpy as np
from scipy import stats

ref_fai = sys.argv[1]
beds = sys.argv[2:]
telomerSize = 0 #150000

#load chrom sizes
chrom2size = {}
for l in open(ref_fai):
  chrom, size = l.split()[:2]
  size = int(size)
  if size>100000: #size>-3*telomerSize and 
    chrom2size[chrom] = size

chrs, LOHs, hetero = [], [], []
for bed in beds:  
  #get loh in chromosomes
  chrom2lohs = {chrom: [] for chrom in chrom2size}  
  for l in open(bed):
    chrom, s, e = l.split()[:3]
    s, e = int(s), int(e)
    #skip if loh in subtelomeric region
    if chrom not in chrom2size or s<telomerSize or e>chrom2size[chrom]-telomerSize:
      continue
    chrom2lohs[chrom].append(e-s)
  #update chr sizes, loh and hetero
  chrs += [size for chrom, size in sorted(chrom2size.items())] #-2*telomerSize
  loh   = [np.mean(lohs) for chrom, lohs in sorted(chrom2lohs.items())]
  LOHs += loh
  hetero += [100-100.0*sum(lohs)/size for (chrom, size), (chrom, lohs) in zip(sorted(chrom2size.items()), sorted(chrom2lohs.items()))]

#get in Mb and in k
LOHs=np.array(LOHs) / 1e3
chrs=np.array(chrs) / 1e6
#print len(chrs), len(LOHs), len(hetero), sorted(chrom2size.items())
'''print "#sample\tchromosome size\tLOH total\tLOH median\tLOH mean\tLOH stdev"
for (chrom, size), (chrom, lohs) in zip(sorted(chrom2size.items()), sorted(chrom2lohs.items())):
  print "%s\t%s\t%s\t%s\t%s\t%s"%(chrom, size, sum(lohs), np.median(lohs), np.mean(lohs), np.std(lohs))'''

print "LOH mean size vs Chromosome size"
print " Pearson: r=%s p=%s" % stats.pearsonr(LOHs, chrs)
print " Spearman: r=%s p=%s" % stats.spearmanr(LOHs, chrs)
print "Heterozygous % vs Chromosome size"
print " Pearson: r=%s p=%s" % stats.pearsonr(hetero, chrs)
print " Spearman: r=%s p=%s" % stats.spearmanr(hetero, chrs)

import matplotlib.pyplot as plt

fig = plt.figure()
ax1 = fig.add_subplot(2,1,1)
ax2 = fig.add_subplot(2,1,2)
p1, = ax1.plot(chrs, hetero, "bo", label="Heterozygous")
ax1.set_ylabel("Heterozygous [%]")
ax2.set_xlabel("Chromosome size [Mb]")
p2, = ax2.plot(chrs, LOHs, "ro", label="LOH mean size")
ax2.set_ylabel("Mean size [kb]")
plt.show()



