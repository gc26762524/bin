#!/usr/bin/env python2
desc="""Plot histogram
"""
epilog="""Author:
l.p.pryszcz+git@gmail.com

Barcelona, 29/11/2012
"""

import argparse, os, sys, random
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from scipy.stats import stats, wilcoxon, ranksums

def group_values(x, y):
  """Group values in y to seperate lists using x"""
  key2group = {}
  for k, v in zip(x, y):
      if k not in key2group:
          key2group[k] = []
      key2group[k].append(v)
  return [v for k, v in sorted(key2group.iteritems())]

def pairwise_wilcoxon(x, y, bootstrapping=10, ranksums=ranksums):
  """Return pairwise wilcoson stats"""
  setx = set(x)
  sety = set(y)
  if   len(setx)<20:  
      values = group_values(x, y)
  elif len(sety)<20:
      values = group_values(y, x)
  else:
      return
  # 1 vs rest
  first = values[0]
  second = [i for items in values[1:] for i in items]
  t, p = ranksums(first, second) 
  print " mean first: %s +/- %s\n mean the_rest: %s +/- %s"%(np.mean(first), np.std(first), np.mean(second), np.std(second))  
  print "Wilcoxon first-vs-the_rest (N=%s vs N=%s): T=%s p=%s" % ((len(first), len(second), t, p))
  # first -vs - second
  second = values[1]
  t, p = ranksums(first, second) 
  print " mean first: %s +/- %s\n mean seond: %s +/- %s"%(np.mean(first), np.std(first), np.mean(second), np.std(second))  
  print "Wilcoxon first-vs-second (N=%s vs N=%s): T=%s p=%s" % ((len(first), len(second), t, p))
  '''for i in range(bootstrapping):
    sfirst = random.sample(first, len(rest))
    t, p = wilcoxon(sfirst, rest)
    print "%s Wilcoxon (1st-vs-rest): T=%s p=%s" % (i+1, t, p)'''

def plot(handles, out, cols, names, bins, title, xlab, ylab, xlog, ylog, \
         vmax, vmin, vMinSum, collapse, normed, alpha, legendLoc, colors,\
         headerLines, verbose, dlimit=1):
    """
    """
    fig = plt.figure()
    #add subplots
    plt.rc('axes', color_cycle=colors) #['c', 'm', 'y', 'k']
    
    for handle in handles:
        if verbose:
            sys.stderr.write( "Parsing data...\n" )
        x = [[] for i in range(len(cols))]
        for i, l in enumerate(handle):
            if i<headerLines:
                continue
            try:
                ldata = l[:-1].split('\t')
                vals = []
                for col in cols:
                    if col>=len(ldata) or not ldata[col]:
                        continue
                    v=float(ldata[col])
                    if vmin<v<vmax:
                        vals.append(v)
                #skip entire line if one value out of bounds
                # or if sum of values below threshold
                if len(vals)!=len(cols) or sum(vals)<vMinSum:
                    continue
                for i, v in enumerate(vals):
                    x[i].append(v)
            except:
                sys.stderr.write("[Error] Cannot parse line: %s\n" % ",".join(l.split('\t')))
        if verbose:
            sys.stderr.write( " %s values loaded.\n" % len(x) )
        #plot
        x, y = x

        # get correlation
        print "%s points\n mean X: %s +/- %s\n mean Y: %s +/- %s"%(len(x), np.mean(x), np.std(x), np.mean(y), np.std(y))
        print "Pearson: r=%s p=%s" % stats.pearsonr(x, y)
        print "Spearman: r=%s p=%s" % stats.spearmanr(x, y)
        print "Wilcoxon: T=%s p=%s" % ranksums(x, y) # wilcoxon(x, y)

        pairwise_wilcoxon(x, y)

        ax = fig.add_subplot(111)
        label = os.path.basename(handle.name)
        ax.plot(x, y, marker=".", linewidth=0, alpha=0.5, label=label) # 'b.'

    #add title
    ax.set_title(title)
    #add subplots labels
    ax.set_xlabel(xlab)#, fontsize=30)
    ax.set_ylabel(ylab)#, fontsize=30)
    #plot legend only if collapsed
    if xlog:
    	ax.set_xscale('log')
    if ylog:
        ax.set_yscale('log', nonposy='clip')

    ax.grid(True)
    #save or show
    if type(out) is file and out.name=='<stdout>':
    	plt.show()
    else:
        fpath = out #handle.name+".png"
        fformat = fpath.split('.')[-1] 
        plt.savefig(fpath.replace(fformat,'nolegend.'+fformat), dpi=300, format=fformat, orientation='landscape', transparent=False)
        ax.legend(loc=legendLoc)
        plt.savefig(fpath, dpi=300, format=fformat, orientation='landscape', transparent=False)        
        sys.stderr.write("Figure written to: %s\n" % fpath)
    
    
