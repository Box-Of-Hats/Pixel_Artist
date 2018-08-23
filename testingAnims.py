from tkinter import *
import imageio
root = Tk()


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


def advanceLabel(label, animation, delay):
    img_path = animation.get_next_frame()
    im = PhotoImage(file=img_path).zoom(3,3)

    label.config(image=im)
    label.image = im

    label.update()

    label.after(delay, lambda: advanceLabel(label,animation, delay))


a = Animation(["one.png", "two.png", "three.png", "four.png"])

a.export_as_gif("TESTGIF.gif")

my_label = Label(root)
my_label.pack()

root.after(500, lambda: advanceLabel(my_label, a, 500) )

root.geometry("{}x{}".format(300,300))
root.mainloop()