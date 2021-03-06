import copy
import os
import math
import requests
#from lxml import html
import colorsys
from urllib.parse import urlparse
#For image exporting
from PIL import Image, ImageDraw
import json
from bs4 import BeautifulSoup

class Art():
    """Contains palette and pixel data"""
    def __init__(self, palette=None, image_size=(16, 16), pixels=None):
        self.image_size = image_size
        if not palette:
            #Greyscale palette by default
            self.palette = {}
            self.palette[0] = "#FFFFFF"
            self.palette[1] = "#E5E5E5"
            self.palette[2] = "#D5D5D5"
            self.palette[3] = "#C5C5C5"
            self.palette[4] = "#B5B5B5"
            self.palette[5] = "#A5A5A5"
            self.palette[6] = "#959595"
            self.palette[7] = "#858585"
        else:
            self.palette = palette

        if not pixels:
            #Image is square of palette colour 0 by default.
            self.pixels = [[0 for x in range(image_size[0])] for y in range(image_size[1])]
        else:
            self.pixels = pixels

    def sort_palette(self):
        """Sort the colour palette.
        Sorting colours is actually really hard so this does its best."""

        def step_sort(r,g,b, repetitions=1):
            """Set up sorting function"""
            lum = math.sqrt( .241 * r + .691 * g + .068 * b )
            h, s, v = colorsys.rgb_to_hsv(r,g,b)
            h2 = int(h * repetitions)
            lum2 = int(lum * repetitions)
            v2 = int(v * repetitions)
            if h2 % 2 == 1:
                v2 = repetitions - v2
                lum2 = repetitions - lum2
            return (h2, lum2, v2)

        colours_as_list = [self.html_colour_to_rgb(self.palette[index]) for index in self.palette]
        sorted_colours = sorted(colours_as_list, key= lambda rgb: step_sort(*rgb,10))
        old_palette = copy.copy(self.palette)
        old_pixels = copy.deepcopy(self.pixels)

        #Actually sort the palette
        for key in self.palette:
            self.palette[key] = self.rgb_colour_to_html(*sorted_colours[key])
        
        #Update the pixel value to the new indexes
        for old_index in old_palette:
            colour = old_palette[old_index]
            new_index = [k for k,v in self.palette.items() if v.lower()==colour.lower()][0]
            for y, row in enumerate(old_pixels):
                for x, index in enumerate(row):
                    if index == old_index:
                        self.pixels[y][x] = new_index
        
        
    def set_pixel(self, x, y, colour):
        """Set a pixel at a given coordinate"""
        self.pixels[x][y] = colour
        
    def html_colour_to_rgb(self, html_colour):
        """Convert a html colour code to an rgb triple"""
        r, g, b = html_colour[1:3], html_colour[3:5], html_colour[5:]
        r, g, b = [int(n, 16) for n in (r, g, b)]
        return (r, g, b)
    
    def rgb_colour_to_html(self, r, g, b):
        """
        "Convert a rgb triple to a hex colour
        src: https://stackoverflow.com/questions/3380726/converting-a-rgb-color-tuple-to-a-six-digit-code-in-python
        """
        def clamp(x): 
            return max(0, min(x, 255))
        return "#{0:02x}{1:02x}{2:02x}".format(clamp(r), clamp(g), clamp(b))


    def export_to_image_file(self, filename, scalar=10, transparent_palette_index=None):
        """
        Export the current image to a file
        """
        format_colour_modes = {
            ".jpg": "RGB",
            ".png": "RGBA",
            ".gif": "RGB"
        }
        
        colour_mode = format_colour_modes[os.path.splitext(filename)[1]]
        #Create blank image
        img = Image.new(colour_mode, (len(self.pixels[1]), len(self.pixels[0])))
        d = ImageDraw.Draw(img)
        #Add each individual pixel to the image
        for xn, x in enumerate(self.pixels):
            for yn, y in enumerate(x):
                if y != transparent_palette_index or not "A" in colour_mode:
                    d.point((yn,xn), fill=(self.html_colour_to_rgb(self.palette[y])))
        
        img = img.resize((scalar*img.size[0], scalar*img.size[1]))

        img.save(filename)

    def load_from_file(filename):
        """Load an Art object from a file""" #TODO: Implement pixel loading
        components = {}
        with open(filename) as f:
            for line in f:
                key, value = line.split(", ")
                components[key] = value.strip()

        #Load palette
        palette = {}
        for colour_index, colour in enumerate(components["palette"].split(" ")):
            palette[colour_index] = colour.strip()
        #Load image size
        size = (int(components["size"]), int(components["size"]))

        #Load pixels
        pixels = [int(pixel.strip()) for pixel in components["pixels"].split(" ")]
        pixels = [pixels[i:i+size[0]] for i in range(0, len(pixels), size[0])]
        print(pixels)
            
        return Art(palette=palette, image_size=size, pixels=pixels)

    def load_palette_from_file(self, filename):
        """Change the palette to one that is loaded from a file."""
        components = {}
        palette = {}
        with open(filename) as f:
            for line in f:
                key, value = line.split(", ")
                components[key] = value
                if key == "palette":
                    for colour_index, colour in enumerate(value.split(" ")):
                        palette[colour_index] = colour.strip()      
                    break    
        
        self.palette = palette

    def save_to_file(self, filename):
        """Save the art to a file"""
        with open(filename, "w") as f:
            #Size
            f.write("size, {}\n".format(len(self.pixels)))
            #Palette
            colours = " ".join([self.palette[index] for index in self.palette])
            f.write("palette, {}\n".format(colours))
            #Pixels
            pixels = " ".join([str(pixel) for pixel_row in self.pixels for pixel in pixel_row])
            f.write("pixels, {}\n".format(pixels))
    
    def copy(self):
        """Get a new instance of this art object"""
        new_pixels = copy.deepcopy(self.pixels)
        return Art(self.palette, self.image_size, new_pixels )

    def load_palette_from_url(self, url):
        """
        Get a palette from a url.
        """
        print("loading from: {}".format(url))
        pl = PaletteLoader()

        for site in pl.supported_sites:
            if site in url:
                new_palette = pl.supported_sites[site](url)
                for index in new_palette:
                    print("Loading {} into index {}".format(new_palette[index], index))
                    self.palette[index] = new_palette[index]
                return True
        else:
            print("Unsupported URL: {}".format(url))
            print("Supported sites: {}".format([s for s in pl.supported_sites]))
            return False

