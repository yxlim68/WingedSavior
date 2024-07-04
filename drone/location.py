
import json
from flask import Blueprint, request

from controller.db import db


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

