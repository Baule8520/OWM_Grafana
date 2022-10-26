#!/usr/bin/env python3

from influxdb import InfluxDBClient
import requests, json, datetime, socket, configparser, time

config = configparser.ConfigParser()
config.read_file(open('./token.config', mode='r'))
influxhost = config.get('config', 'host')
influxusername = config.get('config', 'user')
influxpassword = config.get('config', 'password')
monitoringdbname = config.get('config', 'dbname')

useragent='Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20100101 Firefox/10.0'
latitude=47.853252632085535
longitude=12.343682085867298
url='https://api.met.no/weatherapi/locationforecast/2.0/.json?lat={latitude}&lon={longitude}'.format(latitude=latitude,longitude=longitude)

monitoringhost=socket.getfqdn()
client = InfluxDBClient(host=influxhost, port=8086, username=influxusername, password=influxpassword)
databases = client.get_list_database()
databaseAlreadyThere =False

for item in databases:
    if item['name'] == monitoringdbname:
        databaseAlreadyThere = True

if databaseAlreadyThere == False:
    client.create_database(monitoringdbname)

client.switch_database(monitoringdbname)

headers = {
    'User-Agent': useragent
}

def data():
    response = requests.get(url, headers=headers)
    data = json.loads(response.content.decode('utf-8'))
    timeseries=data['properties']['timeseries']
    lon=data['geometry']['coordinates'][0]
    lat=data['geometry']['coordinates'][1]
    height=str(float(data['geometry']['coordinates'][2])*0.3048)
    json_bodies=[]
    for timeserie in timeseries:
        stats = {}
        data=timeserie['data']['instant']['details']
        for x in data:
            if isinstance(data[x],dict)==False:
                stats[x] = data[x]
        if 'next_1_hours' in timeserie['data'].keys():
            stats['precipitation_amount']=timeserie['data']['next_1_hours']['details']['precipitation_amount']
        json_body = []
        jb={}
        jb["measurement"]="WeatherForecast"
        tags={}
        tags["Server"]=monitoringhost
        tags["Longitude"]=lon
        tags["Latitude"]=lat
        tags["Height"]=height
        tags["Location"]="Prien"
        jb["tags"]=tags
        jb["time"]=timeserie['time']
        jb["fields"]=stats
        json_body.append(jb)
        client.write_points(json_body)

if __name__ == '__main__':
    while True:
        data()
        time.sleep(3600)