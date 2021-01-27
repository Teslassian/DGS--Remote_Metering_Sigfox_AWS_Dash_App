#!/usr/local/bin/python3

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
import boto3

from datetime import datetime, timedelta
from decimal import Decimal
from pprint import pprint

import pandas as pd
import numpy as np
import random
import math

import json
import time
import sys
import csv
import os

import pdb

#----------------------------------------------------------------------------------------------------------------------#
def create_sigfox_table_AWS(dynamodb=None):
    if not dynamodb:
        if online:
            dynamodb = boto3.resource('dynamodb',region_name='us-east-1')
        else:
            dynamodb = boto3.resource('dynamodb',endpoint_url="http://localhost:8000")

    table = dynamodb.create_table(
        TableName=tableName,
        KeySchema=[
            {
                'AttributeName': 'deviceId',
                'KeyType': 'HASH' # Partition Key
            },
            {
                'AttributeName': 'timestamp',
                'KeyType': 'RANGE' # Sort Key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'deviceId',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'timestamp',
                'AttributeType': 'N'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        },
        StreamSpecification={
            'StreamEnabled': True,
            'StreamViewType': 'NEW_AND_OLD_IMAGES'
        }
    )
    return table

def delete_sigfox_table_AWS(dynamodb=None):
    if not dynamodb:
        if online:
            dynamodb = boto3.resource('dynamodb',region_name='us-east-1')
        else:
            dynamodb = boto3.resource('dynamodb',endpoint_url="http://localhost:8000")

    table = dynamodb.Table(tableName)
    table.delete()

def put_item_AWS(deviceId, timestamp, data, temperature, humidity, dynamodb=None):
    if not dynamodb:
        if online:
            dynamodb = boto3.resource('dynamodb',region_name='us-east-1')
        else:
            dynamodb = boto3.resource('dynamodb',endpoint_url="http://localhost:8000")

    table = dynamodb.Table(tableName)
    response = table.put_item(
        Item={
            'deviceId': deviceId,
            'timestamp': timestamp,
            'payload': {
                'data': data,
                'temperature': temperature,
                'humidity' : humidity,
            }
        }
    )
    return response

#----------------------------------------------------------------------------------------------------------------------#
def now():
    return round(datetime.timestamp(datetime.now()))

def populate_table(num_init_items):
    deviceId = '12CAC94'
    for x in range(num_init_items):
        timestamp = now() + x - num_init_items
        data = round(50*math.sin(0.1*x) * math.cos(x) + 50)
        temperature = round(random.randint(40, 80))
        humidity = round(np.random.normal(60, 20))
        item_resp = put_item_AWS(deviceId, timestamp, data, temperature, humidity)
    print("New table created.")
    print('Added ' + str(num_init_items) + ' items.')

#----------------------------------------------------------------------------------------------------------------------#
config_dict = {}
with open('config.txt', mode='r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        config_dict[row['setting']] = row['value']
    csv_file.close()

tableName = str(config_dict['tableName'])
num_init_items = int(config_dict['numInitItems'])
online = int(config_dict['online'])

# Check if a previous table exists, delete it if so
prev_table_exists = 1
try:
    delete_sigfox_table_AWS()
    print("Deleting previous table...")
except:
    print("No previous tables exist.")

# Wait for table to finish deleting, create a new one if done
while prev_table_exists:
    try:
        sigfox_table = create_sigfox_table_AWS()
        print("Creating a new sigfox table")
        prev_table_exists = 0
    except Exception as e:
        # print(e)
        print("Previous table status: DELETING" )
        time.sleep(1)

# Wait for the table to finish creating, populate it if done
table_created = 0
while not table_created:
    try:
        populate_table(num_init_items)
        table_created = 1
    except Exception as e:
        # print(e)
        try:
            print("New table status: " + str(sigfox_table.table_status))
        except:
            print("New table status: INITIALIZING")
    time.sleep(1)


os.system("python3 demo.py")