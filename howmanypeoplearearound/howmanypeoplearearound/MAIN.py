import threading
import sys
import os
import platform
import subprocess
import json
import time

import netifaces
import click

import urllib, urllib2, time
from datetime import datetime

from howmanypeoplearearound.oui import oui
from howmanypeoplearearound.analysis import analyze_file
if os.name != 'nt':
    from pick import pick

import json
#from azure.servicebus import ServiceBusService

'''
def azure_Stream(i):
    #Endpoint=sb://sbrouter.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=a9hK/IQM3HqaPRuKmPZHR7fKbP7CptIbOI5uoBlPjzU=
    #Endpoint=sb://router.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=/K3VX0LsIe+s/3D8jO0n2sA4hwRJe9fDDU9sxDl32C4=
    sbs = ServiceBusService(service_namespace="router",
    shared_access_key_name="RootManageSharedAccessKey",
    shared_access_key_value="/K3VX0LsIe+s/3D8jO0n2sA4hwRJe9fDDU9sxDl32C4=")
# build dictionary and send value
    temp = {'#_people': str(i)}
    sbs.send_event('router_countpeople', json.dumps(temp))
'''
#import Adafruit_DHT as dht

# type of sensor that we're using
#SENSOR = dht.DHT22

# pin which reads the temperature and humidity from sensor
#PIN = 4

# REST API endpoint, given to you when you create an API streaming dataset
# Will be of the format: https://api.powerbi.com/beta/<tenant id>/datasets/< dataset id>/rows?key=<key id>


# Gather temperature and sensor data and push to Power BI REST API
#https://powerbi.microsoft.com/en-us/blog/using-power-bi-real-time-dashboards-to-display-iot-sensor-data-a-step-by-step-tutorial/
def PowerBI(count):
    REST_API_URL = "https://api.powerbi.com/beta/84c31ca0-ac3b-4eae-ad11-519d80233e6f/datasets/1d1076fd-305a-4e7c-94ce-c5508d28178d/rows?key=X6JNiTH9lLbx70rsfiygQCMxKiv3BkBGx1H9dlQfgUNotiuIdxHnMYr9HU3Tl1uH27k3INjF64%2FZX8AryH05ww%3D%3D"
    try:
        now = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S%Z")
	# data that we're sending to Power BI REST API
        data = '[{{"Time" : "{0}", "Number_of_people" : "{1}"}}]'.format(now, count)
        req = urllib2.Request(REST_API_URL, data)
        response = urllib2.urlopen(req)
        print("POST request to Power BI with data:{0}".format(data))
        print("Response: HTTP {0} {1}\n".format(response.getcode(), response.read()))
        time.sleep(15)
    except urllib2.HTTPError as e:
        print("HTTP Error: {0} - {1}".format(e.code, e.reason))
    except urllib2.URLError as e:
        print("URL Error: {0}".format(e.reason))
    except Exception as e:
        print("General Exception: {0}".format(e))

def which(program):
    """Determines whether program exists
    """
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    raise


def showTimer(timeleft):
    """Shows a countdown timer"""
    total = int(timeleft) * 10
    for i in range(total):
        sys.stdout.write('\r')
        # the exact output you're looking for:
        timeleft_string = '%ds left' % int((total - i + 1) / 10)
        if (total - i + 1) > 600:
            timeleft_string = '%dmin %ds left' % (
                int((total - i + 1) / 600), int((total - i + 1) / 10 % 60))
        sys.stdout.write("[%-50s] %d%% %15s" %
                         ('=' * int(50.5 * i / total), 101 * i / total, timeleft_string))
        sys.stdout.flush()
        time.sleep(0.1)
    print("")


@click.command()
@click.option('-a', '--adapter', default='en0', help='adapter to use')
@click.option('-z', '--analyze', default='', help='analyze file')
@click.option('-s', '--scantime', default='40', help='time in seconds to scan')
@click.option('-o', '--out', default='', help='output cellphone data to file')
@click.option('-v', '--verbose', help='verbose mode', is_flag=True)
@click.option('--number', help='just print the number', is_flag=True)
@click.option('-j', '--jsonprint', help='print JSON of cellphone data', is_flag=True)
@click.option('-n', '--nearby', help='only quantify signals that are nearby (rssi > -70)', is_flag=True)
@click.option('--allmacaddresses', help='do not check MAC addresses against the OUI database to only recognize known cellphone manufacturers', is_flag=True)  # noqa
@click.option('--nocorrection', help='do not apply correction', is_flag=True)
@click.option('--loop', default=True, help='loop forever', is_flag=True)
@click.option('--port', default=8001, help='port to use when serving analysis')
@click.option('--sort', help='sort cellphone data by distance (rssi)', is_flag=True)
def run(adapter, scantime, verbose, number, nearby, jsonprint, out, allmacaddresses, nocorrection, loop, analyze, port, sort):
    if analyze != '':
        analyze_file(analyze, port)
        return
    if loop:
        while True:
            scan(adapter, scantime, verbose, number,nearby, jsonprint, out, allmacaddresses, nocorrection, loop, sort)

    else:
        scan(adapter, scantime, verbose, number,
             nearby, jsonprint, out, allmacaddresses, nocorrection, loop, sort)


