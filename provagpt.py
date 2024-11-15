def parse_lab_map(lab_map):
    return [list(row) for row in lab_map.splitlines() if row.strip() != '']


def is_space(lab_map, i, j):
    if i < 0 or i >= len(lab_map) or j < 0 or j >= len(lab_map[0]):
        return False
    return lab_map[i][j] == ' '


def check_sensors(lab_map):
    rows = len(lab_map)
    cols = len(lab_map[0])
    D_values = [[[-1 for _ in range(4)] for j in range(14)] for i in range(7)]

    for i in range(7):
        for j in range(14):
            # Sensor 0 (right)
            if j < 13:
                if not is_space(lab_map, i * 2, j * 2 + 1):
                    D_values[i][j][0] = 0.4
                elif is_space(lab_map, i * 2, j * 2 + 1):
                    if not is_space(lab_map, i * 2, (j + 1) * 2) or not is_space(lab_map, i * 2 + 1, (j + 1) * 2):
                        D_values[i][j][0] = 1.8
                    elif is_space(lab_map, i * 2, (j + 1) * 2) and is_space(lab_map, i * 2 + 1, (j + 1) * 2):
                        D_values[i][j][0] = 2.0
                    else:
                        D_values[i][j][0] = 2.6
            else:
                D_values[i][j][0] = 0.5

            # Sensor 1 (top)
            if i < 6:
                if not is_space(lab_map, i * 2 + 1, j * 2):
                    D_values[i][j][1] = 0.4
                elif is_space(lab_map, i * 2 + 1, j * 2):
                    if not is_space(lab_map, (i + 1) * 2, j * 2 - 1) or not is_space(lab_map, (i + 1) * 2, j * 2 + 1):
                        D_values[i][j][1] = 1.8
                    elif is_space(lab_map, (i + 1) * 2, j * 2 - 1) and is_space(lab_map, (i + 1) * 2, j * 2 + 1):
                        D_values[i][j][1] = 2.0
                    else:
                        D_values[i][j][1] = 2.6
            else:
                D_values[i][j][1] = 0.5

            # Sensor 2 (bottom)
            if i > 0:
                if not is_space(lab_map, i * 2 - 1, j * 2):
                    D_values[i][j][2] = 0.4
                elif is_space(lab_map, i * 2 - 1, j * 2):
                    if not is_space(lab_map, (i - 1) * 2, j * 2 - 1) or not is_space(lab_map, (i - 1) * 2, j * 2 + 1):
                        D_values[i][j][2] = 1.8
                    elif is_space(lab_map, (i - 1) * 2, j * 2 - 1) and is_space(lab_map, (i - 1) * 2, j * 2 + 1):
                        D_values[i][j][2] = 2.0
                    else:
                        D_values[i][j][2] = 2.6
            else:
                D_values[i][j][2] = 0.5

            # Sensor 3 (left)
            if j > 0:
                if not is_space(lab_map, i * 2, j * 2 - 1):
                    D_values[i][j][3] = 0.4
                elif is_space(lab_map, i * 2, j * 2 - 1):
                    if not is_space(lab_map, i * 2, (j - 1) * 2) or not is_space(lab_map, i * 2 + 1, (j - 1) * 2):
                        D_values[i][j][3] = 1.8
                    elif is_space(lab_map, i * 2, (j - 1) * 2) and is_space(lab_map, i * 2 + 1, (j - 1) * 2):
                        D_values[i][j][3] = 2.0
                    else:
                        D_values[i][j][3] = 2.6
            else:
                D_values[i][j][3] = 0.5

    return D_values


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

for i in range(7):
    for j in range(14):
        print(f"Cell ({i}, {j}): Sensors D-values = {D_values[i][j]}")
