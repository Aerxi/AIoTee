from flask import Flask, render_template, jsonify, request,Response
import pandas as pd
import numpy
import time
from sklearn.preprocessing import StandardScaler
from sklearn_extensions.extreme_learning_machines.elm import GenELMClassifier
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import classification_report
import argparse
import sys
import json
import pickle
import gevent
import gevent.monkey
from gevent.pywsgi import WSGIServer

from datetime import datetime

from IOTAssignmentUtilitiesdorachua.MySQLManager import MySQLManager
from twilio.rest import Client
import telepot

import boto3
from boto3.dynamodb.conditions import Key, Attr

import jsonconverter as jsonc


app = Flask(__name__)
oldSpeed = -1

def get_data_from_dynamodb():
    try:
        import boto3
        from boto3.dynamodb.conditions import Key, Attr

        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('carInfo')

        print("Fetching data from DynamoDB")

        response = table.scan()
        # Pulls all data from DDB

        items=response['Items']
        # print ()
        # print (items[-1])
        # print ()

        return items

    except:
        import sys
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])

@app.route("/api/getdata",methods=['GET', 'POST'])
def apidata_getdata():
    if request.method == 'POST' or request.method == 'GET':
        try:
            global timevalues
            global oldSpeed
            global client
            my_bot_token = '1222581641:AAERMoml2QxBI_pYyLmmV2fdrm059rKSDps'
            bot = telepot.Bot(my_bot_token)
            limit = 1000
            bookingid = "ALL"
        
            if 'bookingid' in request.form:        
                bookingid = request.form['bookingid']
            if 'datalimit' in request.form:
                limit = request.form['datalimit']

            loaded_r = json.loads(jsonc.data_to_json(get_data_from_dynamodb()))

            loadedDict = loaded_r[-1]
            bookingid = float(loadedDict.get('bookingid'))
            accuracy = float(loadedDict.get('accuracy'))
            bearing = float(loadedDict.get('bearing'))
            acceleration_x = float(loadedDict.get('acceleration_x'))
            acceleration_y = float(loadedDict.get('acceleration_y'))
            acceleration_z = float(loadedDict.get('acceleration_z'))
            gyro_x = float(loadedDict.get('gyro_x'))
            gyro_y = float(loadedDict.get('gyro_y'))
            gyro_z = float(loadedDict.get('gyro_z'))
            seconds = float(loadedDict.get('seconds'))
            speed = float(loadedDict.get('speed'))
            testingBookingID=[[bookingid,accuracy,bearing,acceleration_x,acceleration_y,acceleration_z,gyro_x,gyro_y,gyro_z,seconds,speed]]
            
            loaded_model = pickle.load(open('iotModel', 'rb'))
            df = pd.DataFrame(testingBookingID, columns = ['bookingid', 'accuracy', 'bearing', 'acceleration_x', 'acceleration_y', 'acceleration_z', 'gyro_x', 'gyro_y', 'gyro_z', 'seconds', 'speed']) 

            predictedSafety = loaded_model.predict(df)
            safetyValue = predictedSafety.item(0)

            # dataSpeed = loaded_r["data"][-1]["speedkmhour"]
            # dataBookingid = loaded_r["data"][-1]["bookingid"]
            if safetyValue==1:
                returnStr = "You are going at %.3f for BookingID %s. Please slow down" %(speed,bookingid)
                print("Message has been sent!")
                bot.sendMessage(324643817, returnStr) 


            if safetyValue==1:
                print("A bit fast there buddy")
                print(safetyValue)

            

            data = {'chart_data': loaded_r, 
             'title': "IOT Data"}
             
            return data

        except:

            import sys
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])
  
#---------------------------------------------------------------------------------
        # u='root';pw='rootr00t!';h='localhost';db='iotdatabase'
        # mysqlm = MySQLManager(u,pw,h,db)
        # mysqlm.connect()

        # sql=f"SELECT MAX(datetimestart_value) FROM iotapp"
        # datasql = {}            
        # list_data = mysqlm.fetch_fromdb_as_list(sql,datasql)

        # if len(list_data)>0:
        #     max_datetimestart_value = list_data[0]['MAX(datetimestart_value)']

        #     if bookingid == "ALL":
        #         sql=f"SELECT distinct * FROM iotapp WHERE datetimestart_value=%(datetimestart_value)s ORDER BY datetime_value DESC"
        #         datasql = {"datetimestart_value": max_datetimestart_value}
        #         print(bookingid)
        #     else:                
        #         sql=f"SELECT * FROM iotapp WHERE bookingid=%(bookingid)s AND datetimestart_value=%(datetimestart_value)s ORDER BY datetime_value DESC"
        #         datasql = {"bookingid": bookingid, "datetimestart_value": max_datetimestart_value}
        #         print(bookingid)
        # else:
        #     if bookingid == "ALL":
        #         sql=f"SELECT * FROM iotapp ORDER BY datetime_value DESC LIMIT {limit}"
        #         datasql = {}
        #         print(bookingid)
        #         print("pp")
        #     else:                
        #         sql=f"SELECT * FROM iotapp WHERE bookingid=%(bookingid)s ORDER BY datetime_value DESC"
        #         datasql = {"bookingid": bookingid}
        #         print(bookingid)
                
#         json_data = mysqlm.fetch_fromdb_as_json(sql,datasql)
#         loaded_r = json.loads(json_data)
# #____________________________________________________________________________________
#         dataSpeed = loaded_r["data"][-1]["speedkmhour"]
#         dataBookingid = loaded_r["data"][-1]["bookingid"]
#         if dataSpeed != oldSpeed:
#             if dataSpeed > 70:
#                 oldSpeed = dataSpeed
#                 diffSpeed = dataSpeed - 70
#                 returnStr = "You are going at %.3f for BookingID %s. Please slow down by %.3f!" %(dataSpeed,dataBookingid,diffSpeed)
#                 print("Message has been sent!")
#                 bot.sendMessage(324643817, returnStr)               
# #____________________________________________________________________________________

#         data = {'chart_data': loaded_r, 'title': "IOT Data", 'chart_data_length': len(json_data)}

#         mysqlm.disconnect()
        
#         return jsonify(data)

        
        
    # except:
    #     print(sys.exc_info()[0])
    #     print(sys.exc_info()[1])


@app.route("/multiple")
def multiple():
    return render_template('index_multiple.html')

@app.route("/")
def home():
    return render_template('index.html')

if __name__ == '__main__':
   try:
        host = '0.0.0.0'
        port = 80
        parser = argparse.ArgumentParser()        
        parser.add_argument('port',type=int)

        args = parser.parse_args()
        if args.port:
            port = args.port
                
        http_server = WSGIServer((host, port), app)
        app.debug = True
        print('Web server waiting for requests')
        http_server.serve_forever()

   except:
        print("Exception while running web server")
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])
