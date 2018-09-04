from Art import Art, Animation, Pencil, Bucket, PartialBucket, MirroredPencil
from tkinter import *
from tkinter.colorchooser import *
from easygui import filesavebox, fileopenbox, ccbox
import random
import sys
import os
#For exporting as .gifs
import imageio
#For image exporting
from PIL import Image, ImageDraw

class PixelArtApp(Frame):
    """Window"""
    def __init__(self, master=None, art=None, canvas_size=(16,16), pixel_size=20):
        super().__init__()
        self.master = master
        if art:
            self.art = art
        else:
            self.art = Art(image_size=canvas_size)
        
        #Options
        self.pen_colour = 0 #Default colour index to use
        self.colour_select_icon = "⊶"
        self.pixel_size = pixel_size #Size of pixels on the drawing canvas
        self.preview_image_scalar = (3,3) #The multiplier scale that the art preview image should display as
        self.zoom_change_amount = 10 #The amount of pixels to increase/decrease pixel size by
        self.tools_selection_per_row = 3
        self.art_history_length = 5
        self.show_debug_console = False

        #Init variables
        self.last_export_filename = None
        self.preview_image = PhotoImage(file="resources/default.png").zoom(*self.preview_image_scalar)
        self.art_history = []
        self.previous_file_save = False

        #Init tools
        self.tools = [Pencil(), Bucket(), PartialBucket(),
                      MirroredPencil("x"), MirroredPencil("y"), MirroredPencil("xy")]
        self.tool_icons = ["resources/pen.png", "resources/bucket.png",
                           "resources/partialbucket.png", "resources/penX.png",
                           "resources/penY.png", "resources/penXY.png"]

        #Init window
        self.init_window()
    
    def init_window(self):
        """Initialise the window"""
        self.master.title('Pixel Artist')
        #self.master.geometry('{}x{}'.format(220, 40))
        self.master.resizable(0, 0)
        self.master.option_add('*tearOff', False)

        #Create menu bar
        self.menu_bar = Menu(self.master)
        self.master.config(menu=self.menu_bar)
        #Add File section to menu bar
        self.file_menu = Menu(self.menu_bar)
        self.file_menu.add_command(label='Save', command=lambda: self._save_to_file(self.previous_file_save), accelerator='Ctrl+S') #Add command
        self.file_menu.add_command(label='Save As...', command=lambda: self._save_to_file(), accelerator='Ctrl+Shift+S')
        self.file_menu.add_command(label='Export as Image', command= self.export_as_image_file, accelerator='')
        self.file_menu.add_command(label='Export as last Image (Overwrite {})'.format(self.last_export_filename), command= lambda: self.export_as_image_file(filename=self.last_export_filename), accelerator='', state="disabled")
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Load', command=lambda: self.load_art_from_file(), accelerator='') 
        self.file_menu.add_command(label='Load Palette', command=lambda: self.load_palette_from_file(), accelerator='')
        self.file_menu.add_command(label='Random Palette', command=lambda: self.randomise_palette(), accelerator='Ctrl+Shift+R')
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Clear Canvas', command=lambda: self.clear_canvas(ask_confirm=True), accelerator="Ctrl+Shift+D")
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Exit', command= quit, accelerator='')
        self.menu_bar.add_cascade(label='File', menu=self.file_menu)
        #Add Edit section to menu bar
        self.edit_menu = Menu(self.menu_bar)
        self.edit_menu.add_command(label='Undo', command=lambda:self.undo(), accelerator="Ctrl+Z")
        self.menu_bar.add_cascade(label='Edit', menu=self.edit_menu)
        #Add Options section to menu bar
        options_menu = Menu(self.menu_bar)
        options_menu.add_command(label='Toggle gridlines', command=self._toggle_canvas_grid, accelerator='')
        options_menu.add_command(label='Zoom in', command=lambda: self._set_pixel_size(self.zoom_change_amount), accelerator='Ctrl+')
        options_menu.add_command(label='Zoom out', command=lambda: self._set_pixel_size(-self.zoom_change_amount), accelerator='Ctrl-')
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
                t.bind('<Button-1>', lambda event, i=i, j=j: self.activate_tool((j, i)))
                t.bind('<Button-3>', lambda event, i=i, j=j: self.change_pen_colour(self.art.pixels[i][j]))
                self.canvas_pixels[i][j] = t

        self.preview_label = Label(self.right_frame, image=self.preview_image)
        self.preview_label.grid(column=10, row=0)

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
        row_no = 0
        for i in range(0, len(self.tools)):
            if i%self.tools_selection_per_row == 0:
                row_no += 1
            try:
                img = PhotoImage(file=self.tool_icons[i])
            except TclError:
                img=None
            b = Radiobutton(tool_buttons_container, value=i,
                image=img, text="{}".format(self.tool_icons[i]) , variable=self.selected_tool_id,
                indicatoron=0, bd=0)
            b.img = img
            b.grid(row=row_no, column=i%self.tools_selection_per_row)
        tool_buttons_container.grid(row=5, column=0, padx=5, pady=5)

        self.bottom_frame = Frame(self.master)
        self.bottom_frame.grid(row=50, column=0, columnspan=100, sticky="nsew")
        self.output_console = Listbox(self.bottom_frame, height=4, width=30, borderwidth=0, highlightcolor="#000000",
                                        relief=FLAT, bg="#000000", fg="#FFFFFF")
        if self.show_debug_console:
            self.output_console.pack(expand=True, fill=BOTH)

        #Keybindings
        #Zoom in (ctrl +)
        self.master.bind_all("<Control-equal>", lambda event: self._set_pixel_size(self.zoom_change_amount))
        #Zoom out (ctrl -)
        self.master.bind_all("<Control-minus>", lambda event: self._set_pixel_size(-self.zoom_change_amount))
        #Save (ctrl S)
        self.master.bind_all("<Control-s>", lambda event: self._save_to_file(self.previous_file_save))
        #Save As (ctrl shift S)
        self.master.bind_all("<Control-S>", lambda event: self._save_to_file())
        #Clear canvas (ctrl shift d)
        self.master.bind_all("<Control-D>", lambda event: self.clear_canvas(ask_confirm=False))
        #Clear canvas (ctrl shift R)
        self.master.bind_all("<Control-R>", lambda event: self.randomise_palette(ask_confirm=False))
        #Undo (ctrl z)
        self.master.bind_all("<Control-z>", lambda event: self.undo())
        #Show/hide debug console (F12)
        self.master.bind_all("<F12>", lambda event: self.toggle_show_console())
        #On window resize
        self.master.after(100, lambda: self.master.bind("<Configure>", lambda event: self._on_window_resize(event)))
        #Quit program on window close
        self.master.protocol('WM_DELETE_WINDOW', lambda: quit())

        #Finally, ensure that the canvas is loaded properly
        # and that the art is in-sync.
        self.update_canvas()
        self.update_palette_buttons()

    def update_preview_image(self, size=(100,100)):
        """Draw the art preview image to the preview label."""
        self.art.export_to_image_file("resources/temp.png", scalar=1)
        self.preview_image = PhotoImage(file="resources/temp.png")
        x_scalar = 4#(size[0]/self.preview_image.width())
        y_scalar = 4#int(size[1]/self.preview_image.height())
        self.preview_image = self.preview_image.zoom(*self.preview_image_scalar)
        self.preview_label.config(image=self.preview_image)
        self.master.update()

    def clear_canvas(self, ask_confirm=True):
        """Clear the current canvas"""
        if ask_confirm:
            user_confirmed = ccbox("Are you sure you want to clear the canvas?")
        else:
            user_confirmed = True
        if user_confirmed:
            self.art = Art(self.art.palette, self.art.image_size, pixels=None)
            self.update_canvas()

    def _toggle_canvas_grid(self):
        """Toggle the canvas gridlines"""
        for y, pixel_row in enumerate(self.canvas_pixels):
            for x, pixel in enumerate(pixel_row):
                toggled_thickness = (pixel.cget('highlightthickness') + 1) % 2
                pixel.config(highlightthickness=toggled_thickness)
    
    def _set_pixel_size(self, modifier_value):
        """Update size of pixels to be a new value."""
        self.pixel_size += modifier_value
        #Ensure that pixel size is 1 or greater to prevent sizing issues
        self.pixel_size = max(1, self.pixel_size)
        for y, pixel_row in enumerate(self.canvas_pixels):
            for x, pixel in enumerate(pixel_row):
                pixel.config(width=self.pixel_size)
                pixel.config(height=self.pixel_size)
        self.update_window_size()

    def randomise_palette(self, ask_confirm=True):
        """Randomise the current palette"""
        if ask_confirm:
            confirmed = ccbox("Are you sure? You will lose your current palette", "Randomise Palette")
        else:
            confirmed = True
        if confirmed:
            for index in self.art.palette.keys():
                random_colour = self.art.rgb_colour_to_html(random.choice(range(0, 255)), random.choice(range(0, 255)), random.choice(range(0, 255)))
                self.art.palette[index] = random_colour
            self.update_canvas()
            self.update_palette_buttons()
            self.update_preview_image()

    def _save_to_file(self, filename=None):
        """Save current artwork/palette to a file"""
        if not filename:
            filename = filesavebox(title="Save art to file", default="./*.pxlart")
        if filename:
            self.log("Saving to: {}".format(filename))
            self.art.save_to_file(filename)
            self.previous_file_save = filename

    def load_palette_from_file(self, filename=None):
        """Load a palette from a given file"""
        if not filename:
            filename = fileopenbox(title="Load Palette", default="./*.pxlart")
        if filename:
            self.log("Loading from: {}".format(filename))
            self.art.load_palette_from_file(filename)
            self.update_canvas()
            self.update_palette_buttons()

    def load_art_from_file(self, filename=None, ignore_warning=False):
        """
        Load artwork from a given file.
        Note: Art must be same resolution as current canvas
        """
        if not filename:
            filename = fileopenbox(title="Load Art", default="./*.pxlart")
        if filename and (ignore_warning or ccbox("Are you sure you want to load {}?\nYou will lose your current artwork".format(filename), "Load art from file?")):
            self.log("Loading from: {}".format(filename))
            self.art = Art.load_from_file(filename)
            self.update_canvas()
            self.update_palette_buttons()

    def export_as_image_file(self, filename=False):
        """Export the current canvas to an image file"""
        root = Toplevel()
        root.title("Export as image...")
        SaveArtWindow(root, self.art)
        root.mainloop()

        """
        if not filename:
            filename = filesavebox(title="Export art as png", default="./*.png")
        if filename:
            self.art.export_to_image_file(filename)
            self.last_export_filename = filename
            self.file_menu.entryconfig(3, label = "Export to... {}".format(self.last_export_filename))
            self.file_menu.entryconfig(3, state="normal")
        """

    def change_pen_colour(self, colour_index):
        """
        Change the colour of the drawing pen.
        """
        self.pen_colour = colour_index
        for button in self.colour_buttons:
            button.config(text="")
        self.colour_buttons[colour_index].config(text=self.colour_select_icon)
        self.log("Set pen colour to: {}".format(colour_index))

    def change_palette_colour(self, colour_index):
        """
        Change the colour of one of the individual colours in the palette.
        """
        default_colour = self.art.palette[colour_index]
        new_colour = askcolor(default_colour)[1]
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
        self.update_preview_image()
        self.log("Updating canvas...")

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
        #Add change to history
        self.art_history.append(self.art.copy())
        while len(self.art_history) >= self.art_history_length:
            self.art_history.remove(self.art_history[0])

        t = self.tools[self.selected_tool_id.get()]
        self.log("{} @ {}".format(type(t).__name__, location))
        t.activate(location, self.art.pixels, self.pen_colour)
        self.update_canvas()
        
    def undo(self):
        """Return to the previous art state"""
        try:
            previous_state = self.art_history.pop()
            self.art = previous_state
            self.update_canvas()
            self.log("Undoing")
        except IndexError:
            self.log("Reached undo limit: {}".format(self.art_history_length))
    
    def log(self, output):
        print(output)
        self.output_console.insert(END, output)
        self.output_console.see(END)
    
    def _on_window_resize(self, event):
        """Window was resized"""
        pass

    def update_window_size(self, height_pad=0, width_pad=0):
        """Update the window size to fit to the widgets"""
        self.master.update()
        if self.show_debug_console:
            height_pad += self.output_console.winfo_height()
        w = self.right_frame.winfo_width() + self.left_frame.winfo_width() + width_pad
        h = height_pad + max(self.right_frame.winfo_height(), self.left_frame.winfo_height())
        self.master.geometry("{}x{}".format(w, h))

    def toggle_show_console(self):
        self.show_debug_console = not self.show_debug_console
        if self.show_debug_console:
            self.log("Show console")
            self.output_console.pack(expand=True, fill=BOTH)
        else:
            self.log("Hide console")
            self.output_console.pack_forget()
        self.update_window_size()

