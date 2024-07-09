import cv2
import numpy as np
from djitellopy import Tello
import time


class TelloObstacleAvoidance:
    def __init__(self, tello):
        self.tello = tello
        self.tello.connect()
        self.tello.streamon()

        # Define parameters for obstacle detection
        self.distance_threshold = 100  # Distance threshold in pixels
        self.movement_speed = 20  # Movement speed of the drone

    def get_frame(self):
        # Get the latest frame from the Tello camera
        frame = self.tello.get_frame_read().frame
        return frame

    def process_frame(self, frame):
        # Convert frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # Use Canny edge detection
        edges = cv2.Canny(blur, 50, 150)

        return edges

    def detect_obstacles(self, edges):
        # Detect contours in the edges
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Filter contours by area
        obstacles = [cnt for cnt in contours if cv2.contourArea(cnt) > 100]

        return obstacles

    def calculate_distance(self, obstacle):
        # Placeholder for distance calculation
        # This should ideally be replaced with a proper distance calculation using camera calibration data
        x, y, w, h = cv2.boundingRect(obstacle)
        distance = 1000 / w  # Simplified distance calculation: inverse of width
        return distance

    def avoid_obstacles(self, obstacles, frame):
        for obstacle in obstacles:
            # Get bounding box of obstacle
            x, y, w, h = cv2.boundingRect(obstacle)

            # Calculate the center of the obstacle
            center_x = x + w // 2
            center_y = y + h // 2

            # Calculate and print the distance of the obstacle
            distance = self.calculate_distance(obstacle)
            print(f"Detected obstacle at distance: {distance:.2f} cm")

            # Draw the bounding box and distance on the frame
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, f"{distance:.2f} cm", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Avoid the obstacle if it is within the distance threshold
            if w > self.distance_threshold or h > self.distance_threshold:
                try:
                    if center_x < 320:
                        # Obstacle on the left, move right
                        self.tello.move_right(self.movement_speed)
                    elif center_x > 320:
                        # Obstacle on the right, move left
                        self.tello.move_left(self.movement_speed)

                    if center_y < 240:
                        # Obstacle above, move down
                        self.tello.move_down(self.movement_speed)
                    elif center_y > 240:
                        # Obstacle below, move up
                        self.tello.move_up(self.movement_speed)
                except Exception as e:
                    print(f"Error moving drone: {e}")

    def run(self):
        while True:
            # Get the latest frame from the Tello camera
            frame = self.get_frame()

            # Process the frame to detect edges
            edges = self.process_frame(frame)

            # Detect obstacles based on edges
            obstacles = self.detect_obstacles(edges)

            # Avoid detected obstacles
            self.avoid_obstacles(obstacles, frame)

            # Display the frame and edges
            cv2.imshow('Tello Camera', frame)
            cv2.imshow('Edges', edges)

            # Exit on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.tello.end()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    obstacle_avoidance = TelloObstacleAvoidance()
    obstacle_avoidance.run()
