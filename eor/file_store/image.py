# coding: utf-8

import logging
log = logging.getLogger(__name__)

import os
import math

from PIL import Image

#from ..utils import app_conf


def get_image_format(file_obj):
    ext = os.path.splitext(file_obj.filename)[1]
    if ext.lower() in('.gif', '.png'):
        return 'png'
    else:
        return 'jpg'


class Thumbnail(object):

    def __init__(self, size, quality, path, keep_proportions=False, original=False):
        self.size = size
        self.quality = quality
        self.path = path
        self.keep_proportions = keep_proportions
        self.original = original


def make_thumbnail(image, thumb_def):

    # TODO what if image is smaller than thumbnail?!

    if thumb_def.original:
        return image

    image = image.copy()

    if thumb_def.keep_proportions:

        # reduce if larger
        if image.size[0] > thumb_def.size[0] or image.size[1] > thumb_def.size[1]:
            image.thumbnail(thumb_def.size, Image.ANTIALIAS)

    else:

        # calculate crop window centered on image
        # TODO!!! won't work if original is smaller than thumbnail
        factor = min(float(image.size[0]) / thumb_def.size[0],  float(image.size[1]) / thumb_def.size[1])
        crop_size = (thumb_def.size[0] * factor, thumb_def.size[1] * factor)

        crop = (math.trunc((image.size[0] - crop_size[0]) / 2), math.trunc((image.size[1] - crop_size[1]) / 2),
                   math.trunc((image.size[0] + crop_size[0]) / 2), math.trunc((image.size[1] + crop_size[1]) / 2))

        #print '\n----------', 'image.size', image.size, 'thumb_def.size', thumb_def.size, 'factor', factor, 'crop_size', crop_size, 'crop', crop

        # crop and reduce
        image = image.crop(crop)
        image.thumbnail(thumb_def.size, Image.ANTIALIAS)

    return image


class NotAnImageException(Exception):
    pass


def save_uploaded_image(file_obj, thumbnails):
    """
    save uploaded image at save_path/image_id.type, make thumbnails if any

    TODO save with original filenames?

    :param file_obj:
    :param image_id:
    :return:
    """

    try:
        image = Image.open(file_obj.file)
    except IOError, e:
        e_str = str(e)
        if e_str.find('annot identify image file'):  # not an image
            raise NotAnImageException
        raise

    if image.mode != 'RGB':
        image.convert('RGB')

    # TODO
    def delete(filename):
        try:
            os.unlink(filename)
        except OSError:
            pass

    for thumb_def in thumbnails:
        make_thumbnail(image, thumb_def).save(thumb_def.path, quality=thumb_def.quality)

    file_obj.file.close() # needed?

#    except(IOError, OSError), err:
#        log.warn(u'image conversion error: %s' % unicode(err))
#        return False
