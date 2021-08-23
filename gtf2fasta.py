#!/usr/bin/env python2
###
# UNFINISHED!!!
#
###

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.Alphabet import IUPAC
import os, sys
from datetime import datetime
from optparse import OptionParser

def _get_fasta_dict( fPath ):
  """Return dictionary of entries from fasta file"""
  fasta_dict = {}
  for r in SeqIO.parse(open(fPath),'fasta'):
    fasta_dict[ r.id ]=Seq(str(r.seq),IUPAC.ambiguous_dna)#r.seq
    #except: print r.seq
  return fasta_dict

def process_gene( contigSeq,geneId,gene_data,files,verbose,seqLengthLimit=60 ):
  #geneId
  fastas={};shortSeq=0
  for type in files: 
    if type=='gene':
      if 'start_codon' not in gene_data.keys() or 'stop_codon' not in gene_data.keys():
        print "Missing gene boundaries in: %s %s" % (geneId, str(gene_data.keys()))
        return
      SCstart,SCend,score,  strand,frame,comments=gene_data['start_codon'][0] 
      ECstart,ECend,score,ECstrand,frame,comments=gene_data['stop_codon'][0] #start,end,score,strand,frame,comments
      #check strand consistency at start & stop
      if strand != ECstrand:
        print "Warning: Different strands at start end stop codons @ %s!" % geneId, gene_data
      #define gene boundaries
      if strand=='+': start,end = SCstart,ECend
      else:           start,end = SCend,ECstart
      seq=get_seq(contigSeq,start,end,score,strand)
      if not str(seq):
        if verbose: print "%s\tERROR! No %s! Seq: %s" % ( geneId,type,seq )
        return 
      fasta='>%s\n%s\n' % ( geneId,seq )
    #CDS
    elif type=='CDS':
      if not 'CDS' in gene_data: 
        if verbose: print "\tError: No CDS."
        return
      cds_dict={}; trascriptsNo=0; commentsList=[]
      for cds_data in gene_data['CDS']:
        start,end,score,strand,frame,comments=cds_data
        if comments in commentsList:
          if strand=='-': cds_dict[trascriptsNo]=[ get_seq(contigSeq,start,end,score,strand)+cds_dict[trascriptsNo][0], int(frame) ] #add seq and update frame
          else: cds_dict[trascriptsNo][0]+=get_seq(contigSeq,start,end,score,strand) #add seq
        else: 
          commentsList.append(comments)
          trascriptsNo+=1
          cds_dict[trascriptsNo]=[get_seq(contigSeq,start,end,score,strand),int(frame)]
      
      fasta=aaFasta=''
      for trascriptsNo in cds_dict:
        seq,frame=cds_dict[trascriptsNo]
        if not seq:
          if verbose: print "%s\tERROR! No %s!" % ( geneId,type )
          return 
        elif len(seq)<seqLengthLimit: 
          if verbose: print "\tWarning! Short seq in %s." % type
          shortSeq=1
        fasta+='>%s|%s.t%s\n%s\n' % ( geneId,geneId,trascriptsNo,seq )
        aaSeq=seq[frame:].translate(table=12,to_stop=False,)#,cds=True)
        aaFasta+='>%s|%s.t%s\n%s\n' % ( geneId,geneId,trascriptsNo,aaSeq )
        ##
        if verbose:
          aa_august='%s' % gene_data['pep_augustus'][trascriptsNo-1]
          aa_gff='%s' % aaSeq.data
          #if '*' in aaSeq.data or len(aaSeq.data)!=len(aa_august):#
          if aa_august!=aa_gff or len(aaSeq.data)!=len(aa_august):
            print '%s %s/%s %s\n%s%s\t' % (geneId,trascriptsNo,len(cds_dict),gene_data['CDS'],strand,frame), seq[frame:], '\n%s\t' %len(aaSeq) ,
            for aa in aaSeq: print '%s ' % aa,
            print '\n%s\t' % len(aa_august),
            for aa in aa_august: print '%s ' % aa,
            print
      ###
      fastas['pep']=aaFasta

    fastas[type]=fasta
    
  for type in files: 
    files[type].write( fastas[type] )
    #if type=='cds':
    #  print 
  #return trascriptsNo,shortSeq

