#!/usr/bin/env python2
"""
Parses SNPs against reference.
-compare with reference (optionally)
Not finished!
"""

import os, sys
import commands
from optparse import OptionParser
from datetime import datetime
from genome_annotation import load_gtf,load_gff,genome2dict,coding_snp_info # bin/python_modules

#from bam2snps.ref import get_alt_allele,_remove_indels
def _remove_indels( alts ):
    """
    Remove indels from mpileup.
    .$....,,,,....,.,,..,,.,.,,,,,,,....,.,...,.,.,....,,,........,.A.,...,,......^0.^+.^$.^0.^8.^F.^].^],
    ........,.-25ATCTGGTGGTTGGGATGTTGCCGCT..
    """
    #remove indels info
    for symbol in ('-','+'):
        baseNo = 0
        while symbol in alts:
            i=alts.index(symbol)
      
            j = 1
            digits=[]
            while alts[i+j].isdigit():
                digits.append( alts[i+j] )
                j += 1
      
            if digits:
                baseNo=int( ''.join(digits) )
        
            alts=alts[:i]+alts[i+baseNo+len(digits)+1:] #......+1A..,
      
    return alts

def get_alt_allele( base_ref,cov,alg,minFreq,alphabet,bothStrands ):
    """Return alternative allele only if different than ref and freq >= minFreq.
    """
    #remove deletions
    alts = alg
    dels = alts.count('*') 
    #remove insertions
    alts = _remove_indels( alts )
    #get base counts
    baseCounts = [ ( alts.upper().count(base),base ) for base in alphabet ]
    #get base frequencies
    for base_count,base in sorted(baseCounts):
        freq = base_count*1.0/cov
        if base!=base_ref and freq >= minFreq:
            #check if alt base in both strands
            if bothStrands: 
                if not base.upper() in alts or not base.lower() in alts:
                    return
            return (base,freq) # base!=base_ref and 
#END
            
def load_vcf( fnames,indels=True ):
    """Return sorted list of coordinates with possible SNPs."""
    coords = set()
    #iter files
    for fn in fnames:
        #iter lines
        for l in open( fn ):
            l = l.strip()
            #skip line if empty or commented
            if not l or l.startswith("#"):
                continue
            #read info
            contig,pos,ID,ref,alt,qual,flt,info = l.split("\t")[:8]
            #skip indels if not requested
            if not indels and info.startswith("INDEL"):
                continue
            coords.add( (contig,int(pos)) )
    #return sorted list of coordinates
    return sorted( coords )

def process_alt( ref,alt,contig,pos,contig2position,gene2position,contig2fasta,l ):
    """
    """
    outline = ""

    genes = filter( lambda x: x[0]<pos+1<x[1], contig2position[contig] )
    if genes:
        for start,stop,feature,geneid in genes:
            # check effect of mutations
            if len(ref)!=len(alt): # indel
                if feature == 'gene':
                    contig,CDSs,strand,function = gene2position[geneid] # get exons
                    cds = filter( lambda x: x[0]<pos+1<x[1],CDSs ) # check if overlaping with indel
                    if cds and len(ref)%3 != len(alt)%3:
                        outline += "%s\texonic\t%s\tframe-shift\t\t\t\t\t\t%s\n" % ( l,geneid,function )
                    else:
                        outline += "%s\tintronic\t%s\t\t\t\t\t\t%s\n" % ( l,geneid,function )
                else:
                    outline += "%s\tintergenic\n" % l
            elif feature == 'gene':
                contig,CDSs,strand,function = gene2position[geneid]
                outline += "%s\t%s\t%s\n" % ( l,coding_snp_info( contig2fasta[contig],geneid,CDSs,strand,alt,pos ),function )
            else:
                outline += "%s\t%s\n" % ( l,feature )
    else:
        outline += "%s\tintergenic\n" % ( l, )
    
    return outline

def mpileup( bam1,bam2,fastaFn,contig,pos,minDepth,minFreq,bothStrands,alphabet='ACGT' ):
    """Return filtered mpileup output"""
    cmd = "samtools mpileup -f %s %s %s -r '%s:%s-%s'" % ( fastaFn,bam2,bam1,contig,pos,pos )
    lines = commands.getoutput(cmd)
    line      = lines.split('\n')[-1].strip()
    lineTuple = line.split('\t')
    if len(lineTuple)<6:
        sys.stderr.write("Cannot parse line: %s\n"%lineTuple)
        return
    #get coordinate
    refCov = refFreq = ''
    contig,pos,baseRef = lineTuple[:3]
    #samplesData = lineTuple[3:]
    #laod ref data
    #if reference:
    refCov,refAlgs,refQuals = lineTuple[3:6]
    refCov = int(refCov)
    samplesData = lineTuple[6:]
    if refCov<minDepth:
        return
    alt_allele = get_alt_allele( '',refCov,refAlgs,minFreq,alphabet,bothStrands )
    if not alt_allele:
        return
    baseRef,refFreq = alt_allele

    #,cov,alg,quals= #; contig,pos,base,cov,alg,quals
    for cov,alg,quals in zip( samplesData[0::3],samplesData[1::3],samplesData[2::3] ):
        #print lineTuple
        cov=int(cov)
        if cov<minDepth:
            continue
        # check for SNP
        alt_allele = get_alt_allele( baseRef,cov,alg,minFreq,alphabet,bothStrands )
        if not alt_allele:
            continue
        # get base and freq
        base,freq = alt_allele
        yield baseRef,base

