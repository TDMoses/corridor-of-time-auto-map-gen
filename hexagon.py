import numpy as np
from PIL import Image, ImageDraw, ImageFont
from matplotlib import pyplot as plt

class Hexagon:

    def __init__(self, id, spreadsheet_row, center, openings, link1, link2, link3, link4, link5, link6):
        center_alts = {'hexagon': 'hex', '': 'blank', 'd': 'diamond', 'pluss': 'plus', 'sneak': 'snake'}
        if center.lower() in center_alts:

            center = center_alts[center.lower()]
        if not isinstance(center, str) or \
            center.lower() not in ['blank', 'clover', 'diamond', 'hex', 'plus', 'snake']:
            print(center)
            import ipdb;ipdb.set_trace(context=5)
            raise ValueError('`center` not valid.')
        elif not isinstance(openings, list) or len(openings) < 1:
            raise ValueError('`openings` must be a list with a least 1 opening.')

        valid_links = ['bcdhps']

        self.id = id
        self.spreadsheet_row = spreadsheet_row
        self.center = center.lower()
        self.openings = sorted([opening.strip() for opening in openings])
        self.links = np.array([link1, link2, link3, link4, link5, link6])
        self.hexagon_links = [False] * 6

        self.visited = False
        self.map_x = np.NaN
        self.map_y = np.NaN

        for i, link in enumerate(self.links):
            if link.lower().strip() in ['bbbbbb', 'bbbbbbb','bbbbb','bbbbbbbb']:  # no link
                self.hexagon_links[i] = None

    def get_hash(self):
        return self.center + ''.join(self.openings) + ''.join(self.links.tolist())

    def get_hexagon_connetions(self):
        return [id for id in self.hexagon_links if id not in [None, False]]

    def get_available_links(self):
        return [i for i, link_value in enumerate(self.hexagon_links)
                if link_value == False]

    def is_missing_links(self):
        return len(self.get_available_links()) > 0

    def is_link_match(self, link_id, link_value):
        def possible_rotation(value):
            b = len(value)
            value_rotations = []
            for i in range (b):
                value_rotations.append(value[i:]+value[:i])
            return value_rotations
        if link_value.lower().strip() == 'bbbbbb':
            return False
        return self.links[link_id] == link_value
        # return self.links[link_id] == link_value or self.links[link_id] == link_value[::-1]
        # return self.links[link_id] in possible_rotation(link_value) or \
        #         self.links[link_id] in possible_rotation(link_value[::-1])

    def set_hexagon_link(self, hexagon, link_id):
        self.hexagon_links[link_id] = hexagon.id


    def draw_self(self):
        img = Image.new('RGBA', [200, 200], 0)
        draw = ImageDraw.Draw(img)
        self._draw_center_hexagon(img, draw)
        return img
        # img_data = np.array(img)
        # plt.imshow(img_data)
        # plt.show()

    @staticmethod
    def _get_corners_of_hexagon(center_x, center_y, size):
        hex_corners = [[np.NaN, np.NaN] for _ in range(6)]
        for i in range(6):
            angle_deg = 60 * i - 120
            angle_rad = np.pi / 180 * angle_deg
            hex_corners[i][0] = center_x + size * np.cos(angle_rad)
            hex_corners[i][1] = center_y + size * np.sin(angle_rad)
        return np.array(hex_corners)

    def _draw_center_hexagon(self, img, draw):
        hex_corners = self._get_corners_of_hexagon(100, 100, 50)
        self._draw_hexagon(img, draw, hex_corners, self.center)
        self._draw_spreadsheet_id(draw, self.spreadsheet_row)
        self._draw_trapezoid_around_hex(draw, hex_corners)
        self._draw_openings(draw, hex_corners)

    def _draw_openings(self, draw, hex_corners):
        hex_corners_loop = hex_corners.copy()
        hex_corners_loop = np.append(hex_corners_loop, [hex_corners_loop[0,:]],
                                     axis=0)
        for opening_id in range(6):
            if str(opening_id + 1) in self.openings:
                continue
            opening_id = int(opening_id)
            draw.line(
                tuple(map(tuple,
                    hex_corners_loop[opening_id: opening_id + 2,:])),
                fill='black', width=5
            )

    def _draw_trapezoid_around_hex(self, draw, hex_corners):
        outer_hex_corners = self._get_corners_of_hexagon(100, 100, 100)
        text_locations = ((80, 31), (142,61), (138,133), (76, 160), (15,112), (22,67))
        for i in range(6): # each side
            if i == 5:
                trap1_corners = np.concatenate([[hex_corners[i, :]], [outer_hex_corners[i, :]], [outer_hex_corners[0, :]],[ hex_corners[0, :]]])
            else:
                trap1_corners = np.concatenate([[hex_corners[i, :]], [outer_hex_corners[i, :]], [outer_hex_corners[i+1, :]],[ hex_corners[i+1, :]]])
            if str(i+1) in self.openings:
                color = (0, 180, 0, 30)
            else:
                color = (180, 180, 180, 30)
            draw.polygon(
                tuple(map(tuple,trap1_corners)),
                fill=color
            )

            font = ImageFont.truetype('arial', size=8)
            draw.text(text_locations[i], self.links[i], font=font, fill=(255,0,0,255))

    @staticmethod
    def _draw_spreadsheet_id(draw, spreadsheet_row):
        font = ImageFont.truetype('arial', size=12)
        text_location = (95, 95)
        draw.text(text_location, str(spreadsheet_row), font=font, fill=(255,0,0,255))

    @staticmethod
    def _draw_hexagon(img, draw, hex_corners, symbol):
        draw.polygon(list(zip(hex_corners[:, 0], hex_corners[:, 1])),
                     fill=(80, 80, 80, 30))
        if symbol.lower() != "blank":
            symbol_file = 'symbols/' + symbol + '.png'
            im_symbol = Image.open(symbol_file)
            im_symbol_small = im_symbol.resize((55, 55))
            img.paste(im_symbol_small, (73, 73), mask=im_symbol_small)
