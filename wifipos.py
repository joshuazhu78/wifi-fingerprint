import argparse
import os
from wifiscanner import *
import numpy as np

parser = argparse.ArgumentParser(description='WiFi positioning')
parser.add_argument('ni', type=str, help='network interface name, use `sudo ifconfig -a` to check')
parser.add_argument('--ssid', type=str, default="*", nargs="+", help='network ssid to scan, default * to scan all')
parser.add_argument('--min', type=float, default=-80, help='min signal quality in dBm for scanning')
parser.add_argument('--fpfilename', type=str, default="fingerprint.txt", help='fingerprint file')
parser.add_argument('--apfilename', type=str, default="aplist.txt", help='ap list file')

args = parser.parse_args()

def fprintpos(aps, ap_list, ap_idx, fp_mean, fp_std):
    sorted_ap_list = sorted(ap_list.items(), key=lambda item: item[1])
    s = {}
    for k, m in fp_mean.items():
        ap_idx_this = ap_idx[k]
        s[k] = {}
        s[k]['Distance'] = []
        s[k]['Nosignal'] = 0
        for i, idx in enumerate(ap_idx_this):
            ap_name = sorted_ap_list[idx][0]
            if ap_name in aps:
                d = (aps[ap_name]['SignalLevel'] - m[i])/fp_std[k][i]
                s[k]['Distance'].append(d * d)
            else:
                s[k]['Nosignal'] = s[k]['Nosignal'] + 1
    s_final = {}
    for k, v in s.items():
        if len(v['Distance']) > 0:
            s_final[k] = s[k]

    for k, v in s_final.items():
        v['Mean'] = (np.sum(v['Distance']) + v['Nosignal'] * np.max(v['Distance']))/(len(v['Distance']) + v['Nosignal'])

    sort_ap = sorted(s_final.items(), key=lambda item: item[1]['Mean'])
    return sort_ap

def freadfingerprint(f):
    aplist = f.readlines()
    fp_mean = {}
    fp_std = {}
    ap_idx = {}
    for idx, ap in enumerate(aplist):
        words = ap.split(' ')[:-1]
        loc = words[0]
        for num, word in enumerate(words):
            if num == 0:
                fp_mean[loc] = []
                fp_std[loc] = []
                ap_idx[loc] = []
            elif num%3 == 1:
                ap_idx[loc].append(int(word))
            elif num%3 == 2:
                fp_mean[loc].append(float(word))
            else:
                fp_std[loc].append(float(word))

    return ap_idx, fp_mean, fp_std

if __name__ == "__main__":
    if not os.path.isfile(args.apfilename):
        print("%s does not exists" % args.apfilename)
        exit()
    if not os.path.isfile(args.fpfilename):
        print("%s does not exists" % args.fpfilename)
        exit()
    f = open(args.apfilename, 'r')
    ap_list = fread_aplist(f)
    f.close()
    f = open(args.fpfilename, 'r')
    ap_idx, fp_mean, fp_std = freadfingerprint(f)
    f.close()
    results = os.popen("sudo iwlist " + args.ni + " scanning").read()
    aps = parse_scan_results(results)
    sort_ap = fprintpos(aps, ap_list, ap_idx, fp_mean, fp_std)
    for v in sort_ap:
        print("%s %f" % (v[0], v[1]['Mean']))
