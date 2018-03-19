from assetserver.models import IMAGE_CLASSES, IMAGE_CLASS_SIZES_REVERSE, MasterImage, DerivativeImage
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from assetserver.utils import make_error_obj_from_validation_error, get_random_string, upload_image_to_azure
from assetserver.imageutils import make_image_path
from patariassetserver import settings
from uuid import UUID
import shutil


@csrf_exempt
def ingest_image(request):
    if request.method == "POST":
        image_path = request.META.get('HTTP_X_FILE_NAME')
        external_identifier = request.GET.get('external_identifier')
        upload_to_azure = request.GET.get('upload_to_azure')

        if image_path is None:
            resp = JsonResponse({"error_message": "image path not coming through"})
            resp.status_code = 400
            return resp
        if external_identifier is None:
            resp = JsonResponse({"error_message": "external_identifier is required"})
            resp.status_code = 400
            return resp

        if upload_to_azure is None:
            resp = JsonResponse({"error_message": "upload_to_azure is required"})
            resp.status_code = 400
            return resp

        image_class = request.GET.get('class', 'normal_tile')
        image_class_int = dict([(x[1], x[0]) for x in IMAGE_CLASSES]).get(image_class)
        try:
            image_path_copy = make_image_path(settings.ORIGINAL_BASE_PATH)
            shutil.copyfile(image_path, image_path_copy)
            image = MasterImage.create_from_path(image_path_copy, external_identifier, image_class_int)

            res_obj = image.get_json()

            if upload_to_azure == 'true':

                # copy files over (tile and thumb)

                azure_upload_path = settings.AZURE_UPLOAD_PATH
                azure_tile_image_path = image.derivatives[IMAGE_CLASS_SIZES_REVERSE.get('tile_mobile_3x')].file_path
                azure_thumbnail_path = image.derivatives[IMAGE_CLASS_SIZES_REVERSE.get('thumbnail')].file_path

                a_thumb_file_name = get_random_string() + '.jpg'
                a_tile_file_name = get_random_string() + '.jpg'

                a_thumb_path = azure_upload_path + '/' + a_thumb_file_name
                a_tile_path = azure_upload_path + '/' + a_tile_file_name

                shutil.copyfile(azure_tile_image_path, a_tile_path)
                shutil.copyfile(azure_thumbnail_path, a_thumb_path)

                # upload files to azure
                first_uploaded = upload_image_to_azure(a_thumb_file_name, a_thumb_path)
                second_uploaded = upload_image_to_azure(a_tile_file_name, a_tile_path)

                if not first_uploaded or not second_uploaded:
                    resp = JsonResponse({"error_message": "upload to azure failed, try again"})
                    resp.status_code = 500
                    return resp

                uploaded_to_azure = {'tile': a_tile_file_name, 'thumb': a_thumb_file_name}
                res_obj['uploaded_to_azure'] = uploaded_to_azure

            return JsonResponse(res_obj)
        except Exception as e:
            from traceback import print_exc, print_stack
            from django.core.exceptions import ValidationError
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
def get_asset_info(request, object_id):
    if not object_id:
        resp = JsonResponse({"error_message": "object_id not supplied"})
        resp.status_code = 400
        return resp
    image = MasterImage.objects.filter(external_identifier=object_id).latest('created_date')
    return JsonResponse(image.get_json())


@csrf_exempt
def get_derivative_info(request, object_id, size=None):
    size = size if size else "tile_web"

    if not object_id or size not in IMAGE_CLASS_SIZES_REVERSE.keys():
        resp = JsonResponse({"error_message": "object_id not supplied or invalid size"})
        resp.status_code = 400
        return resp

    try:
        master_image = MasterImage.objects.filter(external_identifier=object_id).latest('created_date')
        derivative_image = DerivativeImage.objects.get(image_class_size=IMAGE_CLASS_SIZES_REVERSE[size],
                                                       parent=master_image.identifier)
    except Exception as e:
        resp = JsonResponse({"error_message": "asset not found"})
        resp.status_code = 404
        return resp

    return JsonResponse(derivative_image.get_json())


@csrf_exempt
def get_asset_from_objectid(request):
    pass


@csrf_exempt
def get_derivative(request, object_id, size=None):
    size = size if size else "tile_web"

    if not object_id or size not in IMAGE_CLASS_SIZES_REVERSE.keys():
        resp = JsonResponse({"error_message": "object_id not supplied or invalid size"})
        resp.status_code = 400
        return resp

    try:
        master_image = MasterImage.objects.filter(external_identifier=object_id).latest('created_date')
        derivative_image = DerivativeImage.objects.get(image_class_size=IMAGE_CLASS_SIZES_REVERSE[size],
                                                       parent=master_image.identifier)
    except Exception as e:
        resp = JsonResponse({"error_message": "asset not found"})
        resp.status_code = 404
        return resp

    response = HttpResponse(derivative_image.get_json(), status=200)
    file_path = derivative_image.file_path
    file_path_li = ['', 'media'] + file_path.split('/')[-4:]  # derivatives/2018/2/guid.jpeg
    response['Content-Type'] = 'image/jpeg'
    response['X-Accel-Redirect'] = "/".join(file_path_li)
    return response
