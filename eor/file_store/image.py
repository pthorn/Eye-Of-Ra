# coding: utf-8

from __future__ import unicode_literals

import logging
log = logging.getLogger(__name__)

import os
import errno
import math

from PIL import Image

from .config import ImageSpec, Original, Thumbnail


class NotAnImageException(Exception):
    pass


def get_image_format(file_obj):
    ext = os.path.splitext(file_obj.filename)[1]
    if ext.lower() in('.gif', '.png'):
        return 'png'
    else:
        return 'jpg'


def make_thumbnail(image, variant_spec):

    # TODO what if image is smaller than thumbnail?!

    if isinstance(variant_spec, Original):
        return image

    assert isinstance(variant_spec, Thumbnail)

    image = image.copy()

    if variant_spec.exact_size:

        # calculate crop window centered on image
        # TODO!!! won't work if original is smaller than thumbnail
        factor = min(float(image.size[0]) / variant_spec.size[0],  float(image.size[1]) / variant_spec.size[1])
        crop_size = (variant_spec.size[0] * factor, variant_spec.size[1] * factor)

        crop = (math.trunc((image.size[0] - crop_size[0]) / 2), math.trunc((image.size[1] - crop_size[1]) / 2),
                   math.trunc((image.size[0] + crop_size[0]) / 2), math.trunc((image.size[1] + crop_size[1]) / 2))

        #print '\n----------', 'image.size', image.size, 'thumb_def.size', thumb_def.size, 'factor', factor, 'crop_size', crop_size, 'crop', crop

        # crop and reduce
        image = image.crop(crop)
        image.thumbnail(variant_spec.size, Image.ANTIALIAS)

    else:
        # reduce if larger
        if image.size[0] > variant_spec.size[0] or image.size[1] > variant_spec.size[1]:
            image.thumbnail(variant_spec.size, Image.ANTIALIAS)

    return image


def save_uploaded_image(file_obj, model_obj):
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
        if e_str.find('annot identify image file'):
            raise NotAnImageException
        raise

    if image.mode != 'RGB':
        image.convert('RGB')

    for var_name, var_spec in model_obj.variants.iteritems():
        save_path = model_obj.get_path(var_name)
        if os.path.exists(save_path):
            log.warn('overwriting existing image: %s', save_path)

        save_dir = os.path.dirname(save_path)
        if not os.path.exists(save_dir):
            log.warn('save_uploaded_image(): creating directory %s', save_dir)
            try:
                os.makedirs(save_dir)
            except OSError as e:
                # this can still happen if multiple images are uploaded concurrently
                if e.errno == errno.EEXIST:
                    pass
                else:
                    raise

        # TODO save original file for original image?
        make_thumbnail(image, var_spec)\
            .save(save_path, quality=var_spec.quality)

    file_obj.file.close()
