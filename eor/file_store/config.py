# coding: utf-8


class ImageSpec(object):
    pass


class Original(ImageSpec):
    pass


class Thumbnail(ImageSpec):

    def __init__(self, size, quality, exact_size=False):
        super(Thumbnail, self).__init__()
        self.size = size
        self.quality = quality
        self.exact_size = exact_size
