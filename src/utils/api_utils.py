import requests
import time
from requests.auth import HTTPBasicAuth

class ApiUtils:
    @staticmethod
    def safe_request_post(url, auth, json_data, max_retries=5, wait_seconds=5):
        """Realizar petición POST con reintentos"""
        for intento in range(1, max_retries + 1):
            resp = requests.post(url, auth=auth, json=json_data)
            if resp.status_code == 429:  # Too Many Requests
                print(f"⚠ Error 429. Reintentando {intento}/{max_retries} en {wait_seconds}s...")
                time.sleep(wait_seconds)
            else:
                return resp
        return resp

    @staticmethod
    def get_ticket(freshdesk_domain, api_key, ticket_id):
        """Obtener información de un ticket"""
        url = f"{freshdesk_domain}/api/v2/tickets/{ticket_id}"
        auth = HTTPBasicAuth(api_key, "X")
        return requests.get(url, auth=auth)

    @staticmethod
    def enviar_nota_interna(freshdesk_domain, api_key, ticket_id, mensaje, emails):
        """Enviar nota interna a un ticket"""
        url = f"{freshdesk_domain}/api/v2/tickets/{ticket_id}/notes"
        auth = HTTPBasicAuth(api_key, "X")
        note_data = {
            "body": mensaje, 
            "notify_emails": emails, 
            "private": True
        }
        return ApiUtils.safe_request_post(url, auth, note_data)