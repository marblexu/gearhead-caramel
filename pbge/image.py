# Load one image file, use it for multiple images.

import pygame
import weakref
import util
from . import my_state, render_text, TEXT_COLOR, Singleton
import os.path
import copy

# Try to import the caramelrecolor module. This requires caramelrecolor, numpy,
# and a recent enough version of pygame that has pixelcopy. If import fails,
# fall back to the original slow recoloring method.
try:
    import caramelrecolor
    import numpy
except ImportError:
    caramelrecolor = None
    print "Modules caramelrecolor+numpy not found; using slow recolor method."
if not hasattr(pygame,"pixelcopy"):
    print "Module caramelrecolor needs PyGame 1.9.2+; using slow recolor method."
    caramelrecolor = None

# Keep a list of already-loaded images, to save memory when multiple objects
# need to use the same image file.
pre_loaded_images = weakref.WeakValueDictionary()
search_path = list()


class Gradient(Singleton):
    NAME = 'Gradient'
    COLOR_RANGE = (0, 0, 0, 255, 255, 255)

    @classmethod
    def generate_color(cls, color_level):
        # The COLOR_RANGE is a tuple of six values: r g b at highest intensity,
        # and r g b at lowest intensity.
        color_level = max(color_level - 40, 0)
        r = max(min(((cls.COLOR_RANGE[0] - cls.COLOR_RANGE[3]) * color_level) / 215 + cls.COLOR_RANGE[3], 255), 0)
        g = max(min(((cls.COLOR_RANGE[1] - cls.COLOR_RANGE[4]) * color_level) / 215 + cls.COLOR_RANGE[4], 255), 0)
        b = max(min(((cls.COLOR_RANGE[2] - cls.COLOR_RANGE[5]) * color_level) / 215 + cls.COLOR_RANGE[5], 255), 0)
        return r, g, b