def scan(adapter, scantime, verbose, number, nearby, jsonprint, out, allmacaddresses, nocorrection, loop, sort):
    """Monitor wifi signals to count the number of people around you"""

    # print("OS: " + os.name)
    # print("Platform: " + platform.system())

    try:
        tshark = which("tshark")
    except:
        if platform.system() != 'Darwin':
            print('tshark not found, install using\n\napt-get install tshark\n')
        else:
            print('wireshark not found, install using: \n\tbrew install wireshark')
            print(
                'you may also need to execute: \n\tbrew cask install wireshark-chmodbpf')
        return
    if jsonprint:
        number = True
    if number:
        verbose = False

    if len(adapter) == 0:
        if os.name == 'nt':
            print('You must specify the adapter with   -a ADAPTER')
            print('Choose from the following: ' +
                  ', '.join(netifaces.interfaces()))
            return
        title = 'Please choose the adapter you want to use: '
        adapter, index = pick(netifaces.interfaces(), title)

    print("Using %s adapter and scanning for %s seconds..." %
          (adapter, scantime))

    if not number:
        # Start timer
        t1 = threading.Thread(target=showTimer, args=(scantime,))
        t1.daemon = True
        t1.start()

    # Scan with tshark
    command = [tshark, '-I', '-i', adapter, '-a',
               'duration:' + scantime, '-w', '/tmp/tshark-temp']
    if verbose:
        print(' '.join(command))
    run_tshark = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, nothing = run_tshark.communicate()
    if not number:
        t1.join()

    # Read tshark output
    command = [
        tshark, '-r',
        '/tmp/tshark-temp', '-T',
        'fields', '-e',
        'wlan.sa', '-e',
        'wlan.bssid', '-e',
        'radiotap.dbm_antsignal'
    ]
    if verbose:
        print(' '.join(command))
    run_tshark = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, nothing = run_tshark.communicate()
    foundMacs = {}
    for line in output.decode('utf-8').split('\n'):
        if verbose:
            print(line)
        if line.strip() == '':
            continue
        mac = line.split()[0].strip().split(',')[0]
        dats = line.split()
        if len(dats) == 3:
            if ':' not in dats[0] or len(dats) != 3:
                continue
            if mac not in foundMacs:
                foundMacs[mac] = []
            dats_2_split = dats[2].split(',')
            if len(dats_2_split) > 1:
                rssi = float(dats_2_split[0]) / 2 + float(dats_2_split[1]) / 2
            else:
                rssi = float(dats_2_split[0])
            foundMacs[mac].append(rssi)

    if not foundMacs:
        print("Found no signals, are you sure %s supports monitor mode?" % adapter)
        return

    for key, value in foundMacs.items():
        foundMacs[key] = float(sum(value)) / float(len(value))

    cellphone = [
        'Motorola Mobility LLC, a Lenovo Company',
        'GUANGDONG OPPO MOBILE TELECOMMUNICATIONS CORP.,LTD',
        'Huawei Symantec Technologies Co.,Ltd.',
        'Microsoft',
        'HTC Corporation',
        'Samsung Electronics Co.,Ltd',
        'SAMSUNG ELECTRO-MECHANICS(THAILAND)',
        'BlackBerry RTS',
        'LG ELECTRONICS INC',
        'Apple, Inc.',
        'LG Electronics',
        'OnePlus Tech (Shenzhen) Ltd',
        'Xiaomi Communications Co Ltd',
        'LG Electronics (Mobile Communications)']

    cellphone_people = []
    for mac in foundMacs:
        oui_id = 'Not in OUI'
        if mac[:8] in oui:
            oui_id = oui[mac[:8]]
        if verbose:
            print(mac, oui_id, oui_id in cellphone)
        if allmacaddresses or oui_id in cellphone:
            if not nearby or (nearby and foundMacs[mac] > -70):
                cellphone_people.append(
                    {'company': oui_id, 'rssi': foundMacs[mac], 'mac': mac})
    if sort:
        cellphone_people.sort(key=lambda x: x['rssi'], reverse=True)
    if verbose:
        print(json.dumps(cellphone_people, indent=2))

    # US / Canada: https://twitter.com/conradhackett/status/701798230619590656
    percentage_of_people_with_phones = 0.7
    if nocorrection:
        percentage_of_people_with_phones = 1
    num_people = int(round(len(cellphone_people) /
                           percentage_of_people_with_phones))
    if num_people<100:
        PowerBI(num_people)
        print("PowerBI passes")
    else:
        print("too large to be true")
    if number and not jsonprint:
        print(num_people)
    elif jsonprint:
        print(json.dumps(cellphone_people, indent=2))
    else:
        if num_people == 0:
            print("No one around (not even you!).")
        elif num_people == 1:
            print("No one around, but you.")
            #return 1
        else:
            print("There are about %d people around." % num_people)
            #return num_people

    if out:
        with open(out, 'a') as f:
            data_dump = {'cellphones': cellphone_people, 'time': time.time()}
            f.write(json.dumps(data_dump) + "\n")
        if verbose:
            print("Wrote %d records to %s" % (len(cellphone_people), out))
    os.remove('/tmp/tshark-temp')


if __name__ == '__main__':
    run()
    # oui = {}
    # with open('data/oui.txt','r') as f:
    #     for line in f:
    #         if '(hex)' in line:
    #             data = line.split('(hex)')
    #             key = data[0].replace('-',':').lower().strip()
    #             company = data[1].strip()
    #             oui[key] = company
    # with open('oui.json','w') as f:
    #     f.write(json.dumps(oui,indent=2))
