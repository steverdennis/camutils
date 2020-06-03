#!/usr/bin/env python2

import zlib
import sys
import subprocess
import argparse
import re
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
    print("SAM not set up. Try eg `. /cvmfs/dune.opensciencegrid.org/products/dune/setup_dune.sh ; setup sam_web_client`")
    exit()
  samout,samerr = sam_proc.communicate()
  if samerr.strip() == "File '%s' not found"%filename:
    print("File not found on SAM: %s"%filename)
    return STATUS_NOT_FOUND_ON_SAM
  elif samerr.strip():
    print("Unexpected error:\n%s"%samerr)
    return STATUS_UNKNOWN_ERROR
  
  adler_checksum_lines = [l for l in samout.split() if "adler32" in l]
  if len(adler_checksum_lines)==0:
    print("Failed to get adler32 checksum for %s"%f)
    return STATUS_SAM_PARSE_FAILED
  
  pattern = "(?<=adler32:)[0-9a-f]*"
  match = re.search(pattern,adler_checksum_lines[0])
  if not match:
    print("Failed to match %s to %s"%(pattern,adler_checksum_lines[0]))
    return STATUS_SAM_PARSE_FAILED
    
  adler32_checksum_from_sam = match.group()
  
  try:
    with open(path) as handle:
      hash_as_signed_int = zlib.adler32(handle.read())
      hash_as_pos_int = hash_as_signed_int & 0xffffffff
      adler32_checksum_for_my_file = "%08x"%(hash_as_pos_int)
  except IOError:
    print("Failed to find local file ",path)
  
  if adler32_checksum_from_sam != adler32_checksum_for_my_file:
    print("Hash doesn't match for file %s, SAM hash is %s, local is %s"%(path,adler32_checksum_from_sam,adler32_checksum_for_my_file))
    return STATUS_HASH_FAILED
    
  return STATUS_GOOD

# Write command line arguments here
files = sys.argv[1:]

pool = multiprocessing.Pool()
retvals = pool.map(test_file,files)

n_checked = len(retvals)
n_good             = retvals.count(STATUS_GOOD)
n_not_found_on_sam = retvals.count(STATUS_NOT_FOUND_ON_SAM)
n_hash_failed      = retvals.count(STATUS_HASH_FAILED)

n_other_errors = n_checked - n_good - n_not_found_on_sam - n_hash_failed

print("Checked %d files"%len(retvals))
print("%d files not found on SAM (%.2f%%)"%(n_not_found_on_sam,100.*n_not_found_on_sam/n_checked))
print("%d files hash failed (%.2f%%)     "%(n_hash_failed,     100.*n_hash_failed/n_checked))
if (n_other_errors):
  print("%d files with other errors (%.2f%%)"%(n_other_errors,100.*n_other_errors/n_checked))
  
