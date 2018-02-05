from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from assetserver.models import IMAGE_CLASSES, MasterImage
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from assetserver.utils import make_error_obj_from_validation_error


@csrf_exempt
def ingest_image(request):
    if request.method == "POST":
        image_path = request.META.get('HTTP_X_FILE_NAME')
        external_identifier = request.GET.get('external_identifier')
        if image_path is None:
            return JsonResponse({"nofile": True})
        image_class = request.GET.get('class', 'media_tile')
        image_class_int = dict([(x[1], x[0]) for x in IMAGE_CLASSES]).get(image_class)
        try:
            pass  # TODO Needs to create a copy of this instead of letting it live in tmp
            image = MasterImage.create_from_path(image_path, external_identifier, image_class_int)
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
