import argparse
import os

parser = argparse.ArgumentParser(description='WiFi scanner')
parser.add_argument('ni', type=str, help='network interface name, use `sudo ifconfig -a` to check')
parser.add_argument('--ssid', type=str, default="*", nargs="+", help='network ssid to scan, default * to scan all')
parser.add_argument('--min', type=float, default=-65, help='min signal quality in dBm for scanning')
parser.add_argument('--filename', type=str, default="fingerprint.txt", help='fingerprint file')
parser.add_argument('--N', type=int, default=16, help='Max number of APs in the fingerprint')
parser.add_argument('--M', type=int, default=10, help='Number of measurements to avg per location')
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

def fprintf(aps, f, ap_list = []):
    f.write("%s " % args.loc)
    if len(ap_list) == 0:
        for v in aps:
            f.write("%f " % (v[1]['SignalLevel']))
    else:
        for ap in ap_list:
            for num, ap_ref in enumerate(aps):
                if ap_ref[0] == ap:
                    break
            if num < len(aps):
                f.write("%f " % (aps[num][1]['SignalLevel']))
            else:
                f.write("%s " % 'N/A')
    f.write("\n")

def fprintfheaders(aps, f):
    for v in aps:
        f.write("%s " % v[0])
    f.write("\n")

def fread_aplist(f):
    aplist = f.readlines()[0].split(' ')[:-1]
    return aplist

def merge_aps(aps_cum, aps_this):
    aps = aps_cum
    for k, v in aps_this.items():
        if k in aps:
            aps[k]['Counter'] = aps[k]['Counter'] + 1
            aps[k]['SignalLevel'] = aps[k]['SignalLevel'] + v
        else:
            aps[k] = v
            aps[k]['Counter'] = 1
    return aps

if __name__ == "__main__":
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
    if not os.path.isfile(args.filename):
        f = open(args.filename, 'a')
        fprintfheaders(sorted_aps, f)
        ap_list = []
    else:
        f = open(args.filename, 'r')
        ap_list = fread_aplist(f)
        f.close()
        f = open(args.filename, 'a')
    fprintf(sorted_aps, f, ap_list)
    f.close()
