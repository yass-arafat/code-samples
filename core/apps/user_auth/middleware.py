class UserAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One time configuration and initialization

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, *view_args, **view_kargs):
        if path_needs_to_be_validated(request.path):
            encoded_string = request.headers.get("X-Jwt", None)
            user_id = request.headers.get("User-Id", None)
            # print(f" X-jwt = {encoded_string} and user_id = {user_id}")
            if encoded_string:
                user_id, user_subscription_status = decode_jwt(encoded_string)
                request.session["user_id"] = user_id
                request.session["user_subscription_status"] = user_subscription_status
            elif user_id:
                request.session["user_id"] = user_id
                request.session["user_subscription_status"] = "PRO"

            # if not user_id:
            #     from django.http import JsonResponse
            #
            #     return JsonResponse(
            #         {"error": True, "message": "Unauthenticated user"}, status=403
            #     )


# checking some paths don't need to be validated
def path_needs_to_be_validated(path):
    routes = [
        "/admin",
        "/media",
        "/django-rq",
        "/silk",
        "/pillar-core-swagger",
        "/public/healthcheck",
    ]

    for route in routes:
        if path.startswith(route):
            return False
        else:
            continue

    return True


def decode_jwt(encoded_string):
    import base64
    import json

    # add padding
    encoded_string = encoded_string + "=="

    try:
        decoded_string = base64.b64decode(encoded_string)
        decoded_string = json.loads(decoded_string.decode("utf-8"))
    except Exception:
        raise
    return decoded_string.get("identity"), decoded_string.get("subscription_status")
