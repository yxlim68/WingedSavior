
import datetime
import json
from flask import Blueprint, request

from controller.db import db

# maximum amount of time to to consider using the location as the current location
MAX_LOCATION_LIFE = 10000 # ms

current_location = None

location_bp = Blueprint("Location Routes", __name__)

_, cur = db()


@location_bp.route("/location", methods=["POST", "GET"])
def location():
    global current_location
    
    if request.method == "GET":
        return handle_get_location()
    
    
    data = request.json
    current_location = data
    update_location(current_location)
    print(data)
    
    return {}, 200
    
    
def update_location(location):
    
    query = "UPDATE location SET location = %s"
    
    cur.execute(query, (json.dumps(location),))
    cur.execute('commit')
    
    
def handle_get_location():
    global current_location
    
    if not current_location:
        return {}, 400
    return current_location, 200


def get_location():
    _, cur = db()
    
    query = "SELECT location, time from location"

    cur.execute(query)
    
    res = cur.fetchone()
    
    if not res:
        return None
    
    current_time = datetime.datetime.now()
    
    loc_time = res['time']
    
    time_diff = (current_time - loc_time).total_seconds() * 1000
    
    if time_diff > MAX_LOCATION_LIFE:
        return None
    
    return res['location']