class PaletteLoader():
    def __init__(self):
        self.supported_sites = {
            "colormind.io": lambda url: self.load_random_from_colormind(),
            "colourlovers.com": lambda url: self.load_from_colourlovers(url),
            "color-hex.com": lambda url: self.load_from_color_hex(url),
        }

    def load_random_from_colormind(self):
        """
        Load a random palette from colormind.io using the API
        """
        palette = {}
        headers = '{"model": "default"}'
        r = requests.get("http://colormind.io/api/", data=headers)

        if r.status_code == 200:
            for index, rgb in enumerate(r.json()['result']):
                palette[index] = Art().rgb_colour_to_html(*rgb)
                print(index,rgb)
        else:
            print("Failed api call: {} - {}".format(r, r.status_code))

        return palette

    
    def load_from_colourlovers(self, url):
        """e.g colourlovers : "http://www.colourlovers.com/palette/49963/let_them_eat_cake" """
        palette = {}
        api_url = "{}/{}".format(url.replace("/palette","/api/palette"), "/?format=json")
        r = requests.get(api_url)
        if r.status_code == 200:
            for index, colour in enumerate(r.json()[0]["colors"]):
                palette[index] = "#{}".format(colour)

        return palette

    def load_from_color_hex(self, url):
        """
        e.g https://www.color-hex.com/color-palette/65513
        """
        palette = {}
        r = requests.get(url)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "lxml")
            for index, palette_div in enumerate(soup.find_all("div", attrs={'class': 'palettecolordivc'})):
                palette[index] = palette_div["title"]
        return palette

class Tool():
    def __init__(self):
        pass

    def activate(self, location, pixelgrid, symbol):
        #Modifies pixel grid in-place
        pass

    def _get_neighbouring_locations(self, location, pixelgrid):
        #Return a list of neighbouring coordinates
        x,y = location[0], location[1]

        nieghbours = []

        up = (x, y-1)
        down = (x, y+1)
        right = (x+1, y)
        left = (x-1, y)
        for direction in (up, down, left, right):
            if min(direction) < 0:
                continue
            elif max(direction) >= len(pixelgrid):
                continue
            else:
                nieghbours.append(direction)
        return nieghbours

class MirroredPencil(Tool):
    def __init__(self, axis="x"):
        self.axis = axis

    def activate(self, location, pixelgrid, symbol):
        x, y = location[0], location[1]
        pixelgrid[y][x] = symbol

        if "y" in self.axis:
            mirrored_x = len(pixelgrid[0])-1-x
            print("mirroring to: ", mirrored_x, y)
            pixelgrid[y][mirrored_x] = symbol
        if "x" in self.axis:
            mirrored_y = len(pixelgrid[1])-1-y
            print("mirroring to: ", x, mirrored_y)
            pixelgrid[mirrored_y][x] = symbol
        if "xy" in self.axis or "yx" in self.axis:
            pixelgrid[mirrored_y][mirrored_x] = symbol


class Pencil(Tool):
    def __init__(self):
        pass

    def activate(self, location, pixelgrid, symbol):
        x, y = location[0], location[1]
        pixelgrid[y][x] = symbol

class Bucket(Tool):
    def __init__(self):
        pass

    def activate(self, location, pixelgrid, symbol):
        x, y = location[0], location[1]
        symbol_to_fill = pixelgrid[y][x]
        visited_locations = []
        locations_to_expand = [location]

        while len(locations_to_expand) > 0:
            x, y = locations_to_expand[0]

            if pixelgrid[y][x] == symbol_to_fill:
                pixelgrid[y][x] = symbol
                locations_to_expand = locations_to_expand + self._get_neighbouring_locations((x,y), pixelgrid)
                locations_to_expand = [l for l in locations_to_expand if l not in visited_locations]

            if (x,y) in locations_to_expand:
                locations_to_expand.remove((x,y))

            visited_locations.append((x,y))

class PartialBucket(Tool):
    def __init__(self):
        pass

    def activate(self, location, pixelgrid, symbol):
        x, y = location[0], location[1]
        symbol_to_fill = pixelgrid[y][x]
        visited_locations = []
        locations_to_expand = [location]

        while len(locations_to_expand) > 0:
            x, y = locations_to_expand[0]

            if pixelgrid[y][x] == symbol_to_fill:
                if (x+y)%2==0:
                    pixelgrid[y][x] = symbol
                locations_to_expand = locations_to_expand + self._get_neighbouring_locations((x,y), pixelgrid)
                locations_to_expand = [l for l in locations_to_expand if l not in visited_locations]

            if (x,y) in locations_to_expand:
                locations_to_expand.remove((x,y))

            visited_locations.append((x,y))

def main():
    a = Art(image_size=(5,5))
    a.load_palette_from_url("http://www.colourlovers.com/palette/49963/let_them_eat_cake")
    #a.save_to_file("CAKE.pxlart")


if __name__ == "__main__":
    main()