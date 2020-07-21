#!/usr/bin/env python2

# Should support py3
from __future__ import print_function

import zlib
import sys
import subprocess
import argparse
import re
import os
import multiprocessing

STATUS_GOOD = 0
STATUS_NOT_FOUND_ON_SAM = 1
STATUS_NOT_FOUND_LOCAL  = 2
STATUS_HASH_FAILED      = 3
STATUS_SAM_PARSE_FAILED = 4
STATUS_UNKNOWN_ERROR    = 5

def test_file(path):
  filename = path.split("/")[-1]

  try:
    sam_proc = subprocess.Popen(["samweb","get-metadata",filename],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  except OSError: # FileNotFoundError in python3
    print("SAM not set up. Try eg `. /cvmfs/dune.opensciencegrid.org/products/dune/setup_dune.sh ; setup sam_web_client`",file=sys.stderr)
    exit()
  samout,samerr = sam_proc.communicate()
  if samerr.strip() == "File '%s' not found"%filename:
    print("File not found on SAM: %s"%filename,file=sys.stderr)
    return STATUS_NOT_FOUND_ON_SAM
  elif samerr.strip():
    print("Unexpected error:\n%s"%samerr,file=sys.stderr)
    return path,STATUS_UNKNOWN_ERROR
  
  adler_checksum_lines = [l for l in samout.split() if "adler32" in l]
  if len(adler_checksum_lines)==0:
    print("Failed to get adler32 checksum for %s"%f,file=sys.stderr)
    return path,STATUS_SAM_PARSE_FAILED
  
  pattern = "(?<=adler32:)[0-9a-f]*"
  match = re.search(pattern,adler_checksum_lines[0])
  if not match:
    print("Failed to match %s to %s"%(pattern,adler_checksum_lines[0]),file=sys.stderr)
    return path,STATUS_SAM_PARSE_FAILED
    
  adler32_checksum_from_sam = match.group()
  
  try:
    with open(path) as handle:
      hash_as_signed_int = zlib.adler32(handle.read())
      hash_as_pos_int = hash_as_signed_int & 0xffffffff
      adler32_checksum_for_my_file = "%08x"%(hash_as_pos_int)
  except IOError:
    print("Failed to find local file ",path,file=sys.stderr)
  
  if adler32_checksum_from_sam != adler32_checksum_for_my_file:
    print("Hash doesn't match for file %s, SAM hash is %s, local is %s"%(path,adler32_checksum_from_sam,adler32_checksum_for_my_file),file=sys.stderr)
    return path,STATUS_HASH_FAILED
    
  return path,STATUS_GOOD

# Write command line arguments here
parser = argparse.ArgumentParser()
parser.add_argument("--list-good",dest="list_good",action="store_true",help="Instead of normal output, write a list of good filenames")
parser.add_argument("--delete-failed",dest="delete_failed",action="store_true",help="Delete failed files")
parser.add_argument("files",nargs='*',help="Files to read")

args = parser.parse_args()
  
pool = multiprocessing.Pool()
  
retvals = dict(pool.map(test_file,args.files))

n_checked = len(retvals)
n_good             = retvals.values().count(STATUS_GOOD)
n_not_found_on_sam = retvals.values().count(STATUS_NOT_FOUND_ON_SAM)
n_hash_failed      = retvals.values().count(STATUS_HASH_FAILED)

n_other_errors = n_checked - n_good - n_not_found_on_sam - n_hash_failed

if (not args.list_good) :
  print("Checked %d files"%len(retvals))
  print("%d files not found on SAM (%.2f%%)"%(n_not_found_on_sam,100.*n_not_found_on_sam/n_checked))
  print("%d files hash failed (%.2f%%)     "%(n_hash_failed,     100.*n_hash_failed/n_checked))
  if (n_other_errors):
    print("%d files with other errors (%.2f%%)"%(n_other_errors,100.*n_other_errors/n_checked))
else:
  for path,status in retvals.items():
    if status==STATUS_GOOD: print(path)

if(args.delete_failed):
  for path,status in retvals.items():
    if status==STATUS_HASH_FAILED:
      os.remove(path)
