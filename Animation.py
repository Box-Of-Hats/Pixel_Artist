import imageio
import Art

class Animation():
    def __init__(self, frame_list):
        """
        frame_list is a list of filepaths to images
        """
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
        
        for frame in self.frames:
            images.append(imageio.imread(frame))

        imageio.mimsave(fname, images)