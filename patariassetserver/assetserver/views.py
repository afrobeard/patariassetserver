from assetserver.models import IMAGE_CLASSES, IMAGE_CLASS_SIZES_REVERSE, MasterImage, DerivativeImage
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from assetserver.utils import make_error_obj_from_validation_error
from assetserver.imageutils import make_image_path
from patariassetserver import settings
from uuid import UUID
import shutil
from azure.storage.blob import BlockBlobService


@csrf_exempt
def ingest_image(request):
    if request.method == "POST":
        image_path = request.META.get('HTTP_X_FILE_NAME')
        external_identifier = request.GET.get('external_identifier')
        if image_path is None:
            resp = JsonResponse({"error_message": "image path not coming through"})
            resp.status_code = 400
            return resp
        image_class = request.GET.get('class', 'media_tile')
        image_class_int = dict([(x[1], x[0]) for x in IMAGE_CLASSES]).get(image_class)
        try:
            image_path_copy = make_image_path(settings.ORIGINAL_BASE_PATH)
            shutil.copyfile(image_path, image_path_copy)
            image = MasterImage.create_from_path(image_path_copy, external_identifier, image_class_int)
            return JsonResponse(image.get_json())
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
def get_asset_info(request, guid):
    if not guid:
        resp = JsonResponse({"error_message": "guid not supplied"})
        resp.status_code = 400
        return resp
    image = MasterImage.objects.get(identifier=UUID(guid))
    return JsonResponse(image.get_json())


@csrf_exempt
def get_derivative_info(request, guid, size=None):
    size = size if size else "medium"

    if not guid or size not in IMAGE_CLASS_SIZES_REVERSE.keys():
        resp = JsonResponse({"error_message": "guid not supplied or invalid size"})
        resp.status_code = 400
        return resp
    derivative_image = DerivativeImage.objects.get(image_class_size=IMAGE_CLASS_SIZES_REVERSE[size], parent=UUID(guid))
    return JsonResponse(derivative_image.get_json())


@csrf_exempt
def get_derivative(request, guid, size=None):
    size = size if size else "medium"

    if not guid or size not in IMAGE_CLASS_SIZES_REVERSE.keys():
        resp = JsonResponse({"error_message": "guid not supplied or invalid size"})
        resp.status_code = 400
        return resp
    derivative_image = DerivativeImage.objects.get(image_class_size=IMAGE_CLASS_SIZES_REVERSE[size], parent=UUID(guid))
    response = HttpResponse(derivative_image.get_json(), status=200)
    file_path = derivative_image.file_path
    file_path_li = ['', 'media'] + file_path.split('/')[-4:]  # derivatives/2018/2/guid.jpeg
    response['Content-Type'] = 'image/jpeg'
    response['X-Accel-Redirect'] = "/".join(file_path_li)
    return response


@csrf_exempt
def upload_to_azure(request):
    if request.method == "POST":
        image_path = request.META.get('HTTP_X_FILE_NAME')
        blob_name = request.GET.get('blob')

        if blob_name is None or image_path is None:
            resp = JsonResponse({"error_message": "Missing parameters"})
            resp.status_code = 400
            return resp

        block_blob_service = BlockBlobService(account_name=settings.AZURE_ACCOUNT_NAME,
                                              account_key=settings.AZURE_ACCOUNT_KEY)
        try:
            block_blob_service.create_blob_from_path(container_name=settings.AZURE_CONTAINER_NAME,
                                                     blob_name=blob_name,
                                                     file_path=image_path)
            response = JsonResponse({"message": "Success"})
            response.status_code = 200
        except Exception as e:
            print(e)
            response = JsonResponse({"message": "Something went wrong"})
            response.status_code = 500
        return response
    else:
        res = JsonResponse({"error_message": "Wrong Method"})
        res.status_code = 400
        return res
