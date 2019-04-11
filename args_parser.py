import argparse
import sys


parser = argparse.ArgumentParser(description='TBD: some description.')
parser.add_argument('-p', '--path', required=True,  help='Path to directory to scan')
parser.add_argument('-a', '--alg', choices=['sha1', 'sha256', 'sha512', 'md5'], default='sha1', help='Hashing algorithm')
parser.add_argument('-u', '--unit', choices=['kb', 'mb', 'gb', 'tb'], default='gb', help='Unit of measuring size of files')
parser.add_argument('-m', '--max', type=int,  default=sys.maxsize, help='Max files to check in directory')
parser.add_argument('-o', '--output', default='results.txt', help='Output results to txt file')
parser.add_argument('-l', '--log', default='log.txt', help='File for logging')
parser.add_argument('-q', '--quiet', action='store_true', help='Turn off console output')
parser.add_argument('-v', '--verbose', action='store_true', help='Show duplicates in console')
