import subprocess
import uuid
import datetime
import pathlib


def execute_cmd(cmd):
    return subprocess.getoutput(cmd)


def make_image_path(base_path, ext='jpeg', guid=None):
    d = datetime.datetime.now()
    date_path = '{}/{}'.format(d.year, d.month)
    guid = guid if guid else str(uuid.uuid4())
    file_name = guid + '.' + ext
    full_base_path = "{}/{}/".format(base_path, date_path)
    pathlib.Path(full_base_path).mkdir(parents=True, exist_ok=True)
    return "{}{}".format(full_base_path, file_name)


class ImageMagickWrapper(object):
    @staticmethod
    def get_properties(file_path):
        cmd = 'identify -format "%m %G %x %y" {}'.format(file_path)
        output = execute_cmd(cmd)
        (format_str, dim_str, xdensity, ydensity) = output.split(' ')
        (width, height) = dim_str.split('x')

        d = {
            'width': int(width),
            'height': int(height),
            'format': format_str,
            'xdensity': int(xdensity),
            'ydensity': int(ydensity),
        }
        d['density'] = d['xdensity'] if d['xdensity'] < d['ydensity'] else d['ydensity']
        return d

    @staticmethod
    def create_thumbnail(input_path, output_path, dimensions,
                         quality=80,
                         density=None):
        """
        
        :param input_path: 
        :param output_path: 
        :param dimensions: Like {'width': 125, 'height': 125}
        :param density: None for omit else int density to resample
        :return: 
        """
        input_props = ImageMagickWrapper.get_properties(input_path)
        print(repr(input_props))
        if not (dimensions.get('width') < input_props.get('width') and \
            dimensions.get('height') < input_props.get('height')):
            raise Exception('Can Only Downscale. Your Original image is too small')

        args = [
            '-strip', '-interlace Plane',
            '-quality {}'.format(quality),
            '-verbose',
            '-resize {}x{}'.format(dimensions.get('width'), dimensions.get('height'))
        ]
        if density:
            if not density < input_props['density']:
                raise Exception('Original image density too small')
            args.append('-resample {}x{}'.format(density, density))

        cmd = 'convert {} {} {}'.format(" ".join(args),
                                        input_path,
                                        output_path)
        output = execute_cmd(cmd)
        if output_path in output:
            return output_path
        print(output)
        raise Exception("Error during conversion")


if __name__ == "__main__":
    #print(make_image_path('/Users/afrobeard/Scratch/assets/derivatives'))
    """
    ImageMagickWrapper.create_thumbnail('/usr/share/doc/ntp/pic/stack1a.jpg',
                                        '/Users/afrobeard/monkeyman.jpg',
                                        {'width': 50, 'height': 50}, density=10)
    """

    #from assetserver.models import *;
    #MasterImage.create_from_path('/Users/afrobeard/Downloads/20170819_153318.jpg', 'bozo', 1)
