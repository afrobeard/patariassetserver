from django.db import models
from .utils import get_size, get_checksum
from .imageutils import ImageMagickWrapper, make_image_path
from django.conf import settings
import uuid



# Create your models here.
class Asset(models.Model):
    identifier = models.UUIDField(primary_key=True, default=uuid.uuid4)
    file_path = models.CharField(max_length=100)
    file_size = models.IntegerField()  # Computed
    checksum = models.CharField(max_length=25)  # Computed
    created_date = models.DateTimeField(auto_now_add=True)  # Auto Generated

    class Meta:
        abstract = True


IMAGE_TYPES = [
    (0, 'JPEG'),
    (1, 'PNG')
]

IMAGE_CLASSES = [
    (0, 'media_banner'),
    (1, 'media_tile'),
    (2, 'nav_banner'),
]

IMAGE_CLASS_SIZES = [
    (0, 'small'),
    (1, 'medium'),
    (2, 'large'),
]

IMAGE_PROFILE_DATA = {  # Maybe in the future this can be parsed from a json file
    0: {1: {'width': 900, 'height': 200}},  # Media Banner
    2: {1: {'width': 1181, 'height': 220}},  # Nav Banner
    1: {0: {'width': 50, 'height': 50},
        1: {'width': 125, 'height': 125},
        2: {'width': 250, 'height': 250}}
}


class ImageAsset(Asset):
    width = models.IntegerField()
    height = models.IntegerField()
    type = models.IntegerField(choices=IMAGE_TYPES)

    class Meta:
        abstract = True

    @staticmethod
    def populate_image_fields(image_object):
        if not image_object.file_path:
            raise Exception("File Path Identifier is a mandatory field")

        image_object.file_size = get_size(image_object.file_path)
        image_object.checksum = get_checksum(image_object.file_path)
        properties_dict = ImageMagickWrapper.get_properties(image_object.file_path)
        image_object.width = properties_dict.get('width')
        image_object.height = properties_dict.get('height')

        matched_type_rec = [image_type_code for image_type_code, image_type in IMAGE_TYPES if image_type == properties_dict.get('format')]
        image_object.type = matched_type_rec[0]
        return image_object


class DerivativeImage(ImageAsset):
    parent = models.ForeignKey('MasterImage')
    image_class_size = models.IntegerField(choices=IMAGE_CLASS_SIZES)

    @property
    def image_class(self):
        return self.parent.image_class

    def save(self):
        dims = IMAGE_PROFILE_DATA[self.image_class][self.image_class_size]
        parent_path = self.parent.file_path
        image_path = make_image_path(settings.DERIVATIVE_BASE_PATH)
        ImageMagickWrapper.create_thumbnail(parent_path, image_path, dims)


class MasterImage(ImageAsset):
    external_identifier = models.CharField(max_length=100)
    image_class = models.IntegerField(choices=IMAGE_CLASSES)

    @staticmethod
    def create_from_path(file_path, external_identifier, image_class):
        image = MasterImage(file_path=file_path)
        ImageAsset.populate_image_fields(image)
        image.external_identifier = external_identifier
        image.image_class = image_class
        image.save()
        image.create_derivatives()

    def create_derivatives(self):
        master_image = self
        image_class_sizes = IMAGE_PROFILE_DATA[master_image.image_class]
        for image_class_size in image_class_sizes:
            di = DerivativeImage(parent=master_image, image_class_size=image_class_size)
            di.save()






