from Art import Art, Animation, Pencil, Bucket, PartialBucket, MirroredPencil
from tkinter import *
from tkinter.colorchooser import *
from easygui import filesavebox, fileopenbox, ccbox, enterbox
from PIL import Image, ImageDraw
import math
import random
import sys
import os
import colour

class PixelArtApp(Frame):
    """Window"""
    def __init__(self, master=None, art=None, canvas_size=(16,16)):
        super().__init__()
        self.master = master
        if art:
            self.art = art
        else:
            self.art = Art(image_size=canvas_size)
        
        #Options
        self.pen_colour = 0 #Default colour index to use
        self.colour_select_icon = "⏺"
        self.min_pixel_size = 10
        self.default_canvas_size = 284
        self.preview_image_scalar = (3,3) #The multiplier scale that the art preview image should display as
        self.zoom_change_amount = 1.25 #The amount of pixels to increase/decrease pixel size by
        self.tools_selection_per_row = 3
        self.art_history_length = 5
        self.show_debug_console = False
        self.max_log_length = 10
        self.left_bg_colour = "#baad82"
        self.right_bg_colour = "#d6cca9"

        #Init variables
        self.last_export_filename = None
        self.preview_image = PhotoImage(file="resources/default.png").zoom(*self.preview_image_scalar)
        self.art_history = []
        self.previous_file_save = False
        self.show_gridlines = False
        self.enable_drag = False
        self.pixel_size = self.default_canvas_size/len(self.art.pixels[0])

        #Init tools
        self.tools = [Pencil(), Bucket(), PartialBucket(),
                      MirroredPencil("x"), MirroredPencil("y"), MirroredPencil("xy")]
        self.tool_icons = ["resources/pen.png", "resources/bucket.png",
                           "resources/partialbucket.png", "resources/penX.png",
                           "resources/penY.png", "resources/penXY.png"]

        self.init_window()
    
    def init_window(self):
        """Initialise the window"""
        self.master.title('Pixel Artist')
        self.master.geometry('+{}+{}'.format(int(self.master.winfo_screenwidth()/2)-100, int(self.master.winfo_screenheight()/2)-200))
        self.master.resizable(0, 0)
        self.master.option_add('*tearOff', False)
        self.master.config(bg="#FF00FF")

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
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Clear Canvas', command=lambda: self.clear_canvas(ask_confirm=True), accelerator="Ctrl+Shift+D")
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Exit', command= quit, accelerator='')
        self.menu_bar.add_cascade(label='File', menu=self.file_menu)
        #Add Edit section to menu bar
        self.edit_menu = Menu(self.menu_bar)
        self.edit_menu.add_command(label='Undo', command=lambda:self.undo(), accelerator="Ctrl+Z")
        self.menu_bar.add_cascade(label='Edit', menu=self.edit_menu)
        #Add Palette section to menu bar
        self.palette_menu = Menu(self.menu_bar)
        self.palette_menu.add_command(label='Load from file', command=lambda: self.load_palette_from_file(), accelerator='')
        self.palette_menu.add_command(label='Load from URL', command=lambda: self.load_palette_from_url(), accelerator="")
        self.palette_menu.add_command(label='Random Palette', command=lambda: self.randomise_palette(), accelerator='Ctrl+Shift+R')
        self.palette_menu.add_separator()
        self.palette_menu.add_command(label='Sort Palette', command=lambda:self.sort_palette(), accelerator="")
        self.menu_bar.add_cascade(label='Palette', menu=self.palette_menu)
        #Add Options section to menu bar
        options_menu = Menu(self.menu_bar)
        options_menu.add_checkbutton(label='Gridlines', command=self._toggle_canvas_grid, accelerator='')
        options_menu.add_checkbutton(label='Toggle Drag', command=lambda: self.toggle_allow_drag(), accelerator='Ctrl+M')
        options_menu.add_command(label='Zoom in', command=lambda: self._set_pixel_size(self.zoom_change_amount), accelerator='Ctrl+')
        options_menu.add_command(label='Zoom out', command=lambda: self._set_pixel_size(-self.zoom_change_amount), accelerator='Ctrl-')
        options_menu.add_checkbutton(label='Show/Hide Debug Console', command=lambda: self.toggle_show_console(), accelerator='F12')
        self.menu_bar.add_cascade(label='Options', menu=options_menu)

        #Split window into two frames
        self.left_frame = Frame(self.master, width=150, height=300, background=self.left_bg_colour)
        self.left_frame.grid(column=10, row=10, sticky="ns")
        self.right_frame = Frame(self.master, width=300, height=300, background=self.right_bg_colour)
        self.right_frame.grid(column=20, row=10,sticky="nsew")

        #Create drawing canvas
        self.drawing_canvas_frame = Frame(self.right_frame)
        self.drawing_canvas_frame.grid(column=0, row=0, padx=10, pady=10)
        self.drawing_canvas = self._generate_drawing_canvas(self.drawing_canvas_frame)

        #Preview Label
        self.preview_label = Label(self.right_frame, image=self.preview_image)
        self.preview_label.grid(column=10, row=0)

        #Create palete buttons
        self.colour_buttons = []
        colour_buttons_container = Frame(self.left_frame)
        colour_buttons_container.grid(row=0, column=0, padx=10, pady=10)
        for colour_index, pc in enumerate([(c, self.art.palette[c]) for c in sorted(self.art.palette)]): #enumerate through the current palette
            #Create button object
            colour_button = Button(colour_buttons_container, width=2, height=1, bd=0,
                                    relief="flat", background=self.art.palette[colour_index],
                                    highlightbackground="#000000", fg="#000000", font=('Arial' , 8, 'bold'))
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
        tool_buttons_container = Frame(self.left_frame, bg=self.left_bg_colour)
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
                indicatoron=False, bd=3, relief="flat", offrelief="flat", bg=self.left_bg_colour, fg=self.left_bg_colour)
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
        #Enable/Disable mousedrag (Ctrl M)
        self.master.bind_all("<Control-m>", lambda event: self.toggle_allow_drag() )
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

    def load_palette_from_url(self, url=None):
        if not url:
            url = enterbox("Enter a URL", "Load from URL", strip=True)
        if url:
            if self.art.load_palette_from_url(url):
                self.log("Loading from URL: {}".format(url))
                self.update_palette_buttons()
                self.update_canvas()
            else:
                self.log("Unsupported URL: {}".format(url))

    def _generate_drawing_canvas(self, parent):
        """Generate a drawing canvas object"""
        self.canvas_pixels = [[0 for x in range(len(self.art.pixels[0]))] for y in range(len(self.art.pixels[1]))]
        drawing_canvas = Canvas(parent, width=len(self.art.pixels[0])*self.pixel_size, height=len(self.art.pixels[1])*self.pixel_size)
        drawing_canvas.grid(row=0, column=0)
        drawing_canvas.bind('<Button-1>', lambda e: self.activate_tool((math.floor(e.x/self.pixel_size), math.floor(e.y/self.pixel_size))))
        drawing_canvas.bind('<Button-3>', lambda e: self.change_pen_colour(self.art.pixels[math.floor(e.y/self.pixel_size)][math.floor(e.x/self.pixel_size)]))
        return drawing_canvas

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

    def toggle_allow_drag(self):
        """Toggle the ability to draw while dragging the mouse"""
        def button1_move(e):
            try:
                print(self.prev)
            except:
                self.prev = None
            cur = (math.floor(e.x/self.pixel_size), math.floor(e.y/self.pixel_size))
            if cur != self.prev:
                self.prev = cur
                self.activate_tool((math.floor(e.x/self.pixel_size), math.floor(e.y/self.pixel_size)),draw_all=False)
        
        self.enable_drag = not self.enable_drag

        if self.enable_drag:
            self.log("Enabling mouse drag")
            self.drawing_canvas.bind('<B1-Motion>', lambda e: button1_move(e))
        else:
            self.log("Disabling mouse drag")
            self.drawing_canvas.unbind("<B1-Motion>")

    def _toggle_canvas_grid(self):
        """Toggle the canvas gridlines"""
        self.show_gridlines = not self.show_gridlines
        if self.show_gridlines:
            self.log("Show Gridlines")
            for grid_index in range(0, len(self.art.pixels[0])):
                self.drawing_canvas.create_line(grid_index*self.pixel_size, 0,
                                                grid_index*self.pixel_size, self.pixel_size*len(self.art.pixels[0]),
                                                tags="gridline")
                self.drawing_canvas.create_line(0, grid_index*self.pixel_size, 
                                                self.pixel_size*len(self.art.pixels[0]), grid_index*self.pixel_size,
                                            tags="gridline")
        else:
            self.log("Hide Gridlines")
            self.drawing_canvas.delete("gridline")
    
    def _set_pixel_size(self, scale):
        """Update size of pixels to be a new value."""
        if scale < 0:
            #Zooming out
            scale = abs(scale)
            self.pixel_size = max(1, self.pixel_size / scale)
            self.drawing_canvas.config(height=self.pixel_size*len(self.art.pixels[0]),
                                    width=self.pixel_size*len(self.art.pixels[1]))
            self.drawing_canvas.scale(ALL, 0, 0, 1/scale, 1/scale)
        else:
            #Zooming in
            self.pixel_size = self.pixel_size * scale
            self.drawing_canvas.config(height=self.pixel_size*len(self.art.pixels[0]),
                                    width=self.pixel_size*len(self.art.pixels[1]))
            self.drawing_canvas.scale(ALL, 0, 0, scale, scale)

        self.update_window_size()
        self.log("Changing pixel size: {}".format(self.pixel_size))

    def sort_palette(self):
        self.art.sort_palette()
        self.update_palette_buttons()
        self.update_canvas()

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
            self.art.sort_palette()
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
            filename = fileopenbox(title="Load Palette", default="./palettes/*.pxlart")
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
            filename = fileopenbox(title="Load Art", default="./savedArt/*.pxlart")
        if filename and (ignore_warning or ccbox("Are you sure you want to load {}?\nYou will lose your current artwork".format(filename), "Load art from file?")):
            
            self.log("Loading from: {}".format(filename))
            self.art = Art.load_from_file(filename)

            self.drawing_canvas.destroy()
            self.drawing_canvas = self._generate_drawing_canvas(self.drawing_canvas_frame)

            self.update_canvas()
            self.update_palette_buttons()
            self.update_window_size()

    def export_as_image_file(self, filename=False):
        """Export the current canvas to an image file"""
        root = Toplevel(master=self)
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
            self.update_palette_buttons()
        else:
            pass

    def update_canvas(self, clear_canvas=True, selected_pixels=False):
        """
        Update the drawing canvas so the correct colours are showing.
        clear_canvas defines whether the canvas should be deleted.
        selected_pixels is a list of coordinates of pixels that
        should be updated. Updates all pixels by default
        """
        if clear_canvas:
            self.drawing_canvas.delete("rect")
        if not selected_pixels:
            for y, pixel_row in enumerate(self.canvas_pixels):
                for x, pixel_button in enumerate(pixel_row):
                    colour_index = self.art.pixels[y][x]
                    colour = self.art.palette[colour_index]

                    self.drawing_canvas.create_rectangle(x*self.pixel_size, y*self.pixel_size, x*self.pixel_size+self.pixel_size, y*self.pixel_size+self.pixel_size,
                                                        fill=colour, width=0, tags="rect")
        else:
            for pixel in selected_pixels:
                x = pixel[0]
                y = pixel[1]
                colour_index = self.art.pixels[y][x]
                colour = self.art.palette[colour_index]
                self.drawing_canvas.create_rectangle(x*self.pixel_size, y*self.pixel_size, x*self.pixel_size+self.pixel_size, y*self.pixel_size+self.pixel_size,
                                                        fill=colour, width=0, tags="rect")

        self.drawing_canvas.tag_raise("gridline")
        self.update_preview_image()
        self.log("Updating canvas...")

    def update_palette_buttons(self):
        """Update colour of palette buttons to be consistant with the art palette"""
        for colour_index, button in zip(self.art.palette, self.colour_buttons):
            this_colour = self.art.palette[colour_index]
            colour_obj = colour.Color(this_colour)
            colour_obj.green = 1-colour_obj.green
            colour_obj.red = 1-colour_obj.red
            colour_obj.blue = 1-colour_obj.blue
            colour_obj.set_saturation(0.99)
            text_colour = colour_obj.hex
            button.config(fg=text_colour)
            button.config(background=this_colour)

    def set_pixel_colour(self, x, y, colour_index):
        """Set the colour of an individual pixel on the drawing canvas"""
        self.art.set_pixel(x, y, colour_index)
        colour_value = self.art.palette[colour_index]
        self.canvas_pixels[x][y].config(background=colour_value)
    
    def activate_tool(self, location, draw_all=True):
        """
        Activate a the currently selected drawing tool at a given location.
        disabling draw_all means that only new pixels will be updated on the canvas"""
        #Add change to history
        self.art_history.append(self.art.copy())
        while len(self.art_history) >= self.art_history_length:
            self.art_history.remove(self.art_history[0])

        t = self.tools[self.selected_tool_id.get()]
        self.log("{} @ {}".format(type(t).__name__, location))
        try:
            t.activate(location, self.art.pixels, self.pen_colour)
        except IndexError:
            pass

        if draw_all:
            self.update_canvas()
        else:
            self.update_canvas(clear_canvas=False, selected_pixels=[(location)])
        
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
        """Output a string to the debug console"""
        print(output)
        self.output_console.insert(END, output)
        while self.output_console.size() > self.max_log_length:
            self.output_console.delete(0)
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
        """Toggle the display of the debug console"""
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
        self.master.grab_set()

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
    #Create required folders if they don't exist:
    for directory in ["./savedArt", "./exportedArt", "./palettes"]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print("creating directory: {}".format(directory))
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
    w = PixelArtApp(root, art_to_load, canvas_size)

    root.mainloop()

if __name__ == "__main__":
    main()
