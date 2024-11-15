def parse_lab_map(lab_map):
    return [list(row) for row in lab_map.splitlines() if row.strip() != '']


def is_space(lab_map, i, j):
    if i < 0 or i >= len(lab_map) or j < 0 or j >= len(lab_map[0]):
        return False
    return lab_map[i][j] == ' '


def is_top_wall(lab_map, i, j):
    if i == 6:
        return True  # Top boundary of the map
    return not is_space(lab_map, i * 2 - 1, j * 2)


def is_right_wall(lab_map, i, j):
    if j == 13:
        return True  # Right boundary of the map
    return not is_space(lab_map, i * 2, j * 2 + 1)


def is_bottom_wall(lab_map, i, j):
    if i == 0:
        return True  # Bottom boundary of the map
    return not is_space(lab_map, i * 2 + 1, j * 2)


def is_left_wall(lab_map, i, j):
    if j == 0:
        return True  # Left boundary of the map
    return not is_space(lab_map, i * 2, j * 2 - 1)


def check_sensors(lab_map):
    D_values = [[[-1 for _ in range(4)] for j in range(14)] for i in range(7)]

    for i in range(7):
        for j in range(14):
            # Sensor 0 (right)
            if j == 13:
                D_values[i][j][0] = 0.5
            elif is_right_wall(lab_map, i, j):
                D_values[i][j][0] = 0.4
            else:
                if (j < 13 and (is_top_wall(lab_map, i, j + 1) or is_bottom_wall(lab_map, i, j + 1))):
                    D_values[i][j][0] = 1.8
                else:
                    D_values[i][j][0] = 2.6

            # Sensor 1 (top)
            if i == 6:
                D_values[i][j][1] = 0.5
            elif is_top_wall(lab_map, i, j):
                D_values[i][j][1] = 0.4
            else:
                if (i < 6 and (is_left_wall(lab_map, i + 1, j) or is_right_wall(lab_map, i + 1, j))):
                    D_values[i][j][1] = 1.8
                else:
                    D_values[i][j][1] = 2.6

            # Sensor 2 (bottom)
            if i == 0:
                D_values[i][j][2] = 0.5
            elif is_bottom_wall(lab_map, i, j):
                D_values[i][j][2] = 0.4
            else:
                if (i > 0 and (is_left_wall(lab_map, i - 1, j) or is_right_wall(lab_map, i - 1, j))):
                    D_values[i][j][2] = 1.8
                else:
                    D_values[i][j][2] = 2.6

            # Sensor 3 (left)
            if j == 0:
                D_values[i][j][3] = 0.5
            elif is_left_wall(lab_map, i, j):
                D_values[i][j][3] = 0.4
            else:
                if (j > 0 and (is_top_wall(lab_map, i, j - 1) or is_bottom_wall(lab_map, i, j - 1))):
                    D_values[i][j][3] = 1.8
                else:
                    D_values[i][j][3] = 2.6

    return D_values

def print_walls(lab_map):
    for i in range(7):
        for j in range(14):
            top = is_top_wall(lab_map, i, j)
            right = is_right_wall(lab_map, i, j)
            bottom = is_bottom_wall(lab_map, i, j)
            left = is_left_wall(lab_map, i, j)
            print(f"Cell ({i}, {j}): Top: {'Wall' if top else 'Space'}, Right: {'Wall' if right else 'Space'}, Bottom: {'Wall' if bottom else 'Space'}, Left: {'Wall' if left else 'Space'}")

# Example usage
lab_map = """
  |        |     |                 |     
  ·--·  ·--·--·  ·  ·--·--.--·--·  ·--·--
  |        |              |        |     
--·--·  ·--·  ·--·--·--·  ·--·--·  ·--·  
        |        |     |     |     |  |  
--·--·--·  ·--·  .--·--·--·  ·  ·  ·--·  
  |                                      
  ·--·--·--·--·--·--·  ·  ·--·  ·--·--·--
     |  |              |     |     |     
  ·--·  ·--·--·--·--·  ·--·  ·  ·--·  ·  
  |                 |           |     |  
  ·--·  ·--·--·--·  ·--·--·  ·--·  ·--·  
  |  |           |           |     |     
"""

lab_map_parsed = parse_lab_map(lab_map)
D_values = check_sensors(lab_map_parsed)
print_walls(lab_map_parsed)

for i in range(7):
    for j in range(14):
        print(f"Cell ({i}, {j}): Sensors D-values = {D_values[i][j]}")
