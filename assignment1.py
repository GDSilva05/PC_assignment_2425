import sys
from croblink import *
from math import *
import xml.etree.ElementTree as ET
import time
import argparse

# Define constants for the grid and robot
CELLROWS = 7
CELLCOLS = 14
CELL_SIZE = 2    # Length of the cell side
ROBOT_DIAM = 1.0 # Diameter of the robot
NOISE = 0.0      # No motor noise

# Function to parse the XML map file
def parse_lab_file(file_path):
    # Load the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # Find all the rows (Row elements)
    rows = root.findall("Row")
    max_width = int(root.get("Width"))
    
    # Sort the rows based on their position (Pos) in descending order
    rows_sorted = sorted(rows, key=lambda x: int(x.get("Pos")), reverse=True)
    
    patterns = []
    
    for row in rows_sorted:
        pattern_str = row.get("Pattern")  # Read the pattern string from the row
        # Create a list of characters from the pattern string, padding with spaces if necessary
        pattern_list = list(pattern_str.ljust(max_width, ' '))
        patterns.append(pattern_list)  # Add the row to the patterns list
    
    return patterns

# Function to create a grid of cells with wall information
def build_cells(labMap):
    # Initialize the grid with no walls
    cells = [[{'top': False, 'bottom': False, 'left': False, 'right': False} for j in range(CELLCOLS)] for i in range(CELLROWS)]
    
    for i in range(CELLROWS):  # Iterate over rows
        for j in range(CELLCOLS):  # Iterate over columns
            # Check for a wall to the right
            if j <= CELLCOLS - 2:
                c = labMap[2 * i][3 * j + 2]
                cells[i][j]['right'] = c != ' '
            else:
                cells[i][j]['right'] = True  # Edge of the map is considered a wall
            
            # Check for a wall to the left
            if j >= 1:
                c = labMap[2 * i][3 * j - 1]
                cells[i][j]['left'] = c != ' '
            else:
                cells[i][j]['left'] = True  # Edge of the map is considered a wall
            
            # Check for a wall above
            if i <= CELLROWS - 2:
                wall_found = False
                for k in range(3 * j, 3 * j + 2):  # Adjusted range
                    if labMap[2 * i + 1][k] != ' ':
                        wall_found = True
                        break
                cells[i][j]['top'] = wall_found
            else:
                cells[i][j]['top'] = True  # Edge of the map is considered a wall
            
            # Check for a wall below
            if i >= 1:
                wall_found = False
                for k in range(3 * j, 3 * j + 2):  # Adjusted range
                    if labMap[2 * i - 1][k] != ' ':
                        wall_found = True
                        break
                cells[i][j]['bottom'] = wall_found
            else:
                cells[i][j]['bottom'] = True  # Edge of the map is considered a wall
    return cells

# Function to check if all directions in a cell are open (no walls)
def all_directions_open(i, j, cells):
    return not any(cells[i][j].values())