def check_snps( coords,bam1,bam2,fastaFn,outfn,contig2position,gene2position,contig2fasta,minDepth,minFreq,indels,bothStrains=True ):
    """
    """
    # select output
    if outfn:    # write to file, if specified
        out1 = open( outfn,'w')
    else:           # write to stdout
        out1 = sys.stdout

    # parse vcf
    snpsCount = indelsCount = 0
    header="coordinate\tref\talt\tSNP type\tgene\tAA type\tAA position\tposition in codon\tref codon\tref AA\talt codon\talt AA\n"
    out1.write( header )
    for contig,pos in coords:
        sys.stderr.write(" %s\r"%contig)
        # count
        for dtuple in mpileup( bam1,bam2,fastaFn,contig,pos,minDepth,minFreq,bothStrains ):
            if not dtuple:
                continue
            ref,alts = dtuple
            if len(alt)==len(ref):
                snpsCount   += 1
            elif indels: 
                indelsCount += 1
            else:        #skip if indel and not requested
                continue
                
            # check if in gene
            if not contig in contig2position:
                sys.stderr.write("Warining: Contig %s is not present in GTF!\n" % contig )
                continue
                
            l = "%s:%s\t%s\t%s" % ( contig,pos,ref,alt )
            outline = process_alts( ref,alts,contig,pos,contig2position,gene2position,contig2fasta,l )
            out1.write( outline ) 

    sys.stderr.write( "SNPs:\t%s\nINDELs:\t%s\n" % ( snpsCount,indelsCount ) )

def main():
    
    usage = "usage: %prog [options] *.vcf" 
    parser = OptionParser( usage=usage,version="%prog 1.0" ) # allow_interspersed_args=True

    parser.add_option("-g", dest="gtf",
                      help="genome annotation gtf/gff [requires -f]" )
    parser.add_option("-f", dest="fasta",
                      help="genome fasta" )
    parser.add_option("-1", dest="bam1",
                      help="sample bam")
    parser.add_option("-2", dest="bam2",
                      help="reference bam")
    parser.add_option("-o", dest="outfn",
                      help="output fname [stdout]")
    parser.add_option("-d", dest="minDepth", default=5,  type=int,
                      help="""minimal depth; note both samples need to have pass depth filtering [%default]""")
    parser.add_option("-m", dest="minFreq",  default=0.8, type=float,
                      help="min frequency of alternative base [%default]")
    parser.add_option("-n", dest="indels",   default=True, action="store_false", 
                      help="ignore indels [%default]")
    parser.add_option("-b", dest="bothStrands", default=True, action="store_false", 
                      help="report events confirmed by single strand algs")
    parser.add_option("-v", dest="verbose",  default=True, action="store_false")
    
    ( o, args ) = parser.parse_args()
    if o.verbose:
        sys.stderr.write( "%s\n" % ( str(o), ) )

    if not args:
        parser.error( "At least one vcf file has to be specified!" )

    for fn in args:
        if not os.path.isfile( fn ):
            parser.error( "No such file: %s" % fn )

    ctg2cds,id2gene,ctg2seq = {},{},{}
    if o.gtf: # if annotation
        # load genome
        if not o.fasta: # fasta has to be provided
            parser.errer( "Fasta file (-f) is requeired!" )
        elif not os.path.isfile( o.fasta ):
            parser.error( "No such file: %s" % o.fasta )
        ctg2seq        = genome2dict( o.fasta )

        # load genome annotation
        if not os.path.isfile( o.gtf ): # check if correct file
            parser.error( "No such file: %s" % o.gtf )
        # load gtf/gff
        if o.gtf.endswith(".gff"):
            id2gene,ctg2cds = load_gff( o.gtf )
        else:
            id2gene,ctg2cds = load_gtf( o.gtf )
        if o.verbose:
            sys.stderr.write( "Loaded annotation of %s CDS from %s\n" % ( len(id2gene),o.gtf ) )

    # load possible SNPs coordinates
    coords = load_vcf( args,o.indels )
            
    # check with mpileup
    check_snps( coords,o.bam1,o.bam2,o.fasta,o.outfn,ctg2cds,id2gene,ctg2seq,o.minDepth,o.minFreq,o.indels,o.bothStrands )

if __name__=='__main__': 
  t0=datetime.now()
  main()
  dt=datetime.now()-t0
  sys.stderr.write( "#Time elapsed: %s\n" % dt )
