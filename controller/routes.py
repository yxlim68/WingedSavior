import base64
import json
from io import BytesIO
from flask import Blueprint, Response, jsonify, request, Flask, send_file

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