# Function to compute expected sensor measurements for each cell
def compute_expected_measures(cells):
    # Initialize D_values dictionary
    D_values = {}

    # Main loop to calculate D values for each cell and sensor
    for i in range(CELLROWS):
        for j in range(CELLCOLS):
            D = [None, None, None, None]  # D[0]: right, D[1]: top, D[2]: bottom, D[3]: left

            # Extract wall information for the current cell
            wall_right = cells[i][j]['right']
            wall_top = cells[i][j]['top']
            wall_bottom = cells[i][j]['bottom']
            wall_left = cells[i][j]['left']

            # Case 1: Immediate walls
            if wall_right:
                D[0] = 0.4
            if wall_top:
                D[1] = 0.4
            if wall_bottom:
                D[2] = 0.4
            if wall_left:
                D[3] = 0.4

            # Case 2: Walls at the edges of the map
            if j == CELLCOLS - 1:
                D[0] = 0.5
            if i == CELLROWS - 1:
                D[1] = 0.5
            if i == 0:
                D[2] = 0.5
            if j == 0:
                D[3] = 0.5

            # Case 3: Specific edges and adjacent spaces
            if D[0] is None and not wall_right:
                if (i == 0 and j + 1 < CELLCOLS and not cells[i][j + 1]['top']):
                    D[0] = 2
                if (i == CELLROWS - 1 and j + 1 < CELLCOLS and not cells[i][j + 1]['bottom']):
                    D[0] = 2
            if D[1] is None and not wall_top:
                if (j == 0 and i + 1 < CELLROWS and not cells[i + 1][j]['right']):
                    D[1] = 2
                if (j == CELLCOLS - 1 and i + 1 < CELLROWS and not cells[i + 1][j]['left']):
                    D[1] = 2
            if D[2] is None and not wall_bottom:
                if (j == 0 and i - 1 >= 0 and not cells[i - 1][j]['right']):
                    D[2] = 2
                if (j == CELLCOLS - 1 and i - 1 >= 0 and not cells[i - 1][j]['left']):
                    D[2] = 2
            if D[3] is None and not wall_left:
                if (i == 0 and j - 1 >= 0 and not cells[i][j - 1]['top']):
                    D[3] = 2
                if (i == CELLROWS - 1 and j - 1 >= 0 and not cells[i][j - 1]['bottom']):
                    D[3] = 2

            # Case 4: Space with adjacent walls
            if D[0] is None and not wall_right and j + 1 < CELLCOLS:
                if cells[i][j + 1]['top'] or cells[i][j + 1]['bottom']:
                    D[0] = 1.8
            if D[1] is None and not wall_top and i + 1 < CELLROWS:
                if cells[i + 1][j]['left'] or cells[i + 1][j]['right']:
                    D[1] = 1.8
            if D[2] is None and not wall_bottom and i - 1 >= 0:
                if cells[i - 1][j]['left'] or cells[i - 1][j]['right']:
                    D[2] = 1.8
            if D[3] is None and not wall_left and j - 1 >= 0:
                if cells[i][j - 1]['top'] or cells[i][j - 1]['bottom']:
                    D[3] = 1.8

            # Case 5: Open spaces with specific conditions (modified)
            if D[0] is None and not wall_right and j + 1 < CELLCOLS and all_directions_open(i, j + 1, cells):
                if (j + 2 < CELLCOLS and i + 1 < CELLROWS and cells[i + 1][j + 2]['left']) or \
                   (j + 2 < CELLCOLS and i - 1 >= 0 and cells[i - 1][j + 2]['left']):
                    D[0] = 2.6

            if D[1] is None and not wall_top and i + 1 < CELLROWS and all_directions_open(i + 1, j, cells):
                if (i + 2 < CELLROWS and j + 1 < CELLCOLS and cells[i + 2][j + 1]['bottom']) or \
                   (i + 2 < CELLROWS and j - 1 >= 0 and cells[i + 2][j - 1]['bottom']):
                    D[1] = 2.6

            if D[2] is None and not wall_bottom and i - 1 >= 0 and all_directions_open(i - 1, j, cells):
                if (i - 2 >= 0 and j + 1 < CELLCOLS and cells[i - 2][j + 1]['top']) or \
                   (i - 2 >= 0 and j - 1 >= 0 and cells[i - 2][j - 1]['top']):
                    D[2] = 2.6

            if D[3] is None and not wall_left and j - 1 >= 0 and all_directions_open(i, j - 1, cells):
                if (j - 2 >= 0 and i + 1 < CELLROWS and cells[i + 1][j - 2]['right']) or \
                   (j - 2 >= 0 and i - 1 >= 0 and cells[i - 1][j - 2]['right']):
                    D[3] = 2.6

            # Case 6: Sensors near edges with open paths
            if D[0] is None and not wall_right and j == CELLCOLS - 2 and j + 1 < CELLCOLS:
                if not cells[i][j + 1]['top'] and not cells[i][j + 1]['bottom']:
                    D[0] = 2.5
            if D[1] is None and not wall_top and i == CELLROWS - 2 and i + 1 < CELLROWS:
                if not cells[i + 1][j]['left'] and not cells[i + 1][j]['right']:
                    D[1] = 2.5
            if D[2] is None and not wall_bottom and i == 1 and i - 1 >= 0:
                if not cells[i - 1][j]['left'] and not cells[i - 1][j]['right']:
                    D[2] = 2.5
            if D[3] is None and not wall_left and j == 1 and j - 1 >= 0:
                if not cells[i][j - 1]['top'] and not cells[i][j - 1]['bottom']:
                    D[3] = 2.5

            # Case 7: Specific space conditions with a wall in front
            if D[0] is None and not wall_right and j + 1 < CELLCOLS:
                if not cells[i][j + 1]['top'] and not cells[i][j + 1]['bottom'] and cells[i][j + 1]['right']:
                    D[0] = 2.4
            if D[1] is None and not wall_top and i + 1 < CELLROWS:
                if not cells[i + 1][j]['left'] and not cells[i + 1][j]['right'] and cells[i + 1][j]['top']:
                    D[1] = 2.4
            if D[2] is None and not wall_bottom and i - 1 >= 0:
                if not cells[i - 1][j]['left'] and not cells[i - 1][j]['right'] and cells[i - 1][j]['bottom']:
                    D[2] = 2.4
            if D[3] is None and not wall_left and j - 1 >= 0:
                if not cells[i][j - 1]['top'] and not cells[i][j - 1]['bottom'] and cells[i][j - 1]['left']:
                    D[3] = 2.4

            # Case 8: Open spaces and walls in adjacent cells (modified)
            if D[0] is None and not wall_right and j + 1 < CELLCOLS and all_directions_open(i, j + 1, cells):
                if (j + 2 < CELLCOLS and cells[i][j + 2]['top'] and i + 1 < CELLROWS and not cells[i + 1][j + 2]['left']) or \
                   (j + 2 < CELLCOLS and cells[i][j + 2]['bottom'] and i - 1 >= 0 and not cells[i - 1][j + 2]['left']):
                    D[0] = 2.66
            if D[1] is None and not wall_top and i + 1 < CELLROWS and all_directions_open(i + 1, j, cells):
                if (i + 2 < CELLROWS and cells[i + 2][j]['left'] and j - 1 >= 0 and not cells[i + 2][j - 1]['bottom']) or \
                   (i + 2 < CELLROWS and cells[i + 2][j]['right'] and j + 1 < CELLCOLS and not cells[i + 2][j + 1]['bottom']):
                    D[1] = 2.66
            if D[2] is None and not wall_bottom and i - 1 >= 0 and all_directions_open(i - 1, j, cells):
                if (i - 2 >= 0 and cells[i - 2][j]['right'] and j + 1 < CELLCOLS and not cells[i - 2][j + 1]['top']) or \
                   (i - 2 >= 0 and cells[i - 2][j]['left'] and j - 1 >= 0 and not cells[i - 2][j - 1]['top']):
                    D[2] = 2.66
            if D[3] is None and not wall_left and j - 1 >= 0 and all_directions_open(i, j - 1, cells):
                if (j - 2 >= 0 and cells[i][j - 2]['top'] and i + 1 < CELLROWS and not cells[i + 1][j - 2]['right']) or \
                   (j - 2 >= 0 and cells[i][j - 2]['bottom'] and i - 1 >= 0 and not cells[i - 1][j - 2]['right']):
                    D[3] = 2.66

            # If D is still None, set it to 3.0 (default value)
            for k in range(4):
                if D[k] is None:
                    D[k] = 3.0

            # Save the D values for the current cell
            D_values[(i, j)] = D

    # Set the noise value
    noise = 0.1

    # Calculate the M values for each cell
    M_values = {}
    for key in D_values:
        D = D_values[key]
        M = []
        for d in D:
            # Calculate M, rounded to the first decimal place
            m_value = 1 / d + noise
            rounded_m = round(m_value, 1)
            M.append(rounded_m)
        M_values[key] = M

    return M_values

