from django.db import models
from .utils import get_size, get_checksum, upload_image_to_azure
from .imageutils import ImageMagickWrapper, make_image_path
from django.conf import settings
from django.contrib.postgres.fields import JSONField
import uuid


# Create your models here.
class Asset(models.Model):
    identifier = models.UUIDField(primary_key=True, default=uuid.uuid4)
    file_path = models.CharField(max_length=200)
    file_size = models.IntegerField()  # Computed
    checksum = models.CharField(max_length=100)  # Computed
    created_date = models.DateTimeField(auto_now_add=True)  # Auto Generated

    class Meta:
        abstract = True


BACKUP_TYPES = [
    (0, 'AZURE')
]


class Backup(models.Model):
    # linked_asset = models.ForeignKey('MasterImage')
    backup_service = models.IntegerField(choices=BACKUP_TYPES)
    identifier = models.UUIDField(primary_key=True, default=uuid.uuid4)
    created_date = models.DateTimeField(auto_now_add=True)  # Auto Generated

    class Meta:
        abstract = True


class AzureBackup(Backup):
    PATH_PREFIX = "https://patarimedia.blob.core.windows.net/patari/"
    linked_asset = models.ForeignKey('MasterImage')
    derivatives = JSONField(default = [])

    @staticmethod
    def get_path(self):
        return "{}{}".format(AzureBackup.PATH_PREFIX, self.identifier)

    @staticmethod
    def make_backups(drop_backups=False, dry_run=True):
        if drop_backups:
            raise Exception("not Implemented")

        for master_image in MasterImage.objects.filter(azurebackup=None):
            pass_record = False
            temp_uuid = uuid.uuid4()

            if not upload_image_to_azure(temp_uuid, master_image.file_path, dry_run=dry_run):
                print("Error uploading to Azure")
                continue

            derivatives_json = []
            for derivative in DerivativeImage.objects.filter(parent=master_image):
                if not upload_image_to_azure(derivative.identifier, derivative.file_path, dry_run=dry_run):
                    print("Error uploading to Azure")
                    break
                derivatives_json.append(derivative.identifier)

            if pass_record:
                continue

            ab = AzureBackup(linked_asset=master_image, backup_service=0, identifier=temp_uuid,
                             derivatives=[str(x) for x in derivatives_json])
            ab.save()


IMAGE_TYPES = [
    (0, 'JPEG'),
    (1, 'PNG')
]


IMAGE_CLASSES = [
    (0, 'normal_tile'),
    (1, 'featured_tile')
]

IMAGE_CLASS_SIZES = [
    (0,'thumbnail'),
    (1,'tile_web'),
    (2,'tile_mobile_1x'),
    (3,'tile_mobile_2x'),
    (4,'tile_mobile_3x'),
]

IMAGE_CLASSES_QUALITY = [
    (0, 80),
    (1, 90)
]



IMAGE_CLASS_SIZES_REVERSE = dict([(x[1], x[0]) for x in IMAGE_CLASS_SIZES])


IMAGE_PROFILE_DATA = {  # Maybe in the future this can be parsed from a json file
    0: {0: {'width': 50,  'height': 50},
        1: {'width': 180, 'height': 180},
        2: {'width': 120, 'height': 120},
        3: {'width': 240, 'height': 240},
        4: {'width': 360, 'height': 360}},
    1: {1: {'width': 900, 'height': 200},
        2: {'width': 900, 'height': 200}}
}

class ImageAsset(Asset):
    width = models.IntegerField()
    height = models.IntegerField()
    image_type = models.IntegerField(choices=IMAGE_TYPES)

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
        image_object.image_type = matched_type_rec[0]
        return image_object

    def get_json(self, has_backup=False):
        return {
            'guid': str(self.identifier),
            'image_type': dict(IMAGE_TYPES)[self.image_type],
            'image_size': self.file_size,
            'checksum': self.checksum,
            'width': self.width,
            'height': self.height,
            'external_path': AzureBackup.get_path(self) if has_backup else None
        }


class DerivativeImage(ImageAsset):
    parent = models.ForeignKey('MasterImage')
    image_class_size = models.IntegerField(choices=IMAGE_CLASS_SIZES)

    @property
    def image_class(self):
        return self.parent.image_class

    def save(self, *args, **kwargs):
        dims = IMAGE_PROFILE_DATA[self.image_class][self.image_class_size]
        quality = IMAGE_CLASSES_QUALITY[self.image_class][1]
        parent_path = self.parent.file_path
        image_path = make_image_path(settings.DERIVATIVE_BASE_PATH)
        thumbnail_path = ImageMagickWrapper.create_thumbnail(parent_path, image_path, dims, quality)
        self.file_path = thumbnail_path
        ImageAsset.populate_image_fields(self)  # To get all the properties
        super(DerivativeImage, self).save()  # Save the super class

    def get_json(self, has_backup=False):
        ret_json = super(DerivativeImage, self).get_json(has_backup=has_backup)
        ret_json.update({
            'derivative_class_size': dict(IMAGE_CLASS_SIZES).get(self.image_class_size)
        })
        return ret_json


class MasterImage(ImageAsset):
    external_identifier = models.CharField(max_length=100, null=True)
    image_class = models.IntegerField(choices=IMAGE_CLASSES)

    def get_json(self, has_backup=False):
        has_backup = AzureBackup.objects.filter(linked_asset=self)

        ret_json = super(MasterImage, self).get_json(has_backup=has_backup)
        ret_json.update({
            'class': dict(IMAGE_CLASSES).get(self.image_class),
            'external_identifier': self.external_identifier,
            'derivatives': [derivative.get_json(has_backup=has_backup) for derivative in self.derivatives]
        })
        return ret_json

    @staticmethod
    def create_from_path(file_path, external_identifier, image_class):
        print(repr((file_path, external_identifier, image_class)))
        image = MasterImage(file_path=file_path)
        ImageAsset.populate_image_fields(image)
        image.external_identifier = external_identifier
        image.image_class = image_class
        image.save()
        image.create_derivatives()
        return image

    def create_derivatives(self):
        master_image = self
        image_class_sizes = IMAGE_PROFILE_DATA[master_image.image_class]
        print('PROFILE DATA', repr(image_class_sizes))

        derivatives = []
        for image_class_size in image_class_sizes:
            di = DerivativeImage(parent=master_image, image_class_size=image_class_size)
            di.save()
            derivatives.append(di)

        return derivatives

    @property
    def derivatives(self):
        return DerivativeImage.objects.filter(parent=self.identifier)


    def __str__(self):
        return "ID: {} ExternalID: {}".format(self.identifier, self.external_identifier)
