
from datetime import datetime,timedelta
import time
import argparse
import json
import requests
import os, codecs, encodings
import smtplib
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.blocking import BlockingScheduler

zipcode = input('What is your zipcode: ')

sendTextAlert = input('Would you like to receive text notification? Y/N ')

def main():
    
    parser = argparse.ArgumentParser(description='Check next available curbside pickup at nearby HEB locations.')

    parser.add_argument('--radius', dest='radius', type=int, default=5,
                        help='the radius to search for store availability')

    args= parser.parse_args()

    headers = {"Content-Type": "application/json;charset=UTF-8", "Accept": "application/json, text/plain, */*"}
    payload = f'{{"address":"{zipcode}","curbsideOnly":true,"radius":{args.radius},"nextAvailableTimeslot":true,"includeMedical":false}}'

    r = requests.post('https://www.heb.com/commerce-api/v1/store/locator/address', headers=headers, data=payload)

    response = r.json()

    stores = response["stores"]

    counter = 0
    storelist = []
    for store in stores:
        if store["storeNextAvailableTimeslot"]["serviceAvailable"] \
        and store["storeNextAvailableTimeslot"]["nextAvailableTimeslotDate"]:
            
            store_name = store["store"]["name"]
            address = f'{store["store"]["address1"]}, {store["store"]["city"]}, {store["store"]["state"]} {store["store"]["postalCode"]}'
            day, time = store["storeNextAvailableTimeslot"]["nextAvailableTimeslotDate"].split("T")
            timeslot, offset = time.split("-")
            timeslot = datetime.strptime(timeslot, '%H:%M:%S')
            date = datetime.strptime(day, '%Y-%m-%d')
      
            storeInfo = (f"""
                {store_name}
                {address}
                Earliest Time Slot:
                On {date.strftime('%a %B %d, %Y')}
                Between {timeslot.strftime('%H:%M:%S')}-{(timeslot + timedelta(minutes=30)).strftime('%H:%M:%S')}
                """)
            storelist.append(storeInfo)
            
        else:
            counter += 1
            if counter == len(stores):
                storeInfo = (f"No stores with available time slots found within {args.radius} miles of {zipcode}.")

                print(f"No stores with available time slots found within {args.radius} miles of {zipcode}.")
    #
    #   Optional send text message
    #

    if sendTextAlert == "Y" or sendTextAlert == "y": 
        
        send_text(storelist) 
    else:
        # If dont want to receive message, print message on terminal
        print (storelist)
    

def send_text(storelist):

    phoneNumber = input("Please type your number WithOUT dash: ")
    carrierInput = input("what is your carrier? Pls type the No.: \n" + 
                        "1. AT&T \n" +
                        "2. Sprint \n" +
                        "3. T-Mobile \n" +
                        "4. Verizon \n" +
                        "5. MetroPCS \n" +
                        "6. Boost \n" +
                        "  ")
    recipient = ''
    carrierName = ''
    if carrierInput == '1':
        carrierName = '@txt.att.net'
        recipient = phoneNumber + carrierName    
    elif carrierInput == '2':
        carrierName = '@messaging.sprintpcs.com'
        recipient = phoneNumber + carrierName
    elif carrierInput == '3':
        carrierName = '@tmomail.net'
        recipient = phoneNumber + carrierName
    elif carrierInput == '4':
        carrierName = '@vtext.com'
        recipient = phoneNumber + carrierName
    elif carrierInput == '5':
        carrierName = '@mymetropcs.com'
        recipient = phoneNumber + carrierName
    elif carrierInput == '6':
        carrierName = '@myboostmobile.com'
        recipient = phoneNumber + carrierName
    
    msg = MIMEMultipart('mixed')
    msg.set_charset("utf-8")
    
    #
    # Got a new email for this script
    # Password is gmail app generated password
    #
    username = 'testcurbsidedelivery@gmail.com'
    password = 'fyickbaqobjcwapa'
   
    storelist = "".join(storelist)
    msg_body = storelist

    msg = MIMEText(msg_body, 'plain')
    msg['Subject'] = "You got spots"
    msg['From'] = username
    msg['To'] = recipient

    print(msg_body)
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.login(username,password)
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.close()

main()

#
# This code runs the script every hour after main().
#
scheduler = BlockingScheduler()
scheduler.add_job(main, 'interval', hours=1)
scheduler.start()