# Definition of the MyRob class (maintained as per original code)
class MyRob(CRobLinkAngs):
    def __init__(self, rob_name, rob_id, angles, host, M_values):
        CRobLinkAngs.__init__(self, rob_name, rob_id, angles, host)
        # Initialize the probability map with uniform distribution
        self.prob_map = [[1.0 / (CELLROWS * CELLCOLS)] * CELLCOLS for _ in range(CELLROWS)]
        self.state = 'stop'
        self.distance_sum = 0.0  # Sum of distances traveled
        self.out_left = 0.0      # Power applied to the left motor at time t-1 (initially stopped)
        self.out_right = 0.0     # Power applied to the right motor at time t-1 (initially stopped)
        self.M_values = M_values
        self.noise = 0.1  # Standard deviation for sensor noise
        self.file_name = "localization.out"

        # Clear the output file at the start
        with open(self.file_name, "w") as f:
            f.write("")

    def setMap(self, labMap):
        self.labMap = labMap

    def printMap(self):
        for l in reversed(self.labMap):
            print(''.join([str(l) for l in l]))

    def getExpectedMeasures(self, i, j):
        # Returns the M values for the cell (i, j)
        return self.M_values[(i, j)]

    def gaussian_prob(self, mu, sigma, x):
        # Calculates the Gaussian probability
        return (1.0 / (sqrt(2 * pi) * sigma)) * exp(-0.5 * ((x - mu) ** 2) / (sigma ** 2))

    def motionUpdate(self, lin, ang):
        # Initialize a new probability map with zeros
        new_prob_map = [[0.0 for _ in range(CELLCOLS)] for _ in range(CELLROWS)]

        # Define motion uncertainty (can be adjusted)
        motion_noise = 0  # Standard deviation for movement
        possible_moves = [(0, 1)]  # Forward movement

        for i in range(CELLROWS):
            for j in range(CELLCOLS):
                prob = self.prob_map[i][j]
                if prob > 0:
                    for move in possible_moves:
                        new_i = i + move[0]
                        new_j = j + move[1]
                        if 0 <= new_i < CELLROWS and 0 <= new_j < CELLCOLS:
                            # Distribute the probability to neighboring cells
                            new_prob_map[new_i][new_j] += prob * (1 - motion_noise) / len(possible_moves)
                        else:
                            # Probability of hitting a wall or boundary
                            new_prob_map[i][j] += prob * motion_noise / len(possible_moves)

        # Normalize the new probability map
        total_prob = sum(sum(row) for row in new_prob_map)
        for i in range(CELLROWS):
            for j in range(CELLCOLS):
                new_prob_map[i][j] /= total_prob

        self.prob_map = new_prob_map  # Update the probability map with motion update

        # Print the probability map after motion update
        print("Probability map after motion update:")
        self.printProbabilityMap()

    def updateLocalization(self):
        # Get sensor readings from the robot's sensors
        sensor_readings = [
            self.measures.irSensor[0],
            self.measures.irSensor[1],
            self.measures.irSensor[2],
            self.measures.irSensor[3]
        ]

        # Print sensor values at the center of the cell
        print("Sensor values at the center of the cell:", sensor_readings)

        updated_probs = []
        for i in range(CELLROWS):
            row_probs = []
            for j in range(CELLCOLS):
                prior = self.prob_map[i][j]
                likelihood = 1.0
                expected_measures = self.getExpectedMeasures(i, j)

                for sensor_value, expected_value in zip(sensor_readings, expected_measures):
                    # Calculate the likelihood using Gaussian probability
                    likelihood *= self.gaussian_prob(expected_value, self.noise, sensor_value)

                posterior = likelihood * prior
                row_probs.append(posterior)
            updated_probs.append(row_probs)

        # Normalize the updated probabilities
        total_prob = sum(sum(row) for row in updated_probs)
        if total_prob > 0:
            for i in range(CELLROWS):
                for j in range(CELLCOLS):
                    updated_probs[i][j] /= total_prob
        else:
            # Handle the case where total_prob is zero to avoid division by zero
            updated_probs = self.prob_map  # Keep the prior if measurement likelihood is zero

        self.prob_map = updated_probs

        # Print the probability map after measurement update
        print("Probability map after measurement update:")
        self.printProbabilityMap()

    def printProbabilityMap(self):
        # Print the probability map in a readable format
        for row in reversed(self.prob_map):
            line = " ".join(f"{p:.4f}" for p in row)
            print(line)
        print("\n")
        
        # Append the probability map to the output file
        with open(self.file_name, "a") as f:
            for row in reversed(self.prob_map):
                line = " ".join(f"{p:.4f}" for p in row)
                f.write(line + "\n")
            f.write("\n")  # Add a blank line to separate tables

    def applyMovementModel(self, in_left_t, in_right_t):
        # Update movement outputs
        self.out_left = in_left_t
        self.out_right = in_right_t

        # Calculate linear and angular movements
        lin = (self.out_right + self.out_left) / 2
        ang = (self.out_right - self.out_left) / ROBOT_DIAM

        # Update the sum of distances traveled
        self.distance_sum += lin

        # If the robot has moved approximately one cell size, perform motion update
        if self.distance_sum >= CELL_SIZE:
            print(f"Moved one cell size with accumulated distance {self.distance_sum}")
            self.motionUpdate(lin, ang)  # Perform the motion update
            self.updateLocalization()    # Update and print the probability map after motion
            self.distance_sum -= CELL_SIZE  # Reset the distance sum for the next cell

    def run(self):
        if self.status != 0:
            print("Connection refused or error")
            quit()

        print("Robot started")

        # Read sensors once to initialize `measures` before using `updateLocalization`
        self.readSensors()

        # Initialize localization from the starting point
        self.updateLocalization()

        while True:
            self.readSensors()

            if self.measures.endLed:
                print(self.rob_name + " exiting")
                quit()

            if self.state == 'stop' and self.measures.start:
                self.state = 'run'

            if self.state != 'stop' and self.measures.stop:
                self.state = 'stop'

            if self.state == 'run':
                # Remove or comment out the following lines
                # if self.measures.visitingLed:
                #     self.state = 'wait'
                # if self.measures.ground == 0:
                #     self.setVisitingLed(True)
                self.wander()
            # Remove the 'elif' block for the 'wait' state if it's no longer needed
            # elif self.state == 'wait':
            #     self.setReturningLed(True)
            #     if self.measures.visitingLed:
            #         self.setVisitingLed(False)
            #     if self.measures.returningLed:
            #         self.state = 'return'
            #     self.driveMotors(0.0, 0.0)
            elif self.state == 'return':
                if self.measures.visitingLed:
                    self.setVisitingLed(False)
                if self.measures.returningLed:
                    self.setReturningLed(False)
                self.wander()

    def wander(self):
        center_id = 0  # Index of the front sensor
        FRONT_THRESHOLD = 0.5  # Adjust this value as needed

        if self.state == 'run':
            if self.measures.irSensor[0] > 2.6:  # Assuming there's an attribute for collision
                print('Collision detected, stopping the robot.')
                self.driveMotors(0.0, 0.0)
                self.state = 'stop'
            else:
                print('Path clear, continuing forward.')
                self.applyMovementModel(0.1, 0.1)
                self.driveMotors(0.1, 0.1)

