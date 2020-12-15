import argparse
import os

parser = argparse.ArgumentParser(description='WiFi scanner')
parser.add_argument('ni', type=str, help='network interface name, use `sudo ifconfig -a` to check')
parser.add_argument('--ssid', type=str, default="*", nargs="+", help='network ssid to scan, default * to scan all')
parser.add_argument('--min', type=float, default=-65, help='min signal quality in dBm for scanning')

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

if __name__ == "__main__":
    results = os.popen("sudo iwlist " + args.ni + " scanning").read()
    aps = parse_scan_results(results)
    print(aps)
