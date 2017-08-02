import urllib, urllib2, time
from datetime import datetime
#import Adafruit_DHT as dht

# type of sensor that we're using
#SENSOR = dht.DHT22

# pin which reads the temperature and humidity from sensor
#PIN = 4

# REST API endpoint, given to you when you create an API streaming dataset
# Will be of the format: https://api.powerbi.com/beta/<tenant id>/datasets/< dataset id>/rows?key=<key id>
REST_API_URL = "https://api.powerbi.com/beta/84c31ca0-ac3b-4eae-ad11-519d80233e6f/datasets/1d1076fd-305a-4e7c-94ce-c5508d28178d/rows?key=X6JNiTH9lLbx70rsfiygQCMxKiv3BkBGx1H9dlQfgUNotiuIdxHnMYr9HU3Tl1uH27k3INjF64%2FZX8AryH05ww%3D%3D"

# Gather temperature and sensor data and push to Power BI REST API

while True:
	try:
		# read and print out humidity and temperature from sensor
		#humidity,temp = dht.read_retry(SENSOR, PIN)
		#print 'Temp={0:0.1f}*C Humidity={1:0.1f}%'.format(temp, humidity)
		# ensure that timestamp string is formatted properly
		now = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S%Z")
        count = MAIN.run(adapter='en0', number=True, nocorrection=False, loop=True)
		# data that we're sending to Power BI REST API
		data = '[{{"Time" : "{0}", "Number_of_people" : "{1}"}}]'.format(now, count)


		# make HTTP POST request to Power BI REST API
		req = urllib2.Request(REST_API_URL, data)
		response = urllib2.urlopen(req)
		print("POST request to Power BI with data:{0}".format(data))
		print("Response: HTTP {0} {1}\n".format(response.getcode(), response.read()))

		time.sleep(1)
	except urllib2.HTTPError as e:
		print("HTTP Error: {0} - {1}".format(e.code, e.reason))
	except urllib2.URLError as e:
		print("URL Error: {0}".format(e.reason))
	except Exception as e:
		print("General Exception: {0}".format(e))
