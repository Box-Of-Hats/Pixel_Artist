from Art import Art, Animation, Pencil, Bucket
from tkinter import *
from tkinter.colorchooser import *
from easygui import filesavebox, fileopenbox, ccbox
import imageio

#For image exporting
from PIL import Image, ImageDraw

class PixelArtApp(Frame):
    """Window"""
    def __init__(self, master=None):
        self.master = master
        self.art = Art(image_size=(16, 16))
        #self.art = Art.load_from_file("example_art.pxlart")

        #Options
        self.pen_colour = 0 #Default colour index to use
        self.colour_select_icon = "⊶"
        self.pixel_size = 20 #Size of pixels on the drawing canvas

        #Init variables
        self.last_export_filename = None

        #Init tools
        self.tools = [Pencil(), Bucket()]
        self.tool_icons = ["Pen", "Bkt"]

        #Init window
        self.init_window()
    
    def init_window(self):
        """Initialise the window"""
        self.master.title('Pixel Artist')
        #self.master.geometry('{}x{}'.format(220, 40))
        #self.master.resizable(0, 0)
        self.master.option_add('*tearOff', False)

        #Create menu bar
        self.menu_bar = Menu(self.master)
        self.master.config(menu=self.menu_bar)
        #Add File section to menu bar
        self.file_menu = Menu(self.menu_bar)
        self.file_menu.add_command(label='Save', command=None, accelerator='') #Add command
        self.file_menu.add_command(label='Save As...', command=self._save_to_file, accelerator='') #Add command
        self.file_menu.add_command(label='Export as PNG', command=self.export_as_image_file, accelerator='')
        self.file_menu.add_command(label='Export as last PNG (Overwrite {})'.format(self.last_export_filename), command= lambda: self.export_as_image_file(filename=self.last_export_filename), accelerator='', state="disabled")
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Load', command=self._load_art_from_file, accelerator='') 
        self.file_menu.add_command(label='Load Palette', command=lambda: self._load_palette_from_file(), accelerator='')
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Exit', command= quit, accelerator='') #Add command
        self.menu_bar.add_cascade(label='File', menu=self.file_menu)
        #Add Options section to menu bar
        options_menu = Menu(self.menu_bar)
        options_menu.add_command(label='Toggle gridlines', command=self._toggle_canvas_grid, accelerator='')
        options_menu.add_command(label='Zoom in', command=lambda: self._set_pixel_size(10), accelerator='Ctrl+')
        options_menu.add_command(label='Zoom out', command=lambda: self._set_pixel_size(-10), accelerator='Ctrl-')
        self.menu_bar.add_cascade(label='Options', menu=options_menu)

        #Split window into two frames
        self.left_frame = Frame(self.master, width=150, height=300, background="#DDDDFF")
        self.left_frame.grid(column=10, row=10)
        self.right_frame = Frame(self.master, width=300, height=300, background="#000000")
        self.right_frame.grid(column=20, row=10)

        #Create drawing canvas
        self.canvas_pixels = [[0 for x in range(len(self.art.pixels[0]))] for y in range(len(self.art.pixels[1]))]
        drawing_canvas_frame = Frame(self.right_frame)
        drawing_canvas_frame.grid(column=0, row=0, padx=10, pady=10)
        for i in range(len(self.art.pixels[1])):
            for j in range(len(self.art.pixels[0])):
                t = Frame(drawing_canvas_frame, height=self.pixel_size, width=self.pixel_size, bg=self.art.palette[0],)
                t.grid(column=j, row=i)
                #t.bind('<Button-1>', lambda event, i=i, j=j: self.set_pixel_colour(i, j, self.pen_colour))
                t.bind('<Button-1>', lambda event, i=i, j=j: self.activate_tool((j, i)))
                t.bind('<Button-3>', lambda event, i=i, j=j: self.change_pen_colour(self.art.pixels[i][j]))
                self.canvas_pixels[i][j] = t

        

        #Create palete buttons
        self.colour_buttons = []
        colour_buttons_container = Frame(self.left_frame)
        colour_buttons_container.grid(row=0, column=0, padx=10, pady=10)
        for colour_index, pc in enumerate([(c, self.art.palette[c]) for c in sorted(self.art.palette)]): #enumerate through the current palette
            #Create button object
            colour_button = Button(colour_buttons_container, width=2, height=1, relief="flat", background=self.art.palette[colour_index], highlightbackground="#000000")
            colour_button.grid(column=0, row=colour_index)
            #Bind events to colour button
            colour_button.bind("<Button-1>", lambda event, index=colour_index: self.change_pen_colour(index)) #Left-click = select as pen
            colour_button.bind("<Button-3>", lambda event, index=colour_index: self.change_palette_colour(index)) #Right-click=change palette colour
            self.master.bind("{}".format(colour_index+1), lambda event, index=colour_index: self.change_pen_colour(index)) #Number key press = select that colour as pen
            #Save the button in a list
            self.colour_buttons.append(colour_button)
        self.colour_buttons[self.pen_colour].config(text=self.colour_select_icon)

        #Create tool selection buttons
        self.selected_tool_id = IntVar(self.master)
        self.selected_tool_id.set(0)
        tool_buttons_container = Frame(self.left_frame)
        for i in range(0, len(self.tools)):
            b = Radiobutton(tool_buttons_container, value=i,
                text="{}".format(self.tool_icons[i]) , variable=self.selected_tool_id,)
            b.grid(row=0, column=i)
        tool_buttons_container.grid(row=5, column=0)

        #Keybindings
        #Zoom in (ctrl +)
        self.master.bind_all("<Control-equal>", lambda event: self._set_pixel_size(10))
        #Zoom out (ctrl -)
        self.master.bind_all("<Control-minus>", lambda event: self._set_pixel_size(-10))
        self.master.protocol('WM_DELETE_WINDOW', lambda: quit())


    def _toggle_canvas_grid(self):
        """Toggle the canvas gridlines"""
        for y, pixel_row in enumerate(self.canvas_pixels):
            for x, pixel in enumerate(pixel_row):
                toggled_thickness = (pixel.cget('highlightthickness') + 1) % 2
                pixel.config(highlightthickness=toggled_thickness)
    
    def _set_pixel_size(self, modifier_value):
        """Update size of pixels to be a new value"""
        self.pixel_size += modifier_value
        for y, pixel_row in enumerate(self.canvas_pixels):
            for x, pixel in enumerate(pixel_row):
                pixel.config(width=self.pixel_size)
                pixel.config(height=self.pixel_size)

    def _save_to_file(self):
        """Save current artwork/palette to a file"""
        filename = filesavebox(title="Save art to file", default="./*.pxlart")
        if filename:
            self.art.save_to_file(filename)

    def _load_palette_from_file(self):
        """Load a palette from a given file"""
        filename = fileopenbox(title="Load Palette", default="./*.pxlart")
        if filename:
            self.art.load_palette_from_file(filename)
            self.update_canvas()
            self.update_palette_buttons()

    def _load_art_from_file(self):
        """Load artwork from a given file"""
        filename = fileopenbox(title="Load Art", default="./*.pxlart")
        if filename and ccbox("Are you sure you want to load {}?\nYou will lose your current artwork".format(filename), "Load art from file?"):
            self.art = Art.load_from_file(filename)
            self.update_canvas()
            self.update_palette_buttons()

    def export_as_image_file(self, filename=False):
        """Export the current canvas to an image file"""
        if not filename:
            filename = filesavebox(title="Export art as png", default="./*.png")
        if filename:
            self.art.export_to_image_file(filename)
            self.last_export_filename = filename
            self.file_menu.entryconfig(3, label = "Export to... {}".format(self.last_export_filename))
            self.file_menu.entryconfig(3, state="normal")

    def change_pen_colour(self, colour_index):
        """
        Change the colour of the drawing pen.
        """
        self.pen_colour = colour_index
        for button in self.colour_buttons:
            button.config(text="")
        self.colour_buttons[colour_index].config(text=self.colour_select_icon)

    def change_palette_colour(self, colour_index):
        """
        Change the colour of one of the individual colours in the palette.
        """
        new_colour = askcolor()[1]
        if new_colour:
            self.art.palette[colour_index] = new_colour.strip()
            self.colour_buttons[colour_index].config(background=new_colour)
            self.change_pen_colour(colour_index)
            self.update_canvas()
        else:
            pass

    def update_canvas(self):
        """Update the drawing canvas so the correct colours are showing"""
        for y, pixel_row in enumerate(self.canvas_pixels):
            for x, pixel_button in enumerate(pixel_row):
                colour_index = self.art.pixels[y][x]
                colour = self.art.palette[colour_index]
                pixel_button.config(background=colour)
        print("updating canvas")

    def update_palette_buttons(self):
        """Update colour of palette buttons to be consistant with the art palette"""
        for colour_index, button in zip(self.art.palette, self.colour_buttons):
            button.config(background=self.art.palette[colour_index])

    def set_pixel_colour(self, x, y, colour_index):
        """Set the colour of an individual pixel on the drawing canvas"""
        self.art.set_pixel(x, y, colour_index)
        colour_value = self.art.palette[colour_index]
        self.canvas_pixels[x][y].config(background=colour_value)
    
    def activate_tool(self, location):
        t = self.tools[self.selected_tool_id.get()]
        print(t)
        t.activate(location, self.art.pixels, self.pen_colour)
        self.update_canvas()

def main():
    root = Tk()
    w = PixelArtApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()