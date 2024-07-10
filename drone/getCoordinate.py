from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route('/coordinates', methods=['POST'])
def receive_coordinates():
    data = request.json
    coordinates = data.get('coordinates')
    confidence = data.get('confidence')

    # Process the received data as needed
    print(f"Received coordinates: {coordinates} with confidence: {confidence}")

    # Return a response
    return jsonify({'status': 'success', 'message': 'Coordinates received'}), 200


@app.route('/flight_time', methods=['POST'])
def receive_flight_time():
    data = request.json
    flight_time = data.get('flight_time')

    # Process the received data as needed
    print(f"Received flight time: {flight_time} seconds")

    # Return a response
    return jsonify({'status': 'success', 'message': 'Flight time received'}), 200


if __name__ == '__main__':
    app.run(debug=True)
