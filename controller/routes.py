import base64
import json
from io import BytesIO
import cv2
from flask import Blueprint, Response, jsonify, request, Flask, send_file
import numpy as np

from controller.db import db
from controller.util import log as util_log
from drone.config import DEBUG_WEB

routes_bp = Blueprint("general routes", __name__)

log = util_log('web')

@routes_bp.route("/register", methods=['POST'])
def register1():
    if request.method != 'POST':
        return Response(status=405)
    
    try:
        data = request.json
        print(data)
        
        _, cursor = db()
        
        query = "INSERT INTO users(firstname, lastname, email, username, password, organization) VALUES(%s,%s,%s,%s,%s,%s)"
        
        cursor.execute(query, (data['firstname'], data['lastname'],data['email'],data['username'],data['password'],data['organization']))
        user_id = cursor.lastrowid
        cursor.execute("commit")
        
        # TODO: Add validation
        return {
            "message": "Success",
            "user_id": user_id
        }
        
    except Exception as e:
        log('[register] Error occured')
        print(e) 
        return jsonify({
                "message": "Error",
                "error": str(e)
            }), 400
    
    

@routes_bp.route('/login', methods=['POST'])
def login():
    if request.method != 'POST':
        return {}, 405

    try:
        data = request.json
        
        _, cursor = db()
        
        # TODO: add encryption
        query = f"SELECT * FROM users WHERE username = '{data['username']}' AND password = '{data['password']}'"
        
        cursor.execute(query)
        
        res = cursor.fetchone()
        res['profile_image'] = base64.b64encode(res['profile_image']).decode('utf-8')
        
        if not res:
            return {
                "message": "Failed"
            }, 400
        
        return {
            "message": "Success",
            "user": res
        }, 200
        
        
    except Exception as e:
        log('[login] Error occured')
        print(e) 
        return {
            "message": "Error",
            "error": str(e)
        }, 400


@routes_bp.route('/create_project', methods=['POST'])
def create_project():
    if request.method != 'POST':
        return Response('',status=405)
    
    data = request.json
    
    # TODO: add validation
    
    (_, cursor) = db()
    query = f"insert into project(name, coordinate, detect) values ('{data['name']}','{data['coordinate']}','{data['detection']}')"
    cursor.execute(query)
    project_id = cursor.lastrowid
    
    cursor.execute('commit')
    
    
    return jsonify({
        "message": "Success",
        "project_id": project_id
    })


def format_results(result):
        ssb64 = base64.b64encode(result['SS'])
    
        result['SS'] = ssb64.decode('utf-8')
        result['Time'] = result['Time'].strftime('%d/%m/%Y')
        result['location'] = result['location'].decode('utf-8') if result['location'] is not None else None
        
        return result

@routes_bp.route('/get_snapshot')
def get_snapshot():
    image_ids = request.args.get('id')
    project_id = request.args.get('project')
    
    if not image_ids and not project_id:
        return {"message": "Please provide image ids or project id"}, 400
    
    if image_ids and project_id:
        return {"message": "Provide either project id or image ids only"}, 400
    
    
    _, cur = db()
    
    if image_ids:
        try:
            # convert to array
            
            ids = json.loads(image_ids)
            
            ids = map(lambda x: str(x), ids)
            
            query_ids = "(" + ",".join(ids) + ")"
            
            if query_ids == '()':
                return [], 200
            
            
            query = f'SELECT * FROM img WHERE SSID in {query_ids}'
            cur.execute(query)
            
            results = cur.fetchall()
            
            results = map(format_results, results)
            
            
            return jsonify(list(results)), 200
            
        except json.JSONDecodeError as e:
            return jsonify(e), 400
        except Exception as e:
            return jsonify(e), 500
        
    
    # handle project id
    
    query = "SELECT * FROM img WHERE project_id = %s"
    cur.execute(query, (project_id,))
    results = list(map(format_results, cur.fetchall()))
    
    return jsonify(results), 200
    
    

@routes_bp.route('/check_project')
def check_project():
    project_id = request.args.get('project')
    if not project_id:
        return {}, 404
    
    _, cur = db()
    
    query = f"SELECT * FROM project WHERE id = '{project_id}'"
    cur.execute(query)
    res = cur.fetchone()
    if not res:
        return {}, 404
    
    return {}, 200

@routes_bp.route('/notification')
def notification():
    
    project_id = request.args.get('project')
    
    if not project_id:
        return {}, 400
    
    _, cur = db()
    
    query = "SELECT * FROM notification WHERE project_id = %s"
    
    cur.execute(query, (project_id,))
    
    results = cur.fetchall()
    
    return jsonify(results), 200

@routes_bp.route('/image/<int:img_id>.jpeg')
def get_image(img_id):
    
    if not img_id:
        return {"message": "Please provide an image"}, 400
    
    # get image from database
    print(img_id)
    try:
        query = "SELECT * FROM img WHERE SSID = %s"
        _, cur = db()
        
        cur.execute(query, (img_id,))

        res = cur.fetchone()
        
        if not res:
            return Response(status=404)
        
        image_bytes = BytesIO(res['SS'])
        
        return send_file(image_bytes, mimetype="image/jpeg")
        
    except Exception as e:
        print(e)
        return {"message": "Internal server error"}, 500
    
@routes_bp.route("/ping", methods=["GET", "POST"])
def ping():
    print(request.json)
    return {"message": "Pong"}, 200

@routes_bp.route('/project_list')
def project_list():
    try:
        
        query = "SELECT * FROM project"
        
        _, cur = db()
        
        cur.execute(query)
        
        res = cur.fetchall()
        
        return res, 200
    except Exception as e:
        print(e)
        return {"error": e}, 500
    
@routes_bp.route("/update_user", methods=["POST"])
def update_user():
    if request.method != 'POST':
        return {}, 405
    
    
    id = request.form.get('id')
    firstname = request.form.get('firstname')
    lastname = request.form.get('lastname')
    email = request.form.get('email')
    organization = request.form.get('organization')
    username = request.form.get('username')
    password = request.form.get('password')
    
    profile_pic = request.files.get('profile-pic')
    profile_bytes = profile_pic.read()
    
    log('pw', password)
    
    
    
    if len(profile_bytes) > 0:
        # thre is picture
        # update picture first
        profile_bytes = np.frombuffer(profile_bytes, np.uint8)
        image = cv2.imdecode(profile_bytes, cv2.IMREAD_COLOR)
        
        # Convert to JPEG if necessary
        if profile_pic.content_type != 'image/jpeg':
            _, jpeg_data = cv2.imencode('.jpg', image)
            jpeg_data = jpeg_data.tobytes()
        else:
            jpeg_data = profile_bytes.tobytes()
        _, cur = db()
            
        cur.execute("UPDATE users SET profile_image = %s WHERE id = %s", (jpeg_data, id))
        cur.execute("commit")
        
        
    _, cur = db()
    # update all user data
    query = f"UPDATE users SET firstname = %s, lastname = %s, email = %s, organization = %s, username = %s{', password = %s' if password is not None and len(password) > 0 else ''} WHERE id = %s"
    log(query)
    if password is not None and len(password) > 0:
        cur.execute(query, (firstname, lastname, email, organization, username, password, id))
    else:
        cur.execute(query, (firstname, lastname, email, organization, username, id))
        
    cur.execute("commit")
    
    # user data
    cur.execute("SELECT * FROM users WHERE id = %s", (id,))
    res = cur.fetchone()
    
    res = format_user(res)
        
    log(res)
    
    return res, 200

def format_user(res):
    res['profile_image'] = base64.b64encode(res['profile_image']).decode('utf-8')
    return res 