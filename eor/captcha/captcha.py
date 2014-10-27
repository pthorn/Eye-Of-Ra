# coding: utf-8

import logging
log = logging.getLogger(__name__)

import datetime
import os
import fnmatch
import random

from PIL import Image, ImageDraw, ImageFont, ImageOps
import StringIO

from sqlalchemy.orm.exc import NoResultFound

from pyramid.threadlocal import get_current_request

from eor.utils import app_conf

from .models import CaptchaEntity, CaptchaWord


class Captcha(object):
    
    def __init__(self, remote_addr, form_id=''):
        CaptchaEntity.delete_expired()

        try:
            CaptchaEntity.get(remote_addr, form_id).delete()
        except NoResultFound:
            pass

        self.captcha_entity = CaptchaEntity(
            remote_addr = remote_addr,
            form_id     = form_id,
            value       = CaptchaWord.get_random().word
        )
        self.captcha_entity.add(flush=True)

    @classmethod
    def validate(cls, remote_addr, form_id, value):
        try:
            return CaptchaEntity.get(remote_addr, form_id).validate(value)
        except NoResultFound:  # captcha expired
            return False

    def render(self):

        font_file = os.path.join(
             app_conf('captcha-font-path'),
             random.choice([font_file for font_file in os.listdir(app_conf('captcha-font-path')) if fnmatch.fnmatch(font_file, '*.ttf')]))
        font = ImageFont.truetype(font_file, app_conf('captcha-font-size'))

        text_color = random.choice([(190, 0, 0, 255), (37, 37, 37, 255), (0, 0, 127, 255)])

        size = font.getsize(self.captcha_entity.value)
        image = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.text((0, 0), self.captcha_entity.value, font=font, fill=text_color)

        # deform begin

        project = lambda orig, dist: orig + random.randint(-1 * dist, dist)
  
        divisions = int(len(self.captcha_entity.value) / 1.5)
        distorsion = dict(x=app_conf('captcha-distortion-x'), y=app_conf('captcha-distortion-y'))

        # add margins

        margin_img_size = (
            image.size[0] + (2 * distorsion['x']),
            image.size[1] + (2 * distorsion['y']),
        )
        margins_img = Image.new('RGBA', margin_img_size, (0, 0, 0, 0))
        margins_img.paste(image, (distorsion['x'], distorsion['y']))
        image = margins_img

        # calculate distortion mesh

        last_projected_x = last_projected_y = 0
        mesh = []
        for pos in xrange(divisions + 1):
            x0 = image.size[0] / divisions * pos
            x1 = image.size[0] / divisions * (pos + 1)
            y0 = 0
            y1 = image.size[1]
  
            projected_x = project(x1, distorsion['x'])
            projected_y = project(y0, distorsion['y'])
  
            mesh.append((
                (x0, y0, x1, y1),
                (
                    last_projected_x, last_projected_y,
                    x0, y1,
                    x1, y1,
                    projected_x, projected_y,
                ),
            ))
            last_projected_x, last_projected_y = projected_x, projected_y

        image = image.transform(image.size, Image.MESH, mesh, Image.BICUBIC)
        image = image.crop(image.getbbox())

        # deform end

        stringio = StringIO.StringIO()
        image.save(stringio, 'PNG') #, quality=100) # TODO png quality?
        return (stringio.getvalue(), 'image/png')


'''
def get_random_element_from_queryset(queryset):
    return queryset[random.randint(0, len(queryset) - 1)]
  
  
def get_random_word(length=10):
    import string
    result = [random.choice(string.lowercase) for char in xrange(length)]
    return ''.join(result)
  
  
def text_to_captcha_image_data(text):
    import ImageFont
    
    captcha = CaptchaImage(text, font)
    captcha.colorize_text(os.path.join(os.path.dirname(__file__), 'bg.png'))
    captcha.make_transparent_bg()
    captcha.deform_text()
    return (captcha.get_image('PNG'), 'image/png')


import Image, ImageDraw, ImageFont, ImageOps
from cStringIO import StringIO
  
BLACK = (0, 0, 0, 255)
TRANSPARENT = (0, 0, 0, 0)
  
  
class CaptchaImage:
  
    def __init__(self, text, font=ImageFont.load_default()):
        self.text = " " + text + " "
        size = font.getsize(self.text)
        self.img = Image.new('RGBA', size, BLACK)
        draw = ImageDraw.Draw(self.img)
        draw.text((0, 0), self.text, font=font, fill=TRANSPARENT)
        self.mask = self.img.split()[3]
  
    def deform_text(self):
        import random
        project = lambda orig, dist: orig + random.randint(-1 * dist, dist)
  
        divisions = len(self.text) / 2
        distorsion = dict(x=10, y=30)
        margin_img_size = (
            self.img.size[0] + (2 * distorsion['x']),
            self.img.size[1] + (2 * distorsion['y']),
        )
        margins_img = Image.new('RGBA', margin_img_size, TRANSPARENT)
        margins_img.paste(self.img, (distorsion['x'], distorsion['y']))
        self.img = margins_img
  
        last_projected_x = last_projected_y = 0
        mesh = []
        for pos in xrange(divisions+1):
            x0 = self.img.size[0] / divisions * pos
            x1 = self.img.size[0] / divisions * (pos + 1)
            y0 = 0
            y1 = self.img.size[1]
  
            projected_x = project(x1, distorsion['x'])
            projected_y = project(y0, distorsion['y'])
  
            mesh.append((
                (x0, y0, x1, y1),
                (
                    last_projected_x, last_projected_y,
                    x0, y1,
                    x1, y1,
                    projected_x, projected_y,
                ),
            ))
            last_projected_x, last_projected_y = projected_x, projected_y
  
        self.img = self.img.transform(self.img.size, Image.MESH, mesh, Image.BICUBIC)
        self.img = self.img.crop(self.img.getbbox())
  
    def colorize_text(self, color_file):
        col_img = Image.open(color_file, 'r')
        col_img = col_img.resize(self.img.size)
        self.img = Image.composite(self.img, col_img, mask=self.mask)
  
    def make_transparent_bg(self):
        transparent_img = Image.new('RGBA', self.img.size, TRANSPARENT)
        reverted_mask = ImageOps.invert(self.mask)
        self.img = Image.composite(self.img, transparent_img, mask=reverted_mask)
  
    def get_image(self, format='PNG'):
        result = StringIO()
        self.img.save(result, format)
        result.seek(0)
        return result.read()
'''
                