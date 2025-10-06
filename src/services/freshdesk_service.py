import requests
import pandas as pd
from requests.auth import HTTPBasicAuth
from utils.api_utils import ApiUtils

class FreshdeskService:
    def __init__(self, config_manager):
        self.config = config_manager

    def obtener_tickets_paginados(self, pagina=1, por_pagina=100):
        """Obtener tickets paginados"""
        if not self.config.validar_configuracion():
            return None

        url = f"{self.config.freshdesk_domain}/api/v2/tickets"
        auth = HTTPBasicAuth(self.config.api_key, "X")
        params = {"page": pagina, "per_page": por_pagina}

        response = requests.get(url, auth=auth, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error al obtener tickets: {response.status_code}")
            return None

    def obtener_empresas(self):
        """Obtener lista de empresas"""
        if not self.config.validar_configuracion():
            return None

        empresas = []
        pagina = 1

        while True:
            url = f"{self.config.freshdesk_domain}/api/v2/companies"
            auth = HTTPBasicAuth(self.config.api_key, "X")
            params = {"page": pagina}

            response = requests.get(url, auth=auth, params=params)
            if response.status_code == 200:
                data = response.json()
                if not data:
                    break
                empresas.extend(data)
                pagina += 1
            elif response.status_code == 403:
                print("⛔ No tienes permisos para ver empresas.")
                break
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                break

        return empresas