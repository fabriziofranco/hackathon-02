import json

import requests
import environ
from django.http import HttpResponse
from rest_framework import permissions
from rest_framework.views import APIView

CULQI_API_URL = "https://api.culqi.com/v2"

# Initialise environment variables
env = environ.Env()
environ.Env.read_env()

culqi_headers = {"Content-Type": "application/json", "Authorization": "Bearer " + env("CULQI_PRIVATE_KEY")}


class CreateChargeClient(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            user = self.request.user
            if user.email is None:
                user.email = request.data['email']
            creditos_a_comprar = int(request.data['amount']) * 0.1

            anti_fraud = dict()
            anti_fraud['first_name'] = user.first_name
            anti_fraud['last_name'] = user.last_name
            anti_fraud['phone'] = str(user.phone_number.national_number)

            request.data['currency_code'] = 'PEN'
            request.data['description'] = 'Compra de ' + str(creditos_a_comprar) + ' créditos.'
            request.data['antifraud_details'] = anti_fraud
            request_data = json.dumps(request.data)
            response = requests.post(f"{CULQI_API_URL}/charges", data=request_data, headers=culqi_headers)
            response_dict = json.loads(response.text)

            if response.status_code == 201:
                user.number_of_credits += creditos_a_comprar
                user.save()

            return HttpResponse(json.dumps({"message": response_dict}), status=response.status_code,
                                content_type="application/json")

        except Exception as e:
            return HttpResponse(json.dumps({"message": e}), status=400, content_type="application/json")
