import argparse
import os
from wifiscanner import *
import numpy as np

parser = argparse.ArgumentParser(description='WiFi positioning')
parser.add_argument('ni', type=str, help='network interface name, use `sudo ifconfig -a` to check')
parser.add_argument('--ssid', type=str, default="*", nargs="+", help='network ssid to scan, default * to scan all')
parser.add_argument('--min', type=float, default=-80, help='min signal quality in dBm for scanning')
parser.add_argument('--filename', type=str, default="fingerprint.txt", help='fingerprint file')

args = parser.parse_args()

def fprintpos(aps, ap_list, fp_mean, fp_std):
    v = []
    valid = []
    idx = 0
    for ap in ap_list:
        if ap in aps:
            v.append(aps[ap]['SignalLevel'])
            valid.append(idx)
        else:
            v.append(args.min)
        idx = idx + 1
    for k, m in fp_mean.items():
        v_ = [v[i] for i in valid]
        m_ = [m[i] for i in valid]
        s_ = [fp_std[k][i] for i in valid]
        print("%s, %f" % (k, np.linalg.norm(np.divide(np.subtract(v_, m_), s_))))

def freadfingerprint(f):
    aplist = f.readlines()
    fp_mean = {}
    fp_std = {}
    for idx, ap in enumerate(aplist):
        if idx == 0:
            continue
        words = ap.split(' ')[:-1]
        loc = words[0]
        for num, word in enumerate(words):
            if num == 0:
                fp_mean[loc] = []
                fp_std[loc] = []
            elif num%2 == 1:
                fp_mean[loc].append(float(word))
            else:
                fp_std[loc].append(float(word))

    return fp_mean, fp_std

if __name__ == "__main__":
    if not os.path.isfile(args.filename):
        print("%s does not exists" % args.filename)
        exit()
    f = open(args.filename, 'r')
    ap_list = fread_aplist(f)
    f.close()
    f = open(args.filename, 'r')
    fp_mean, fp_std = freadfingerprint(f)
    f.close()
    results = os.popen("sudo iwlist " + args.ni + " scanning").read()
    aps = parse_scan_results(results)
    fprintpos(aps, ap_list, fp_mean, fp_std)
