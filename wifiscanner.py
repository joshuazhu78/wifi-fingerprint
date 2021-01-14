import argparse
import os
import numpy as np
import time

parser = argparse.ArgumentParser(description='WiFi scanner')
parser.add_argument('ni', type=str, help='network interface name, use `sudo ifconfig -a` to check')
parser.add_argument('--ssid', type=str, default="*", nargs="+", help='network ssid to scan, default * to scan all')
parser.add_argument('--min', type=float, default=-65, help='min signal quality in dBm for scanning')
parser.add_argument('--fpfilename', type=str, default="fingerprint.txt", help='fingerprint file')
parser.add_argument('--apfilename', type=str, default="aplist.txt", help='ap list file')
parser.add_argument('--N', type=int, default=16, help='Max number of APs in the fingerprint')
parser.add_argument('--M', type=int, default=20, help='Number of measurements to avg per location')
parser.add_argument('--threshold', type=float, default=0.75, help='threshold to record one AP into fingerprint')
parser.add_argument('--loc', type=str, default="8W022", help='fingerprint file')

args = parser.parse_args()

def parse_scan_results(results):
    ll = results.split("\n")
    aps = {}
    in_cell = False
    for l in ll:
        words = l.strip().split(" ")
        if words[0] == "Cell":
            address = words[-1]
            aps[address] = {}
            in_cell = True
        elif words[0].split(":")[0] == 'Channel' and in_cell:
            channel = int(words[0].split(":")[1])
            aps[address]['Channel'] = channel
        elif words[-1] == 'dBm' and in_cell:
            signal_level = float(words[-2].split('=')[1])
            aps[address]['SignalLevel'] = signal_level
            if signal_level < args.min:
                del aps[address]
                in_cell = False
        elif words[0].split(":")[0] == 'ESSID' and in_cell:
            ESSID = words[0].split(":")[1].strip()[1:-1]
            aps[address]['ESSID'] = ESSID
            if ESSID not in args.ssid:
                del aps[address]
                in_cell = False
        elif words[0].split(":")[0] == 'Frequency' and in_cell:
            frequency_GHz = float(words[0].split(":")[1].split(' ')[0])
            aps[address]['Frequency'] = frequency_GHz

    return aps

def fprintf(aps, f, f_fp, ap_list):
    f_fp.write("%s " % args.loc)
    for ap_ref in aps:
        if ap_ref[0] not in ap_list:
            num_ap = len(ap_list)
            ap_list[ap_ref[0]] = num_ap
            f.write("%s %d\n" % (ap_ref[0], num_ap))
        ap_idx = ap_list[ap_ref[0]]
        f_fp.write("%d %f %f " % (ap_idx, ap_ref[1]['SignalLevel'], ap_ref[1]['SignalStd']))
    f_fp.write("\n")

def fprintaps(aps, f):
    ap_list = {}
    for i, v in enumerate(aps):
        f.write("%s %d\n" % (v[0], i))
        ap_list[v[0]] = i
    return ap_list

def fread_aplist(f):
    ap_list = {}
    for line in f.readlines():
        words = line.split(' ')
        ap_list[words[0]] = int(words[1])
    return ap_list

def merge_aps(aps_cum, aps_this):
    aps = aps_cum
    for k, v in aps_this.items():
        if k in aps:
            aps[k]['Samples'].append(v['SignalLevel'])
        else:
            aps[k] = v
            aps[k]['Samples'] = [v['SignalLevel']]
    return aps

if __name__ == "__main__":
    aps_orig = {}
    for m in range(args.M):
        results = os.popen("sudo iwlist " + args.ni + " scanning").read()
        print("\rScan %d/%d" % (m+1, args.M), end='')
        time.sleep(0.1)
        aps_this = parse_scan_results(results)
        aps_orig = merge_aps(aps_orig, aps_this)

    aps = {}
    for k, v in aps_orig.items():
        if len(v['Samples']) >= args.M * args.threshold:
            aps[k] = v
    for k, v in aps.items():
        v['SignalLevel'] = np.mean(v['Samples'])
        v['SignalStd'] = np.std(v['Samples'])

    sorted_aps = sorted(aps.items(), key=lambda item: item[1]['SignalLevel'], reverse=True)
    if len(sorted_aps) > args.N:
        sorted_aps = sorted_aps[0:args.N]
    if not os.path.isfile(args.apfilename):
        f = open(args.apfilename, 'a')
        ap_list = fprintaps(sorted_aps, f)
    else:
        f = open(args.apfilename, 'r')
        ap_list = fread_aplist(f)
        f.close()
        f = open(args.apfilename, 'a')
    f_fp = open(args.fpfilename, 'a')
    fprintf(sorted_aps, f, f_fp, ap_list)
    f.close()
    f_fp.close()
