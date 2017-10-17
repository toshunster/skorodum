from django.db.models.fields.files import ImageField, ImageFieldFile
from django.core.files.storage import FileSystemStorage 
from django.conf import settings

import os
from hashlib import md5
import math

from PIL import Image

class MyFileSystemStorage(FileSystemStorage):
    def get_available_name(self, name):
        if self.exists(name):
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return name


def _add_thumb(s):
  
  img_format = s.split(".")[-1]
  parts = s.split("/")
  parts[-1] =  md5(parts[-1]).hexdigest() + "." + img_format
  s = "/".join(parts)
  parts = s.split(".")
  parts.insert(-1, "thumb")
  if parts[-1].lower() not in ["jpeg", "jpg"]:
    parts[-1] = img_format
  return ".".join(parts)

def _add_small_thumb(s):
  img_format = s.split(".")[-1]
  parts = s.split("/")
  parts[-1] =  md5(parts[-1]).hexdigest() + "." + img_format
  s = "/".join(parts)
  parts = s.split(".")
  parts.insert(-1, "small_thumb")
  if parts[-1].lower() not in ["jpeg", "jpg"]:
    parts[-1] = img_format
  return ".".join(parts)
    
class ThumbnailImageFieldFile(ImageFieldFile):
  
  def _get_thumb_path(self):
    return _add_thumb(self.path)
  thumb_path = property(_get_thumb_path)

  def _get_small_thumb_path(self):
    return _add_small_thumb(self.path)
  small_thumb_path = property(_get_small_thumb_path)  
  
  def _get_thumb_url(self):
    return _add_thumb(self.url)
  thumb_url = property(_get_thumb_url)
  
  def _get_small_thumb_url(self):
    return _add_small_thumb(self.url)
  small_thumb_url = property(_get_small_thumb_url)
  
  def _get_thumb_name(self):
    return _add_thumb(self.name)
  thumb_name = property(_get_thumb_name)
  
  def _get_small_thumb_name(self):
    return _add_small_thumb(self.name)
  small_thumb_name = property(_get_small_thumb_name)
  
  def _get_orig_name(self):
    return self.name
  orig_name = property(_get_orig_name)
  
  def _get_thumb_width(self):
    return self.field.thumb_width
  thumb_width = property(_get_thumb_width)
  
  def _get_small_thumb_width(self):
    return self.field.small_thumb_width
  small_thumb_width = property(_get_small_thumb_width)
  
  def _get_thumb_height(self):
    img = Image.open(self.path)
    delta = self.field.thumb_width * img.size[1] / img.size[0]
    return int(delta)
  thumb_height = property(_get_thumb_height)
  
  def _get_small_thumb_height(self):
    img = Image.open(self.path)
    delta = self.field.small_thumb_width * img.size[1] / img.size[0]
    return int(delta)
  small_thumb_height = property(_get_small_thumb_height)
  
  def save(self, name, content, save=True):
    super(ThumbnailImageFieldFile, self).save(name, content, save)
    img = Image.open(self.path)
    img_format = self.path.split(".")[-1].upper()
    if len(img_format) != 3 or img_format == 'JPG':
      img_format = 'JPEG'
    img.convert('RGBA')
    #img.thumbnail(
    #    (self.field.thumb_width, self.field.thumb_height),
    #    Image.ANTIALIAS
    #)
    delta_small = int(self.field.small_thumb_width * img.size[1] // img.size[0])
    img_small = img.resize((int(self.field.small_thumb_width), int(math.floor(delta_small))), Image.ANTIALIAS)
    self.field.small_thumb_width_ = img_small.size[0]
    self.field.small_thumb_height_ = img_small.size[1]
    png_small_info = img_small.info
    img_small.save(self.small_thumb_path, **png_small_info)
    
    delta = int(self.field.thumb_width * img.size[1] / img.size[0])
    img = img.resize((int(self.field.thumb_width), int(math.floor(delta))), Image.ANTIALIAS)
    self.field.thumb_width_ = img.size[0]
    self.field.thumb_height_ = img.size[1]
    png_info = img.info
    img.save(self.thumb_path, **png_info)
    
  def delete(self, save=True):
    if os.path.exists(self.thumb_path):
      os.remove(self.thumb_path)
    super(ThumbnailImageFieldFile, self).delete(save)

class ThumbnailImageField(ImageField):
  attr_class = ThumbnailImageFieldFile
  
  def __init__(self, thumb_width=500, thumb_height=300, small_thumb_width=100, small_thumb_height=100, *args, **kwargs):
    
    self.thumb_width = thumb_width
    self.thumb_height = thumb_height
    self.thumb_width_ = thumb_width
    self.thumb_height_ = thumb_height
    self.small_thumb_width = small_thumb_width 
    self.small_thumb_height = small_thumb_height
    super(ThumbnailImageField, self).__init__(*args, **kwargs)
