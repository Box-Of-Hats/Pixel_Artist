import copy
import imageio
#For image exporting
from PIL import Image, ImageDraw

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

    
    def set_pixel(self, x, y, colour):
        """Set a pixel at a given coordinate"""
        self.pixels[x][y] = colour
        
    def html_colour_to_rgb(self, html_colour):
        """Convert a html colour code to an rgb triple"""
        r, g, b = html_colour[1:3], html_colour[3:5], html_colour[5:]
        r, g, b = [int(n, 16) for n in (r, g, b)]
        return (r, g, b)
    
    def rgb_colour_to_html(self, r, g, b):
        """Convert a rgb triple to a hex colour"""
        def clamp(x): 
            return max(0, min(x, 255))
        return "#{0:02x}{1:02x}{2:02x}".format(clamp(r), clamp(g), clamp(b))


    def export_to_image_file(self, filename, scalar=10, transparent_palette_index=None):
        """
        Export the current image to a file
        """
        #Create blank image
        img = Image.new('RGBA', (len(self.pixels[1]), len(self.pixels[0])))
        d = ImageDraw.Draw(img)
        #Add each individual pixel to the image
        for xn, x in enumerate(self.pixels):
            for yn, y in enumerate(x):
                if y != transparent_palette_index:
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


class Animation():
    def __init__(self, frame_list):
        self.frames = frame_list
        self.current_frame = None

    def get_next_frame(self):
        if self.current_frame == None:
            self.current_frame = 0
        else:
            self.current_frame = (self.current_frame+1)% len(self.frames)
        return self.frames[self.current_frame]

    def export_as_gif(self, fname):
        images = []
        for filename in self.frames:
            images.append(imageio.imread(filename))
        imageio.mimsave(fname, images)


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
    for x in a.pixels:
        print(x)
    print()
    p = Pencil()
    for x in range(0,5):
        p.activate((x,3), a.pixels, 1)

    for x in a.pixels:
        print(x)

    print(p._get_neighbouring_locations((0,0), a.pixels))
    print(p._get_neighbouring_locations((1,1), a.pixels))
    print(p._get_neighbouring_locations((15,15), a.pixels))
    print(p._get_neighbouring_locations((1,15), a.pixels))

    b = Bucket()
    b.activate((2,0), a.pixels, 4)

    for x in a.pixels:
        print(x)


if __name__ == "__main__":
    main()