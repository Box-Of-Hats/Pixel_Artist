from Art import Art
import argparse
from lxml import html
import requests
import sys



def main():
    art = Art(image_size=(8,8))
    for y in range(0,8):
        for x in range(0,8):
            art.set_pixel(x,y,y)

    if sys.argv[1].lower() == "savepalettefromlist":
        """
        Save these palette values to a .pxlart file.
        Usage:
        python3 ArtTools.py savePalette OUTPUT_FILENAME LIST_OF_HEX_COLOURS
        e.g:
        python3 ArtTools.py savePalette "test.pxlart" "#170900,#BB00FF,#E87B74,#E8C658,#836FAA,#170900,#BB00FF,#E87B74"
        """
        filepath = sys.argv[2]
        palette_colours =  [c.strip() for c in sys.argv[3].split(",")]
        for index, colour in enumerate(palette_colours):
            art.palette[index] = colour
        art.sort_palette()
        art.save_to_file(filepath)

        quit()
    elif sys.argv[1].lower() == "purl":
        """
        Get a palette from a colourlovers url.
        """
        filepath = sys.argv[2]
        url = sys.argv[3]

       
        r = requests.get(url)
        tree = html.fromstring(r.content)

        theme_input = tree.xpath('/html/body/div[3]/div/div[2]/div[3]/input[2]')
        palette_colours = [c.strip() for c in theme_input[0].value.split(",")]
        for index, colour in enumerate(palette_colours):
            art.palette[index] = colour
        print("Saving to: {}".format(filepath))
        art.sort_palette()
        art.save_to_file(filepath)
    else:
        print("No commands found.")
        print(sys.argv)



if __name__ == "__main__":
    main()