class SaveArtWindow(Toplevel):
    def __init__(self, master, art):
        self.master = master
        self.main_frame = Frame(master)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20)
        self.art = art

        self.preview_image = PhotoImage(file="resources/temp.png").zoom(6)
        
        self.preview_label = Label(self.main_frame, image=self.preview_image)
        self.preview_label.grid(row=30, column=0)

        self.master.update()

        self.scale_input = Scale(self.main_frame, from_=1, to=100, length=200, orient=HORIZONTAL, command= lambda e:self._update_preview_image())
        self.scale_input.grid(row=5, column=0, sticky="nw")
        self.scale_input.set(20)

        self.white_as_transparent = IntVar()
        self.white_as_transparent_btn = Checkbutton(self.main_frame, text="White as transparent", variable=self.white_as_transparent)
        self.white_as_transparent_btn.grid(row=10, column=0, sticky="nw")

        image_format_container = Frame(self.main_frame)
        self.image_format = StringVar()
        self.image_format_select = Listbox(image_format_container, height=1)
        self.image_format_select.insert(0, "JPG")
        self.image_format_select.insert(0, "PNG")
        self.image_format_select.grid(row=0, column=1)
        Label(image_format_container, text="Format").grid(row=0, column=0)
        image_format_container.grid(row=12, column=0, sticky="nw")


        self.file_select_button = Button(self.main_frame, text="Save", command=lambda: self.save_art())
        self.file_select_button.grid(row=20, column=0, sticky="nw")

    def save_art(self):
        scale = int(self.scale_input.get())
        image_format = self.image_format.get()

        filename = filesavebox(title="Export art...", default="./*.png")
        if filename:
            if self.white_as_transparent.get() == 1:
                transparent_option = 0
            else:
                transparent_option = None

            self.art.export_to_image_file(filename, scale, transparent_option)
            self.master.destroy()
            #self.last_export_filename = filename
            #self.file_menu.entryconfig(3, label = "Export to... {}".format(self.last_export_filename))
            #self.file_menu.entryconfig(3, state="normal")
    
    def _update_preview_image(self):
        scale = int(self.scale_input.get())
        print("Updating preview {}".format(scale))
        self.preview_image = PhotoImage(file="resources/temp.png").zoom(scale)
        self.preview_label.config(image=self.preview_image)



def main():
    art_to_load = None
    canvas_size = (8, 8)
    try:
        if os.path.splitext(sys.argv[1])[1] == ".pxlart":
            try:
                art_to_load = Art.load_from_file(sys.argv[1])
            except FileNotFoundError:
                print("Could not find file: {}".format(sys.argv[1]))
        else:
            try:
                canvas_size = (int(sys.argv[1]), int(sys.argv[1]))
            except ValueError:
                print("Using default canvas size")

    except ValueError:
        print("Using default canvas size")
    
    except IndexError:
        print("No args provided. Using default canvas size.")

    root = Tk()
    w = PixelArtApp(root, art_to_load, canvas_size, pixel_size=10)

    root.mainloop()

if __name__ == "__main__":
    main()
