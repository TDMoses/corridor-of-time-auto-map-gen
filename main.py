import warnings
import math
import csv
import numpy as np
from hexagon import Hexagon
from PIL import Image
from matplotlib import pyplot as plt

_link_connections = dict(
    [(1, 4), (2, 5), (3, 6), (4, 1), (5, 2), (6, 3)]
)


def convert_num_to_link_name(link_num):
    return 'link' + str(link_num + 1)


def convert_link_name_to_num(link_name):
    return int(link_name[-1]) - 1


def connect_hexes(hexagon1, hexagon2, link_id1, link_id2):
    hexagon1.set_hexagon_link(hexagon2, link_id1)
    hexagon2.set_hexagon_link(hexagon1, link_id2)


def match_hexagons(hexagons, hexagon_missing_links):
    for hexagon in hexagons:
        hex_missing_links = hexagon.get_available_links()
        for missing_link_id in hex_missing_links:
            matching_link_id = _link_connections[missing_link_id + 1] - 1 # back to 0 index
            hex_link_value = hexagon.links[missing_link_id]
            missing_link_name = convert_num_to_link_name(missing_link_id)
            matching_link_name = convert_num_to_link_name(matching_link_id)
            for search_list_id, possible_hex_id in \
                           enumerate(hexagon_missing_links[matching_link_name]):
                possible_hex = hexagons[possible_hex_id]

                if possible_hex.is_link_match(link_id=matching_link_id,
                                              link_value=hex_link_value):
                    connect_hexes(hexagon1=hexagon,
                                  hexagon2=possible_hex,
                                  link_id1=missing_link_id,
                                  link_id2=matching_link_id)
                    try:
                        del hexagon_missing_links[matching_link_name][search_list_id]
                        hexagon_missing_links[missing_link_name].remove(hexagon.id)
                    except Exception as e:
                        print(e)
                        # import ipdb;ipdb.set_trace(context=5)
                        print()
                        break

                    break


def set_hexagon_neightbor_locations(hexagon, hexagons):

    hex_outer_centers = [[ 1.07156595e-14, -1.75000000e+02],
       [ 1.51554446e+02, -8.75000000e+01],
       [ 1.51554446e+02,  8.75000000e+01],
       [ 1.07156595e-14,  1.75000000e+02],
       [-1.51554446e+02,  8.75000000e+01],
       [-1.51554446e+02, -8.75000000e+01]]

    link_relative_pos = dict(list(zip(range(6), hex_outer_centers)))
    for link_num, neighbor_id in enumerate(hexagon.hexagon_links):
        if neighbor_id not in [None, False]:
            neighbor = hexagons[neighbor_id]
            if not np.isnan(neighbor.map_x):
                continue
            neighbor.map_x = hexagon.map_x + link_relative_pos[link_num][0]
            neighbor.map_y = hexagon.map_y + link_relative_pos[link_num][1]


def build_maps(hexagons):

    maps = []

    for initial_hexagon in hexagons:
        if initial_hexagon.visited:
            continue

        initial_hexagon.map_x = 0
        initial_hexagon.map_y = 0
        initial_hexagon.visited = True

        queue = initial_hexagon.get_hexagon_connetions()
        set_hexagon_neightbor_locations(initial_hexagon, hexagons)
        maps.append([initial_hexagon])

        prev_hex_id = initial_hexagon.id

        while queue:
            curr_hex_id = queue.pop()
            curr_hex = hexagons[curr_hex_id]

            if not curr_hex.visited:
                curr_hex.visited = True
                queue.extend(curr_hex.get_hexagon_connetions())
                set_hexagon_neightbor_locations(curr_hex, hexagons)
                maps[-1].append(curr_hex)
    return maps

def build_images(maps):

    def get_min_max_coords(map):
        min_coords = [np.inf ,  np.inf]
        max_coords = [-np.inf, -np.inf]
        for hexagon in map:
            if hexagon.map_x < min_coords[0]:
                min_coords[0] = hexagon.map_x
            if hexagon.map_y < min_coords[1]:
                min_coords[1] = hexagon.map_y
            if hexagon.map_x > max_coords[0]:
                max_coords[0] = hexagon.map_x
            if hexagon.map_y > max_coords[1]:
                max_coords[1] = hexagon.map_y
        return min_coords, max_coords

    for map_id, map_ in enumerate(maps):
        if len(map_) < 5:
            continue
        min_coords, max_coords = get_min_max_coords(map_)
        centering_image_shift = 100

        image_size =(
            math.ceil(max_coords[0] - min_coords[0]) + centering_image_shift*2,
            math.ceil(max_coords[1] - min_coords[1]) + centering_image_shift*2
        )

        img = Image.new('RGBA', image_size, (255, 255, 255, 255))
        for hexagon in map_:
            hex_img = hexagon.draw_self()
            hex_loc = (int(round(hexagon.map_x - min_coords[0])),
                       int(round(hexagon.map_y - min_coords[1])))
            img.paste(hex_img, hex_loc, mask=hex_img)

        img.convert('RGB').save('maps/map' + str(map_id) + '.jpg', 'JPEG', quality=80)
        # img_data = np.array(img)
        # plt.imshow(img_data)
        # plt.show()

if __name__ == "__main__":

    _filepath = "dawning_sample.csv"
    shift_openings = False

    _hexagons = []
    _hexagon_missing_links = dict(
        link1=[], link2=[], link3=[], link4=[], link5=[], link6=[]
    )

    _dup_hash = dict()
    with open(_filepath, 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        header = next(csvreader)

        _hexagon_id = 0
        for row_id, row in enumerate(csvreader):
            row = dict(list(zip(header[:12], row[:12])))
            # import ipdb;ipdb.set_trace(context=5)
            if all(np.array(list(row.values())) == ''):
                continue
            if row['Center'].lower().strip() in ['duplicate', '100% match', 'none']:
                continue
            elif row['Link1'].strip() == '':
                warnings.warn('missing link row: {}'.format(str(_hexagon_id)))
                continue

            row['Openings'] = row['Openings'].replace('.', ',')
            if shift_openings and row['Openings'].strip() != '':
                try:
                    _openings = list(map(lambda x: str(int(x) + 1), row['Openings'].strip().split(',')))
                except Exception as e:
                    import ipdb; ipdb.set_trace(context=5)
                    print(e)
            else:
                _openings = row['Openings'].strip().split(',')

            _new_hex = Hexagon(
                id=_hexagon_id,
                spreadsheet_row= row_id + 2,
                center=row['Center'].strip(),
                openings=_openings,
                link1=row['Link1'].strip(),
                link2=row['Link2'].strip(),
                link3=row['Link3'].strip(),
                link4=row['Link4'].strip(),
                link5=row['Link5'].strip(),
                link6=row['Link6'].strip(),
            )
            if _dup_hash.get(_new_hex.get_hash(), False):
                continue
            _dup_hash[_new_hex.get_hash()] = True

            _hexagons.append(_new_hex)
            for _missing_link_num in _hexagons[-1].get_available_links():
                _link_name = convert_num_to_link_name(_missing_link_num)
                _hexagon_missing_links[_link_name].append(_hexagon_id)

            _hexagon_id += 1
    match_hexagons(_hexagons, _hexagon_missing_links)

    # import ipdb;ipdb.set_trace(context=5)
    maps = build_maps(_hexagons)
    build_images(maps)
    print(_hexagons)
