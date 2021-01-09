import argparse
import os
from wifiscanner import *
import numpy as np

parser = argparse.ArgumentParser(description='WiFi positioning')
parser.add_argument('ni', type=str, help='network interface name, use `sudo ifconfig -a` to check')
parser.add_argument('--ssid', type=str, default="*", nargs="+", help='network ssid to scan, default * to scan all')
parser.add_argument('--min', type=float, default=-65, help='min signal quality in dBm for scanning')
parser.add_argument('--filename', type=str, default="fingerprint.txt", help='fingerprint file')
parser.add_argument('--N', type=int, default=16, help='Max number of APs in the fingerprint')
parser.add_argument('--M', type=int, default=10, help='Number of measurements to avg per location')

args = parser.parse_args()

def fprintpos(aps, ap_list, fingerprint):
    v = []
    for ap in ap_list:
        for num, ap_ref in enumerate(aps):
            if ap_ref[0] == ap:
                break
        if num < len(aps):
            v.append(aps[num][1]['SignalLevel'])
        else:
            print('error')
            exit()
    v = v - np.mean(v)
    v = v / np.linalg.norm(v)
    for k, fp in fingerprint.items():
        print("%s, %f" % (k, np.dot(v, fp)))

def freadfingerprint(f):
    aplist = f.readlines()
    fingerprint = {}
    for idx, ap in enumerate(aplist):
        if idx == 0:
            continue
        words = ap.split(' ')[:-1]
        loc = words[0]
        for num, word in enumerate(words):
            if num == 0:
                fingerprint[loc] = []
            else:
                fingerprint[loc].append(float(word))
        fingerprint[loc] = fingerprint[loc] - np.mean(fingerprint[loc])
        fingerprint[loc] = fingerprint[loc] / np.linalg.norm(fingerprint[loc])
    
    return fingerprint

def merge_aps(aps_cum, aps_this):
    aps = aps_cum
    for k, v in aps_this.items():
        if k in aps:
            aps[k]['Counter'] = aps[k]['Counter'] + 1
            aps[k]['SignalLevel'] = aps[k]['SignalLevel'] + aps_this[k]['SignalLevel']
        else:
            aps[k] = v
            aps[k]['Counter'] = 1
    return aps

if __name__ == "__main__":
    if not os.path.isfile(args.filename):
        print("%s does not exists" % args.filename)
        exit()
    f = open(args.filename, 'r')
    ap_list = fread_aplist(f)
    f.close()
    f = open(args.filename, 'r')
    fp = freadfingerprint(f)
    f.close()
    aps = {}
    for m in range(args.M):
        results = os.popen("sudo iwlist " + args.ni + " scanning").read()
        aps_this = parse_scan_results(results)
        aps = merge_aps(aps, aps_this)
    for k, v in aps.items():
        v['SignalLevel'] = v['SignalLevel'] / v['Counter']

    sorted_aps = sorted(aps.items(), key=lambda item: item[1]['SignalLevel'], reverse=True)
    if len(sorted_aps) > args.N:
        sorted_aps = sorted_aps[0:args.N]

    fprintpos(sorted_aps, ap_list, fp)
