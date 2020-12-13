import argparse
import os

parser = argparse.ArgumentParser(description='WiFi scanner')
parser.add_argument('ni', type=str, help='network interface name, use `sudo ifconfig -a` to check')

args = parser.parse_args()

def parse_scan_results(results):
    ll = results.split("\n")
    aps = {}
    for l in ll:
        words = l.strip().split(" ")
        if words[0] == "Cell":
            address = words[-1]
            aps[address] = {}
        elif words[0].split(":")[0] == "Channel":
            channel = int(words[0].split(":")[1])
            aps[address][channel] = {}
        elif words[-1] == "dBm":
            signal_level = float(words[-2].split('=')[1])
            aps[address][channel]["SignalLevel"] = signal_level

    return aps

if __name__ == "__main__":
    results = os.popen("sudo iwlist " + args.ni + " scanning").read()
    aps = parse_scan_results(results)
    print(aps)