def main():
    
    usage   = "%(prog)s [options] -v" 
    parser  = argparse.ArgumentParser( usage=usage,description=desc,epilog=epilog )
  
    parser.add_argument("-v", "--verbose", default=False, action="store_true", help="verbose")    
    parser.add_argument('--version', action='version', version='1.0')
    parser.add_argument("-i", "--input",   default=sys.stdin, type=file, nargs="+", 
                        help="input           [stdin]")
    parser.add_argument("-o", "--output",  default=sys.stdout, 
                        help="input           [stdout]")
    parser.add_argument("-b", "--bins",    default=100, type=int,
                        help="number of bins  [%(default)s]")
    parser.add_argument("-c", "--col",     default=[1, 2], nargs="+", type=int,
                        help="columns to use  [%(default)s]")
    parser.add_argument("-n", "--names",   default="", nargs="+", 
                        help="column names    [%(default)s]")
    parser.add_argument("-t", "--title",   default="Histogram", 
                        help="histogram title [%(default)s]")
    parser.add_argument("-x", "--xlab",    default="", 
                        help="x-axis label    [%(default)s]")
    parser.add_argument("-y", "--ylab",    default="", 
                        help="y-axis label    [%(default)s]")
    parser.add_argument("--ylog", "--log", default=False, action="store_true",
                        help="log Y scale")
    parser.add_argument("--xlog",          default=False, action="store_true",
                        help="log X scale")
    parser.add_argument("--max",           default=float('inf'), type=float,
                        help="max value       [%(default)s]")
    parser.add_argument("--min",           default=float('-inf'), type=float,
                        help="min value       [%(default)s]")
    parser.add_argument("--vMinSum",           default=float('-inf'), type=float,
                        help="min Sum of values [%(default)s]")
    parser.add_argument("--collapse",      default=False, action="store_true",
                        help="collapse into single subplot")
    parser.add_argument("--normed",        default=0, choices=(0, 1), type=int,
                        help="normalise values")
    parser.add_argument("--alpha",         default=0.75, type=float,
                        help="plot alpha      [%(default)s]")
    parser.add_argument("--colors",        nargs="+", default=['b', 'r', 'y', 'g', 'grey', 'black'],
                        help="plot alpha      [%(default)s]")    
    parser.add_argument("--legendLoc",     default=1, choices=(1, 2, 3, 4), type=int,
                        help="legend location (1=top right, 2=top left, 3=bottom left, 4=bottom right")
    parser.add_argument("--headerLines",   default=1, type=int,
                        help="number of header lines to skip [%(default)s]")
    

    o = parser.parse_args()
    if o.verbose:
        sys.stderr.write( "Options: %s\n" % str(o) )

    plot(o.input, o.output, o.col, o.names, o.bins, o.title, o.xlab, o.ylab, \
              o.xlog, o.ylog, o.max, o.min, o.vMinSum, o.collapse, o.normed, o.alpha, o.legendLoc, \
              o.colors, o.headerLines, o.verbose)
              
if __name__=='__main__': 
    t0  = datetime.now()
    main()
    dt  = datetime.now()-t0
    sys.stderr.write( "#Time elapsed: %s\n" % dt )
