import os
import logging
import requests
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from src.utils.pim_dimensions import procesar_dimensiones_producto

load_dotenv()

logger = logging.getLogger(__name__)

def get_filtered_products(categoria=None):
    """
    Obtiene productos filtrados desde la API del PIM.

    Filtra productos por:
    - Estados: ACTIVA, PROXIMAMENTE, FIN EXISTENCIAS
    - Excluye categoría: REPUESTOS
    - Solo marcas: AS (Aspes), SV (Svan), NL (Nilson), HY (Hyundai)
    - Excluye productos con descripción por defecto
    - Solo productos que tienen medidas (dimensiones físicas válidas)

    Args:
        categoria (str, optional): Filtrar por categoría específica

    Returns:
        list: Lista de productos filtrados con sus dimensiones procesadas
    """
    # Configuración de la API desde variables de entorno
    BASE_URL = os.environ.get('PIM_BASE_URL', 'https://pim.gruposvan.com:7005')
    LOGIN_ENDPOINT = "/auth/login"
    GET_TEXTOS_ENDPOINT = "/B2bProductos"
    SSL_VERIFY = os.environ.get('PIM_SSL_VERIFY', 'true').lower() != 'false'

    # Credenciales de autenticación desde variables de entorno
    AUTH_PAYLOAD = {
        "mail": os.environ.get('PIM_MAIL'),
        "password": os.environ.get('PIM_PASSWORD')
    }

    if not AUTH_PAYLOAD["mail"] or not AUTH_PAYLOAD["password"]:
        raise ValueError("PIM_MAIL y PIM_PASSWORD deben estar definidos en las variables de entorno.")

    try:
        # Autenticación
        login_url = f"{BASE_URL}{LOGIN_ENDPOINT}"
        login_response = requests.post(
            login_url,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            json=AUTH_PAYLOAD,
            verify=SSL_VERIFY
        )
        login_response.raise_for_status()
        login_data = login_response.json()

        # Obtener token
        if isinstance(login_data, dict) and 'token' in login_data:
            access_token = login_data['token']
        elif isinstance(login_data, str):
            access_token = login_data
        else:
            raise ValueError("No se pudo encontrar el token de acceso en la respuesta de login.")

        # Configurar filtro
        filter_params = {}
        if categoria:
            filter_params = {
                "filter": json.dumps({
                    "where": {
                        "categorias": categoria
                    }
                })
            }

        # Obtener datos
        get_textos_url = f"{BASE_URL}{GET_TEXTOS_ENDPOINT}"
        get_headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        get_response = requests.get(
            get_textos_url,
            headers=get_headers,
            params=filter_params,
            verify=SSL_VERIFY
        )
        get_response.raise_for_status()

        textos_generados_data = get_response.json()
        
        # Filtrar y procesar datos
        filtered_data = []
        for item in textos_generados_data:
            # Procesar dimensiones del producto
            dimensiones = procesar_dimensiones_producto(item)

            # Solo incluir productos que tienen medidas (dimensiones válidas)
            # Un producto tiene medidas si tiene las tres dimensiones físicas completas (alto, ancho, largo)
            # El volumen es opcional pero las dimensiones físicas son obligatorias para paletización 3D
            tiene_medidas = (
                dimensiones.get('alto') and 
                dimensiones.get('ancho') and 
                dimensiones.get('largo') and
                dimensiones.get('alto') > 0 and
                dimensiones.get('ancho') > 0 and
                dimensiones.get('largo') > 0
            )

            # Si no tiene medidas completas, saltar este producto
            if not tiene_medidas:
                continue

            # Mapear marca a código
            marca_pim = item.get('marca')
            marca_codigo = {
                'Aspes': 'AS',
                'Svan': 'SV',
                'Nilson': 'NL',
                'Hyundai': 'HY'
            }.get(marca_pim, marca_pim)  # Si no está en el mapa, usar el original

            product_data = {
                'id': item.get('id'),
                'titulo': item.get('titulo'),
                'descripcion_larga': item.get('descripcion_larga'),
                'estado_referencia': item.get('estado_referencia'),
                'categorias': item.get('categorias'),
                'categoriaPadre': item.get('categoriaPadre'),
                'marca': marca_codigo,  # Usar el código mapeado
                'activoEnMarketPlace': item.get('activoEnMarketPlace'),
                'sku': item.get('sku'),
                'volumen': item.get('volumen'),  # Campo volumen del PIM
                # Dimensiones extraídas
                'alto': dimensiones.get('alto'),
                'ancho': dimensiones.get('ancho'),
                'largo': dimensiones.get('largo'),
                'peso': dimensiones.get('peso')
            }

            filtered_data.append(product_data)

        # Ambas variantes de la descripción por defecto son iguales salvo el \n final;
        # strip() las normaliza a la misma cadena en un único paso.
        _DESC_DEFAULT = "<p>Escriba <strong>aquí</strong> su <em>descripción</em>.</p>"
        filtered_data = [
            p for p in filtered_data
            if p.get('descripcion_larga') and p['descripcion_larga'].strip() != _DESC_DEFAULT
        ]

        filtered_data = [p for p in filtered_data if p['estado_referencia'] in ['ACTIVA', 'PROXIMAMENTE', 'FIN EXISTENCIAS']]
        # Filtro anterior: filtered_data = [p for p in filtered_data if p['estado_referencia'] == 'ACTIVA']
        filtered_data = [p for p in filtered_data if p['categorias'] != "REPUESTOS"]
        filtered_data = [p for p in filtered_data if p.get('marca') in ['AS', 'SV', 'NL', 'HY']]

        logger.info("Total de productos después del filtrado (solo con medidas): %d", len(filtered_data))

        return filtered_data

    except requests.HTTPError as e:
        logger.error("Error HTTP al conectar con PIM: %s", e)
        raise
    except Exception as e:
        logger.exception("Error inesperado al obtener productos del PIM")
        raise

# Ejemplo de uso
if __name__ == "__main__":
    data = get_filtered_products("")
    
    # Imprimir los datos
    print(json.dumps(data, indent=4))
    print(f"Total de productos después del filtrado: {len(data)}")
