import shutil
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from .models import IMAGE_CLASSES, IMAGE_CLASS_SIZES_REVERSE, MasterImage, DerivativeImage
from .utils import make_error_obj_from_validation_error, get_random_string, upload_image_to_azure
from .imageutils import make_image_path
import patariassetserver.settings as settings


@csrf_exempt
def ingest_image(request):
    if request.method == "POST":
        image_path = request.META.get('HTTP_X_FILE_NAME')
        external_identifier = request.GET.get('external_identifier')

        if image_path is None:
            resp = JsonResponse({"error_message": "image path not coming through"})
            resp.status_code = 400
            return resp
        if external_identifier is None:
            resp = JsonResponse({"error_message": "external_identifier is required"})
            resp.status_code = 400
            return resp

        image_class = request.GET.get('class', 'normal_tile')
        image_class_int = dict([(x[1], x[0]) for x in IMAGE_CLASSES]).get(image_class)
        try:
            image_path_copy = make_image_path(settings.ORIGINAL_BASE_PATH)
            shutil.copyfile(image_path, image_path_copy)
            image = MasterImage.create_from_path(image_path_copy, external_identifier, image_class_int)
            res_obj = image.get_json()
            print("successfully uploaded for external_identifier:{} as a {}".format(external_identifier, image_class))
            return JsonResponse(res_obj)
        except Exception as e:
            from traceback import print_exc, print_stack
            from django.core.exceptions import ValidationError
            print("uploading for external_identifier:{} as a {} failed".format(external_identifier, image_class))
            print_stack()
            print_exc()
            if isinstance(e, ValidationError):
                resp = JsonResponse(make_error_obj_from_validation_error(e))
                resp.status_code = 400
            else:
                internal_error_message = e.message if hasattr(e, 'message') else str(e)
                resp = JsonResponse({"error_message": "Something went wrong.",
                                     "internal_error_message": internal_error_message})
                resp.status_code = 400
            return resp


@csrf_exempt
def get_asset_info(request, identifier):
    ext_id = request.path.startswith('/assets/e/')
    if not identifier:
        resp = JsonResponse({"error_message": "object_id not supplied"})
        resp.status_code = 400
        return resp

    if ext_id:
        image_rs = MasterImage.objects.filter(external_identifier=identifier)
    else:
        image_rs = MasterImage.objects.filter(identifier=identifier)

    if image_rs:
        image = image_rs.latest('created_date')
        return JsonResponse(image.get_json())
    else:
        resp = JsonResponse({"error_message": "Asset does not exist"})
        resp.status_code = 404
        return resp


@csrf_exempt
def get_derivative_info(request, identifier, size=None):
    ext_id = request.path.startswith('/assets/e/')
    size = size if size else "tile_web"

    if not identifier or size not in IMAGE_CLASS_SIZES_REVERSE.keys():
        resp = JsonResponse({"error_message": "object_id not supplied or invalid size"})
        resp.status_code = 400
        return resp

    if ext_id:
        image_rs = MasterImage.objects.filter(external_identifier=identifier)
    else:
        image_rs = MasterImage.objects.filter(identifier=identifier)

    if image_rs:
        master_image = image_rs.latest('created_date')
        derivative_image = DerivativeImage.objects.get(image_class_size=IMAGE_CLASS_SIZES_REVERSE[size],
                                                       parent=master_image.identifier)
        return JsonResponse(derivative_image.get_json())
    else:
        resp = JsonResponse({"error_message": "Asset does not exist"})
        resp.status_code = 404
        return resp


@csrf_exempt
def get_derivative(request, identifier, size=None, ):
    ext_id = request.path.startswith('/assets/e/')
    size = size if size else "tile_web"

    if ext_id:
        image_rs = MasterImage.objects.filter(external_identifier=identifier)
    else:
        image_rs = MasterImage.objects.filter(identifier=identifier)

    if not identifier or size not in IMAGE_CLASS_SIZES_REVERSE.keys():
        resp = JsonResponse({"error_message": "object_id not supplied or invalid size"})
        resp.status_code = 400
        return resp

    if image_rs:
        master_image = image_rs.latest('created_date')
        master_image = MasterImage.objects.filter(external_identifier=identifier).latest('created_date')
        derivative_image = DerivativeImage.objects.get(image_class_size=IMAGE_CLASS_SIZES_REVERSE[size],
                                                       parent=master_image.identifier)
    else:
        resp = JsonResponse({"error_message": "Asset does not exist"})
        resp.status_code = 404
        return resp

    response = HttpResponse(derivative_image.get_json(), status=200)
    file_path = derivative_image.file_path
    file_path_li = ['', 'media'] + file_path.split('/')[-4:]  # derivatives/2018/2/guid.jpeg
    response['Content-Type'] = 'image/jpeg'
    response['X-Accel-Redirect'] = "/".join(file_path_li)
    return response
