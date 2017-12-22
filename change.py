import hashlib
import hmac
import json
import os
from influxdb import InfluxDBClient
import requests
import time

API_URL = 'https://api.changelly.com'
API_KEY = os.environ['API_KEY']
API_SECRET = os.environ['API_SECRET']

def sendRequest(message):
	serialized_data = json.dumps(message)

	sign = hmac.new(API_SECRET.encode('utf-8'), serialized_data.encode('utf-8'), hashlib.sha512).hexdigest()

	headers = {'api-key': API_KEY, 'sign': sign, 'Content-type': 'application/json'}
	response = requests.post(API_URL, headers=headers, data=serialized_data)

	return response.json()

def getEstimatedRates(src, amount, dest):
	p = []
	for curr in dest:
		if (src != curr):
			p.append({"from": src, "to": curr, "amount": amount})

	message = {
		"jsonrpc": "2.0",
		"method": "getExchangeAmount",
		"params": p,
		"id": 1
	}
	r = sendRequest(message)
	return r

def getCurrencies():
	message = {
	    'jsonrpc': '2.0',
	    'id': 1,
	    'method': 'getCurrencies',
	    'params': []
	}
	r = sendRequest(message)
	return r


def sendToInflux(currency, msg):
	vals = {}
	for v in msg["result"]:
		vals[v["to"]] = float(v["result"])

	json_body = [
		{
			"measurement": "coins",
			"tags": {
				"from": currency,
			},
			"time": int(time.time()),
			"fields": vals,
		}
	]
	params = {"precision": "s"}
	client.write_points(json_body, time_precision='s')

influx_host = os.environ['INFLUXDB_HOST']
influx_port = os.environ['INFLUXDB_PORT']
influx_db = os.environ['INFLUXDB_DB']
interval = 60

print("Connecting to influxdb at {0}".format(influx_host))
client = InfluxDBClient(influx_host, influx_port, '', '', influx_db)

currencies = getCurrencies()['result']

while (1): 
	resp = getEstimatedRates('btc', 1.0, currencies)
	print(resp)
	sendToInflux('btc', resp)
	time.sleep(interval)

