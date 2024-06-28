import base64
import json
from flask import Response, jsonify, request, Flask
from flask_cors import CORS
import mysql.connector as connector

DEBUG_WEB = True

def log(msg):
    print('[web] ' + msg)

if DEBUG_WEB:
    app = Flask(__name__)
else:
    from drone.state import app

CORS(app)

def init_app():
    app.run(host="0.0.0.0", port=8766)
    
def db():
    try:
        conn = connector.connect(
            host="localhost",
            database="drone",
            user="root",
            password=""
        )
        
        cursor = conn.cursor(dictionary=True)
        
        return (conn, cursor)
    except connector.Error as e:
        log(f'Error while connecting to database: {e}')
        raise e
        

@app.route("/register", methods=['POST'])
def register():
    if request.method != 'POST':
        return Response(status=405)
    
    try:
        data = request.json
        print(data)
        
        _, cursor = db()
        
        query = f"INSERT INTO users(email, username, password) VALUES('{data['email']}', '{data['username']}','{data['password']}')"
        
        cursor.execute(query)
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
    
    

@app.route('/login', methods=['POST'])
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
            }, 200
        
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


@app.route('/create_project', methods=['POST'])
def create_project():
    if request.method != 'POST':
        return Response('',status=405)
    
    data = request.json
    
    # TODO: add validation
    
    (_, cursor) = db()
    query = f"insert into project(name, coordinate, detect) values ({data['name']},{data['coordinate']},{data['detection']})"
    cursor.execute(query)
    project_id = cursor.lastrowid
    
    cursor.execute('commit')
    
    
    return jsonify({
        "message": "Success",
        "project_id": project_id
    })


@app.route('/get_snapshot')
def get_snapshot():
    
    print(request.args)
    snapshot_id = request.args.get("id")
    
    (_, cursor) = db()

    query = f"SELECT * FROM img WHERE SSID = {snapshot_id}"
    cursor.execute(query)
    result = cursor.fetchone()

    ssb64 = base64.b64encode(result['SS'])
    
    result['SS'] = ssb64.decode('utf-8')
    result['Time'] = result['Time'].strftime('%d/%m/%Y')
    
    encoded = json.dumps(result)
    
    return jsonify(encoded)

if __name__ == "__main__":
    init_app()