def get_seq( contig,start,end,score,strand ):
  start,end=int(start),int(end)
  contigSeq=str(contig).replace('\n','')

  seq=contigSeq[start-1:end]
  seq=Seq(seq,IUPAC.ambiguous_dna)
  if strand=='-': seq=seq.reverse_complement()
  return seq

def process_gtf( gtfPath,contigsPath,entireGene=True,verbose=True,seqTypes=( 'gene','cds','mrna','pep' ) ):
  #preparation
  name2contigSeq=_get_fasta_dict( contigsPath )

  #open files for writting
  files={}; 
  for type in seqTypes: 
    outFname='%s.%s.fa' % ( gtfPath,type )
    files[type]=open( outFname,'w' )
  
  #parse gtf and save sequences
  gene_data={}; GeneId=None
  i=genes=trascriptsNo=shortSeq=0
  for line in open(gtfPath):    #print r.mContig,r.mSource,r.mFeature,r.mFrame,r.mStart,r.mEnd,r.mScore,r.mStrand,r.mGeneId,r.mTranscriptId,r.mAttributes
    line=line.strip() #Contig_1.1  CPAR1_CUSTOMGENE_1  start_codon  1008  1010  .  -  0  gene_id "CPAG_00001"; transcript_id "CPAG_00001.1";
    contig,source,feature,start,end,score,strand,frame,comments=line.split('\t')
    #print contig,source,feature,start,stop,dot,strand,frame,comments
    curGeneId=comments.split('"')[1]
    if GeneId and curGeneId!=GeneId:
      data=process_gene( name2contigSeq[contig],GeneId,gene_data,files,verbose )
      if data: 
        _trascriptsNo,_shortSeq=data
        genes+=1
        trascriptsNo+=_trascriptsNo
        shortSeq+=_shortSeq
        
      i+=1#; print i, r.mGeneId, r.mContig
      dataTuple=( start,end,score,strand,frame,comments )
      GeneId=curGeneId
      gene_data={ feature: [ dataTuple ] }
    else:
      dataTuple=( start,end,score,strand,frame,comments )
      try:    gene_data[feature].append( dataTuple )
      except: gene_data[feature]=[ dataTuple ]
      GeneId=curGeneId
    #print gene_data
    
  print GeneId
  data=process_gene( name2contigSeq[contig],GeneId,gene_data,files,verbose )
  if data: 
    _trascriptsNo,_shortSeq=data
    genes+=1
    trascriptsNo+=_trascriptsNo
    shortSeq+=_shortSeq
  i+=1#; print i, r.mGeneId, r.mContig
      
  for type in files: 
    files[type].close()
    
  print "%s %s %s %s" % ( i,genes,trascriptsNo,shortSeq )

def main():
  usage = "differential_expression.py [options] gene_exp.diff [ gene_exp2.diff ... ] > ctr/diff_expr_sds3oh.4_10.txt"
  parser = OptionParser( usage ) 
  
  parser.add_option("-v", dest="verbose", default=0, type=str,
                    help="verbosity [default: %default]" )
  parser.add_option("-i", dest="fasta", default=None, type=str,
                    help="define fasta file [default: %default]" )             
  parser.add_option("-a", dest="gtf", default=None, type=str,
                    help="define annotation file [default: %default]" )
  parser.add_option("-e", dest="entireGene", default=False, type=str,
                    help="store only complete genes [default: %default]" )
                    
  ( o, args )   = parser.parse_args()
  print o
  
  #error checking
  if not o.gtf or not o.fasta:
    sys.exit( "You have to specify GTF and FASTA file." )
    
  if not os.path.isfile( o.gtf ):
    sys.exit( "No such file: %s" % o.gtf )
    
  if not os.path.isfile( o.fasta ):
    sys.exit( "No such file: %s" % o.fasta )
  
  process_gtf( o.gtf,o.fasta,o.entireGene,o.verbose ); 

if __name__=='__main__': 
  t0=datetime.now()
  main()
  dt=datetime.now()-t0
  sys.stderr.write( "#Time elapsed: %s\n" % dt )