if __name__ == '__main__':
    # Set up argument parsing for command-line inputs
    parser = argparse.ArgumentParser(description='Robot Localization and Control.')
    parser.add_argument('--host', '-H', type=str, default='localhost', help='Host address')
    parser.add_argument('--pos', '-p', type=int, default=1, help='Initial position of the robot')
    parser.add_argument('--robname', '-r', type=str, default='pClient1', help='Name of the robot')
    parser.add_argument('--map', '-m', type=str, required=True, help='Path to the XML map file')
    # Example: python3 mainRob.py -H host_or_ip -m lab.xml -p 1
    args = parser.parse_args()

    rob_name = args.robname
    host = args.host
    pos = args.pos
    xml_file_path = args.map

    # Read patterns from the XML file
    try:
        patterns = parse_lab_file(xml_file_path)
    except Exception as e:
        print(f"Error reading the XML file: {e}")
        quit()

    # Reverse the list to align cell indices (line 0 at the bottom)
    patterns = patterns[::-1]

    # Build the labMap with consistent line lengths
    labMap = []
    for pattern in patterns:
        labMap.append(pattern)

    # Build the cells and calculate expected measures
    cells = build_cells(labMap)
    M_values = compute_expected_measures(cells)

    # Initialize the robot with the read map
    rob = MyRob(rob_name, pos, [0.0, 90.0, -90.0, 180.0], host, M_values)
    rob.setMap(labMap)
    rob.printMap()

    # Run the robot
    rob.run()
