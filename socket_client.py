from time import sleep
import sys
import json
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

from datetime import datetime  
from datetime import timedelta  
import argparse

from IOTAssignmentClientdorachua.GrabCarClient import GrabCarClient
from IOTAssignmentUtilitiesdorachua.MySQLManager import MySQLManager
from IOTAssignmentUtilitiesdorachua.MySQLManager import QUERYTYPE_DELETE, QUERYTYPE_INSERT

# Custom MQTT message callback
def customCallback(client, userdata, message):
	print("Received a new message: ")
	print(message.payload)
	print("from topic: ")
	print(message.topic)
	print("--------------\n\n")

def getData(gcc,sqlm,datetime_start,my_rpi):    
    while True:
        try:
            reading = gcc.get_reading()            

            if reading is not None and len(reading)>0:
                readings = json.loads(reading)
                            
                for str_reading in readings:
                    r = json.loads(str_reading)
                    
                    if sqlm.isconnected:

                        #print("Inserting data ...")
                        sql = "INSERT INTO iotapp (bookingid,bookingidwithtime,datetimestart_value,seconds,speed,speedkmhour,datetime_value) VALUES (%(bookingid)s,%(bookingidwithtime)s,%(datetimestart_value)s,%(seconds)s,%(speed)s,%(speedkmhour)s,%(datetime_value)s)"
                        bid = r["bookingid"]                                                
                        seconds = r["seconds"]
                        speed = r["speed"]
                        speedkmhour = r["speedkmhour"]
                        accuracy = r["accuracy"]
                        bearing = r["bearing"]
                        acceleration_x = r["acceleration_x"]
                        acceleration_y = r["acceleration_y"]
                        acceleration_z = r["acceleration_z"]
                        gyro_x = r["gyro_x"]
                        gyro_y = r["gyro_y"]
                        gyro_z = r["gyro_z"]
                        datetime_value = datetime_start + timedelta(seconds=seconds)
                        datetimestart_value = str(datetime_start)
                        bidwithtime = f"{bid}_{datetimestart_value}"
                        #print(f"bid,seconds,speed,speedkmhour,datetime_value {bid} {seconds} {speed} {speedkmhour} {datetime_value}")
                        data = {'bookingid': bid , 'bookingidwithtime':bidwithtime,'datetimestart_value':datetimestart_value,'accuracy': accuracy,"bearing": bearing,'acceleration_x': acceleration_x,'acceleration_y': acceleration_y,'acceleration_z': acceleration_z,'gyro_x': gyro_x,'gyro_y': gyro_y,'gyro_z': gyro_z,'seconds': seconds,'speed': speed,'speedkmhour': speedkmhour, 'datetime_value':datetime_value, 'assignment':'1'} 
                        success = mysqlm.insertupdatedelete(QUERYTYPE_INSERT,sql,data)
                        my_rpi.publish("carInfo", json.dumps(data,default=str), 1)
                        if success:
                            print(f"{data} inserted")

                    else:
                        print("Not connected to database")

                    
            yield             

        except GeneratorExit:
            print("Generator Exit error")
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])
            return

        except KeyboardInterrupt:
            exit(0)

        except:
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])       


if __name__ == "__main__":

    host = "azmpvf5osq5pb-ats.iot.us-east-1.amazonaws.com"
    rootCAPath = "rootca.pem"
    certificatePath = "certificate.perm.crt"
    privateKeyPath = "private.pem.key"

    my_rpi = AWSIoTMQTTClient("IOT_CA2_MQTT")
    my_rpi.configureEndpoint(host, 8883)
    my_rpi.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

    my_rpi.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
    my_rpi.configureDrainingFrequency(2)  # Draining: 2 Hz
    my_rpi.configureConnectDisconnectTimeout(10)  # 10 sec
    my_rpi.configureMQTTOperationTimeout(5)  # 5 sec

    # Connect and subscribe to AWS IoT
    my_rpi.connect()
    my_rpi.subscribe("carInfo", 1, customCallback)
    sleep(2)
    
    #message = {}
    #message["deviceid"] = "KennethdevID"    
    #message["value"] = "test"
    #my_rpi.publish("carInfo", json.dumps(message), 1)
    
    try:                 
        host,port = "127.0.0.1", 8889
        parser = argparse.ArgumentParser()
        parser.add_argument('host')
        parser.add_argument('port',type=int)
        
        args = parser.parse_args()
        if args.host:
            host = args.host
        if args.port:
            port = args.port

        mygcc = GrabCarClient(host,port)

        u='iotuser';pw='iotpassword';h='localhost';db='iotdatabase'

        mysqlm =  MySQLManager(u,pw,h,db)
        mysqlm.connect()

        #print("Truncating records from database first...")
        #mysqlm.insertupdatedelete(QUERYTYPE_DELETE, "DELETE FROM iotapp",{})

        print("Streaming started")        
        datetime_start = datetime.now()
        gen = getData(mygcc,mysqlm,datetime_start,my_rpi)

        while True:
            next(gen)
            sleep(2)
        
    except KeyboardInterrupt:
        print('Interrupted')
        mysqlm.disconnect()
        sys.exit()


    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])       