class Image(object):
    def __init__(self, fname=None, frame_width=0, frame_height=0, color=None, custom_frames=None,
                 flags=pygame.RLEACCEL):
        """Load image file, or create blank image, at frame size"""
        if fname:
            if (fname, repr(color)) in pre_loaded_images:
                self.bitmap = pre_loaded_images[(fname, repr(color))]
            else:
                if not os.path.exists(fname):
                    for p in search_path:
                        if os.path.exists(os.path.join(p, fname)):
                            fname = os.path.join(p, fname)
                            break
                self.bitmap = pygame.image.load(fname).convert()
                self.bitmap.set_colorkey((0, 0, 255), flags)
                if color:
                    self.recolor(color)
                self.record_pre_loaded(fname, color, self.bitmap)
        else:
            self.bitmap = pygame.Surface((frame_width, frame_height))
            self.bitmap.fill((0, 0, 255))
            self.bitmap.set_colorkey((0, 0, 255), flags)

        self.fname = fname

        if frame_width == 0:
            frame_width = self.bitmap.get_width()
        if frame_height == 0:
            frame_height = self.bitmap.get_height()

        if frame_width > self.bitmap.get_width():
            frame_width = self.bitmap.get_width()
        self.fname = fname
        self.frame_width = frame_width
        self.frame_height = frame_height

        self.custom_frames = custom_frames

    @staticmethod
    def record_pre_loaded(ident, colorset, bitmap):
        pre_loaded_images[(ident, repr(colorset))] = bitmap

    def render(self, dest=(0, 0), frame=0, dest_surface=None):
        # Render this Image onto the provided surface.
        # Start by determining the correct sub-area of the image.
        if self.custom_frames and frame < len(self.custom_frames):
            area = pygame.Rect(self.custom_frames[frame])
        else:
            frames_per_row = self.bitmap.get_width() / self.frame_width
            area_x = (frame % frames_per_row) * self.frame_width
            area_y = (frame / frames_per_row) * self.frame_height
            area = pygame.Rect(area_x, area_y, self.frame_width, self.frame_height)
        dest_surface = dest_surface or my_state.screen
        dest_surface.blit(self.bitmap, dest, area)

    def get_rect(self, frame):
        # Return a rect of the correct size for this frame.
        if self.custom_frames and frame < len(self.custom_frames):
            return pygame.Rect(0, 0, self.custom_frames[frame][2], self.custom_frames[frame][3])
        else:
            return pygame.Rect(0, 0, self.frame_width, self.frame_height)

    def num_frames(self):
        if self.custom_frames:
            return len(self.custom_frames)
        else:
            frames_per_row = self.bitmap.get_width() / self.frame_width
            frames_per_column = self.bitmap.get_height() / self.frame_height
            return frames_per_row * frames_per_column

    def recolor(self, color_channels):
        # Just gonna brute force this. It could probably be speeded up by using
        # a pixel array, but that would add dependencies. Besides- this should get
        # called just once, when the image is created, so speed isn't that
        # important.
        if caramelrecolor:
            dims = (self.bitmap.get_width(), self.bitmap.get_height())
            data = numpy.zeros(dims, numpy.uint32)
            pygame.pixelcopy.surface_to_array(data, self.bitmap)
            caramelrecolor.recolor(data, list(color_channels))
            pygame.pixelcopy.array_to_surface(self.bitmap, data)
        else:
            self.red_channel, self.yellow_channel, self.green_channel, self.cyan_channel, self.magenta_channel = color_channels
            self.bitmap.lock()
            par = pygame.PixelArray(self.bitmap)
            for y in range(self.bitmap.get_height()):
                for x in range(self.bitmap.get_width()):
                    c = self.bitmap.unmap_rgb(par[x,y])
                    if (c.r > 0) and (c.g == 0) and (c.b == 0):
                        par[x, y] = self.red_channel.generate_color(c.r)
                        # par[x,y] = self.generate_color(red_channel,c.r)
                    elif (c.r > 0) and (c.g > 0) and (c.b == 0):
                        par[x, y] = self.yellow_channel.generate_color(c.r)
                    elif (c.r > 0) and (c.g == 0) and (c.b > 0):
                        par[x, y] = self.magenta_channel.generate_color(c.r)
                    elif (c.r == 0) and (c.g > 0) and (c.b == 0):
                        par[x, y] = self.green_channel.generate_color(c.g)
                    elif (c.r == 0) and (c.g > 0) and (c.b > 0):
                        par[x, y] = self.cyan_channel.generate_color(c.g)
            del par
            self.bitmap.unlock()

    def __reduce__(self):
        # Rather than trying to save the bitmap image, just save the filename.
        return Image, (self.fname, self.frame_width, self.frame_height)

    def tile(self, dest=None, frame=0, dest_surface=None):
        dest_surface = dest_surface or my_state.screen
        if not dest:
            dest = my_state.screen.get_rect()
        grid_w = dest.w / self.frame_width + 2
        grid_h = dest.h / self.frame_height + 2
        dest_surface.set_clip(dest)
        my_rect = pygame.Rect(0, 0, 0, 0)

        for x in range(0, grid_w):
            my_rect.x = dest.x + x * self.frame_width
            for y in range(0, grid_h):
                my_rect.y = dest.y + y * self.frame_height
                self.render(my_rect, frame, dest_surface)

        dest_surface.set_clip(None)

    def copy(self,ident=None):
        nu_sprite = Image(frame_height=self.frame_height,frame_width=self.frame_width,)
        nu_sprite.bitmap = self.bitmap.copy()
        if ident:
            self.record_pre_loaded(ident, None, nu_sprite.bitmap)
        return nu_sprite

class TextImage(Image):
    def __init__(self, txt='?????', frame_width=128, color=None, font=None):
        """Create an image of the provided text"""
        if not font:
            font = my_state.anim_font
        if not color:
            color = TEXT_COLOR

        self.txt = txt
        self.bitmap = render_text(font, txt, frame_width, color, justify=0, antialias=False)
        self.frame_width = self.bitmap.get_width()
        self.frame_height = self.bitmap.get_height()
        self.custom_frames = None

    def __reduce__(self):
        # Rather than trying to save the bitmap image, just save the filename.
        return TextImage, (self.txt, self.frame_width, self.frame_height)


def init_image(def_image_folder):
    search_path.append(def_image_folder)
