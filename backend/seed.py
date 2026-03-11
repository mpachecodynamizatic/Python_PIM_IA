"""
seed.py — Carga datos de ejemplo en la BD de PIM.

Ejecutar desde la carpeta backend/ con el venv activado:
    python seed.py

El script borra y recrea todos los datos de muestra cada vez que se ejecuta
(excepto el usuario admin, que lo gestiona el lifespan de main.py).
"""

import asyncio
import sys
from pathlib import Path

# Asegura que el paquete 'app' sea importable aunque se ejecute desde backend/
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.audit import AuditLog
from app.models.attribute_family import AttributeFamily  # noqa: F401
from app.models.base import Base
from app.models.brand import Brand
from app.models.category import Category
from app.models.external_taxonomy import ExternalTaxonomy, ProductExternalTaxonomy
from app.models.media import MediaAsset
from app.models.product import Product, ProductI18n
from app.models.product_channel import ProductChannel
from app.models.channel import Channel
from app.models.product_compliance import ProductCompliance
from app.models.product_logistics import ProductLogistics
from app.models.quality_rule import QualityRule, QualityRuleSet
from app.models.supplier import Supplier, ProductSupplier
from app.models.sync_job import SyncJob

# ── Datos de muestra ──────────────────────────────────────────────────────────

CATEGORIES = [
    # (slug, name, parent_slug, attribute_schema)
    ("electronica",  "Electrónica",   None,           {}),
    ("smartphones",  "Smartphones",    "electronica",  {
        "color":   {"type": "string", "label": "Color"},
        "ram_gb":  {"type": "number", "label": "RAM (GB)"},
        "storage_gb": {"type": "number", "label": "Almacenamiento (GB)"},
    }),
    ("laptops",      "Laptops",        "electronica",  {
        "cpu":     {"type": "string",  "label": "Procesador"},
        "ram_gb":  {"type": "number",  "label": "RAM (GB)"},
        "screen_inches": {"type": "number", "label": 'Pantalla (")'},
    }),
    ("audio",        "Audio",          "electronica",  {
        "wireless": {"type": "boolean", "label": "Inalámbrico"},
        "battery_h": {"type": "number", "label": "Batería (h)"},
    }),
    ("ropa",         "Ropa",           None,           {}),
    ("ropa-hombre",  "Hombre",         "ropa",         {
        "talla": {"type": "string", "label": "Talla", "options": ["XS","S","M","L","XL","XXL"]},
    }),
    ("ropa-mujer",   "Mujer",          "ropa",         {
        "talla": {"type": "string", "label": "Talla", "options": ["XS","S","M","L","XL"]},
    }),
    ("hogar",        "Hogar",          None,           {}),
    ("cocina",       "Cocina",         "hogar",        {
        "material": {"type": "string", "label": "Material"},
        "capacidad_l": {"type": "number", "label": "Capacidad (L)"},
    }),
    ("decoracion",   "Decoración",     "hogar",        {
        "estilo": {"type": "string",  "label": "Estilo", "options": ["Moderno", "Rústico", "Clásico"]},
    }),
]

PRODUCTS = [
    # Smartphones — calidad ALTA (todo completado)
    {
        "sku": "PHONE-S24-BLK", "brand": "Samsung", "status": "ready",
        "category_slug": "smartphones",
        "seo": {"title": "Samsung Galaxy S24 Negro 256GB", "description": "El smartphone más potente de Samsung con cámara de 200MP y pantalla Dynamic AMOLED 2X."},
        "attributes": {"color": "Negro", "ram_gb": 8, "storage_gb": 256, "red_5g": True},
        "translations": {
            "es": ("Samsung Galaxy S24 Negro 256GB", "Experimenta el poder de la IA en la palma de tu mano con el Galaxy S24. Pantalla de 6.2\" Dynamic AMOLED 2X, procesador Snapdragon 8 Gen 3 y cámara de 50MP."),
            "en": ("Samsung Galaxy S24 Black 256GB", "Experience the power of AI in the palm of your hand with the Galaxy S24. 6.2\" Dynamic AMOLED 2X display, Snapdragon 8 Gen 3 processor and 50MP camera."),
        },
        "media_urls": ["/uploads/sample-phone-s24.jpg"],
    },
    {
        "sku": "PHONE-IP15-WHT", "brand": "Apple", "status": "ready",
        "category_slug": "smartphones",
        "seo": {"title": "iPhone 15 Pro Blanco Natural 128GB", "description": "iPhone 15 Pro con chip A17 Pro, cámara de 48MP y titanio de grado aeroespacial."},
        "attributes": {"color": "Blanco Natural", "ram_gb": 8, "storage_gb": 128, "chip": "A17 Pro"},
        "translations": {
            "es": ("iPhone 15 Pro Blanco Natural 128GB", "El iPhone más avanzado jamás creado. Chip A17 Pro de titanio. Sistema de cámara Pro con zoom óptico 3x."),
            "en": ("iPhone 15 Pro Natural White 128GB", "The most advanced iPhone ever. A17 Pro chip. Titanium design. Pro camera system with 3x optical zoom."),
        },
        "media_urls": ["/uploads/sample-iphone15.jpg"],
    },
    {
        "sku": "PHONE-PIX8-GRN", "brand": "Google", "status": "ready",
        "category_slug": "smartphones",
        "seo": {"title": "Google Pixel 8 Verde 128GB", "description": "El Pixel 8 con Google AI integrado, cámara de 50MP y 7 años de actualizaciones garantizadas."},
        "attributes": {"color": "Verde Menta", "ram_gb": 8, "storage_gb": 128},
        "translations": {
            "es": ("Google Pixel 8 Verde Menta 128GB", "Google AI en tu bolsillo. Llama a la Mejor Foto, Borrador Mágico y 7 años de actualizaciones de Android."),
            "en": ("Google Pixel 8 Mint Green 128GB", "Google AI in your pocket. Best Take, Magic Eraser and 7 years of Android updates guaranteed."),
        },
        "media_urls": [],
    },
    {
        "sku": "PHONE-XIA-BLU", "brand": "Xiaomi", "status": "draft",
        "category_slug": "smartphones",
        "seo": {"title": "Xiaomi 14 Azul 256GB", "description": ""},
        "attributes": {"color": "Azul Océano", "ram_gb": 12, "storage_gb": 256},
        "translations": {
            "es": ("Xiaomi 14 Azul Océano 256GB", "Snapdragon 8 Gen 3 con cámara Leica profesional y carga de 90W HyperCharge."),
        },
        "media_urls": [],
    },
    {
        "sku": "PHONE-OPP-RED", "brand": "OPPO", "status": "draft",
        "category_slug": "smartphones",
        "seo": {},
        "attributes": {},
        "translations": {},
        "media_urls": [],
    },

    # Laptops — calidad MEDIA
    {
        "sku": "LAPTOP-MBP-14", "brand": "Apple", "status": "ready",
        "category_slug": "laptops",
        "seo": {"title": "MacBook Pro 14\" M3 Pro 18GB 512GB", "description": "MacBook Pro con chip M3 Pro de 11 núcleos. Pantalla Liquid Retina XDR de 14.2\"."},
        "attributes": {"cpu": "Apple M3 Pro", "ram_gb": 18, "screen_inches": 14.2, "color": "Plata"},
        "translations": {
            "es": ("MacBook Pro 14\" M3 Pro", "El portátil profesional con chip M3 Pro, hasta 18 horas de batería y pantalla Liquid Retina XDR."),
            "en": ("MacBook Pro 14\" M3 Pro", "Professional laptop with M3 Pro chip, up to 18 hours battery life and Liquid Retina XDR display."),
        },
        "media_urls": ["/uploads/sample-macbook.jpg"],
    },
    {
        "sku": "LAPTOP-DELL-XPS", "brand": "Dell", "status": "ready",
        "category_slug": "laptops",
        "seo": {"title": "Dell XPS 15 Core i9 32GB 1TB", "description": "El ultrabook premium de Dell con pantalla OLED 3.5K y procesador Intel Core i9."},
        "attributes": {"cpu": "Intel Core i9-13900H", "ram_gb": 32, "screen_inches": 15.6},
        "translations": {
            "es": ("Dell XPS 15 OLED", "Ultrabook premium con pantalla OLED 3.5K, Intel Core i9 y RTX 4070. Para creativos exigentes."),
        },
        "media_urls": [],
    },
    {
        "sku": "LAPTOP-LNVO-T14", "brand": "Lenovo", "status": "draft",
        "category_slug": "laptops",
        "seo": {},
        "attributes": {"cpu": "AMD Ryzen 7 PRO", "ram_gb": 16, "screen_inches": 14.0},
        "translations": {},
        "media_urls": [],
    },

    # Audio — calidad VARIADA
    {
        "sku": "AUDIO-SONY-WH", "brand": "Sony", "status": "ready",
        "category_slug": "audio",
        "seo": {"title": "Sony WH-1000XM5 Negro - Auriculares Inalámbricos", "description": "Los mejores auriculares con cancelación de ruido del mercado. 30 horas de batería y llamadas de voz nítidas."},
        "attributes": {"wireless": True, "battery_h": 30, "color": "Negro", "anc": True},
        "translations": {
            "es": ("Sony WH-1000XM5 Negros", "Líderes en cancelación de ruido. 30h de batería, procesador QN2e y micrófono con IA para llamadas perfectas."),
            "en": ("Sony WH-1000XM5 Black", "Industry-leading noise canceling headphones with 30h battery, QN2e processor and AI-powered mic for crystal-clear calls."),
        },
        "media_urls": ["/uploads/sample-sony-wh.jpg"],
    },
    {
        "sku": "AUDIO-BOSE-700", "brand": "Bose", "status": "ready",
        "category_slug": "audio",
        "seo": {"title": "Bose Headphones 700 Negro", "description": "Auriculares premium Bose con 11 niveles de cancelación de ruido."},
        "attributes": {"wireless": True, "battery_h": 20, "color": "Negro"},
        "translations": {
            "es": ("Bose Headphones 700", "La excelencia en audio Bose. 11 niveles de ANC ajustables, micrófono con 8 micrófonos y asistentes de voz integrados."),
            "en": ("Bose Headphones 700", "Bose audio excellence. 11 adjustable ANC levels, 8-mic system and built-in voice assistants."),
        },
        "media_urls": [],
    },
    {
        "sku": "AUDIO-AIRPD-PRO", "brand": "Apple", "status": "ready",
        "category_slug": "audio",
        "seo": {"title": "AirPods Pro (2ª gen) con MagSafe", "description": ""},
        "attributes": {"wireless": True, "battery_h": 6, "color": "Blanco"},
        "translations": {
            "es": ("AirPods Pro 2ª Generación", "ANC adaptativa, audio espacial personalizado con seguimiento de cabeza y chip H2 para un sonido inigualable."),
        },
        "media_urls": [],
    },
    {
        "sku": "AUDIO-JBL-FLIP", "brand": "JBL", "status": "draft",
        "category_slug": "audio",
        "seo": {},
        "attributes": {"wireless": True, "battery_h": 12, "waterproof": "IPX7"},
        "translations": {},
        "media_urls": [],
    },

    # Ropa — calidad BAJA (principalmente borradores sin traducciones)
    {
        "sku": "ROPA-NKE-TEE-M", "brand": "Nike", "status": "draft",
        "category_slug": "ropa-hombre",
        "seo": {"title": "Nike Dri-FIT Camiseta Hombre", "description": "Camiseta técnica Nike Dri-FIT para entrenamiento."},
        "attributes": {"talla": "M", "color": "Negro", "tejido": "Dri-FIT"},
        "translations": {},
        "media_urls": [],
    },
    {
        "sku": "ROPA-ADI-JACK-L", "brand": "Adidas", "status": "draft",
        "category_slug": "ropa-hombre",
        "seo": {},
        "attributes": {"talla": "L"},
        "translations": {},
        "media_urls": [],
    },
    {
        "sku": "ROPA-ZAR-DRS-S", "brand": "Zara", "status": "draft",
        "category_slug": "ropa-mujer",
        "seo": {},
        "attributes": {"talla": "S"},
        "translations": {},
        "media_urls": [],
    },

    # Hogar — mix
    {
        "sku": "HOGAR-INS-OLLA32", "brand": "Instant Pot", "status": "ready",
        "category_slug": "cocina",
        "seo": {"title": "Instant Pot Duo 7 en 1 - 5,7 L", "description": "La olla a presión eléctrica multifunción más vendida del mundo. 7 funciones en un solo electrodoméstico."},
        "attributes": {"material": "Acero inoxidable", "capacidad_l": 5.7, "funciones": 7},
        "translations": {
            "es": ("Instant Pot Duo 7 en 1 — 5,7 L", "Olla a presión, olla arrocera, sauteadora, vaporera, yogurtera y calentador todo en uno. Cocina hasta 70% más rápido."),
            "en": ("Instant Pot Duo 7-in-1 — 5.7L", "Pressure cooker, rice cooker, sauté pan, steamer, yogurt maker and food warmer all in one. Cook up to 70% faster."),
        },
        "media_urls": [],
    },
    {
        "sku": "HOGAR-IKA-LAMP", "brand": "IKEA", "status": "draft",
        "category_slug": "decoracion",
        "seo": {},
        "attributes": {"estilo": "Moderno", "material": "Metal"},
        "translations": {},
        "media_urls": [],
    },
    {
        "sku": "HOGAR-DYS-V15", "brand": "Dyson", "status": "ready",
        "category_slug": "cocina",
        "seo": {"title": "Dyson V15 Detect Aspirador Inalámbrico", "description": "Aspirador sin cable con láser que detecta el polvo invisible. 60 min de autonomía."},
        "attributes": {"material": "Plástico ABS", "capacidad_l": 0.76, "bateria_min": 60},
        "translations": {
            "es": ("Dyson V15 Detect", "El aspirador más inteligente de Dyson con tecnología láser para detectar polvo invisible y pantalla LCD en tiempo real."),
        },
        "media_urls": [],
    },
]


SYNC_JOBS = [
    # Job completado con éxito — B2C (FTP) con filtro "ready"
    {
        "channel_code": "b2c",
        "status": "done",
        "filters": {"status": "ready"},
        "started_at": "2026-03-10T08:00:00",
        "finished_at": "2026-03-10T08:00:12",
        "metrics": {"total_products": 8, "exported": 8, "skipped": 0, "errors": []},
        "error_message": None,
    },
    # Job completado — B2C (FTP) sin filtros (todos los productos)
    {
        "channel_code": "b2c",
        "status": "done",
        "filters": {},
        "started_at": "2026-03-09T14:30:00",
        "finished_at": "2026-03-09T14:30:25",
        "metrics": {"total_products": 18, "exported": 18, "skipped": 0, "errors": []},
        "error_message": None,
    },
    # Job completado con skips — Amazon (HTTP POST) con filtro de marca
    {
        "channel_code": "amazon",
        "status": "done",
        "filters": {"brand": "Apple"},
        "started_at": "2026-03-10T10:15:00",
        "finished_at": "2026-03-10T10:15:45",
        "metrics": {"total_products": 4, "exported": 3, "skipped": 1, "errors": ["AUDIO-AIRPD-PRO: HTTP 503"]},
        "error_message": None,
    },
    # Job fallido — Amazon (HTTP POST) endpoint no disponible
    {
        "channel_code": "amazon",
        "status": "failed",
        "filters": {"status": "ready", "brand": "Samsung"},
        "started_at": "2026-03-11T07:00:00",
        "finished_at": "2026-03-11T07:00:03",
        "metrics": {"total_products": 0, "exported": 0, "skipped": 0, "errors": ["ConnectionError: endpoint no accesible"]},
        "error_message": "ConnectionError: All connection attempts failed — endpoint https://api.amazon.com/products no accesible",
    },
    # Job en cola (aún no ha arrancado) — B2C (FTP)
    {
        "channel_code": "b2c",
        "status": "queued",
        "filters": {"status": "draft"},
        "started_at": None,
        "finished_at": None,
        "metrics": {},
        "error_message": None,
    },
    # Job completado — Miravia (HTTP POST) exportación masiva exitosa
    {
        "channel_code": "miravia",
        "status": "done",
        "filters": {"status": "ready"},
        "started_at": "2026-03-08T16:00:00",
        "finished_at": "2026-03-08T16:02:30",
        "metrics": {"total_products": 8, "exported": 8, "skipped": 0, "errors": []},
        "error_message": None,
    },
    # Job completado — B2B (SSH) filtrado por marca Sony
    {
        "channel_code": "b2b",
        "status": "done",
        "filters": {"brand": "Sony"},
        "started_at": "2026-03-07T09:00:00",
        "finished_at": "2026-03-07T09:00:05",
        "metrics": {"total_products": 1, "exported": 1, "skipped": 0, "errors": []},
        "error_message": None,
    },
]

BRANDS = [
    {"name": "Samsung",      "slug": "samsung",       "website": "https://www.samsung.com",   "description": "Lider global en electronica de consumo y semiconductores."},
    {"name": "Apple",        "slug": "apple",         "website": "https://www.apple.com",     "description": "Tecnologia, software y servicios premium."},
    {"name": "Google",       "slug": "google",        "website": "https://store.google.com",  "description": "Hardware y servicios de Google."},
    {"name": "Xiaomi",       "slug": "xiaomi",        "website": "https://www.mi.com",        "description": "Smartphones y electrodomesticos de gran relacion calidad/precio."},
    {"name": "OPPO",         "slug": "oppo",          "website": "https://www.oppo.com",      "description": "Fabricante chino de smartphones con camara innovadora."},
    {"name": "Dell",         "slug": "dell",          "website": "https://www.dell.com",      "description": "Computadoras y servidores empresariales."},
    {"name": "Lenovo",       "slug": "lenovo",        "website": "https://www.lenovo.com",    "description": "Tecnologia personal y empresarial."},
    {"name": "Sony",         "slug": "sony",          "website": "https://www.sony.com",      "description": "Electronica de consumo y entretenimiento."},
    {"name": "Bose",         "slug": "bose",          "website": "https://www.bose.com",      "description": "Audio premium y cancelacion de ruido."},
    {"name": "JBL",          "slug": "jbl",           "website": "https://www.jbl.com",       "description": "Audio portatil y de alta fidelidad."},
    {"name": "Nike",         "slug": "nike",          "website": "https://www.nike.com",      "description": "Ropa y calzado deportivo."},
    {"name": "Adidas",       "slug": "adidas",        "website": "https://www.adidas.com",    "description": "Ropa, calzado y accesorios deportivos."},
    {"name": "Zara",         "slug": "zara",          "website": "https://www.zara.com",      "description": "Moda accesible de tendencia. Grupo Inditex."},
    {"name": "Instant Pot",  "slug": "instant-pot",   "website": "https://www.instanthome.com","description": "Utensilios de cocina multifuncion."},
    {"name": "IKEA",         "slug": "ikea",          "website": "https://www.ikea.com",      "description": "Muebles y decoracion para el hogar."},
    {"name": "Dyson",        "slug": "dyson",         "website": "https://www.dyson.com",     "description": "Aspiradoras, purificadores y cuidado del cabello."},
]

SUPPLIERS = [
    {
        "name": "Tech Distributors SL",
        "code": "TD-ES",
        "country": "ES",
        "contact_email": "ventas@techdist.es",
        "contact_phone": "+34 91 234 5678",
        "notes": "Distribuidor oficial Samsung y Sony en Peninsula Iberica. MOQ 50 unidades.",
        "active": True,
    },
    {
        "name": "Apple Premium Reseller",
        "code": "APR-EU",
        "country": "DE",
        "contact_email": "orders@apr-eu.com",
        "contact_phone": "+49 89 987 6543",
        "notes": "Distribuidor autorizado Apple para Europa central. SLA 48h.",
        "active": True,
    },
    {
        "name": "Global Imports HK",
        "code": "GI-HK",
        "country": "HK",
        "contact_email": "b2b@globalimports.hk",
        "contact_phone": "+852 3456 7890",
        "notes": "Importador directo desde fabrica Xiaomi y OPPO. Lead time 21 dias.",
        "active": True,
    },
    {
        "name": "Fashion Wholesale FR",
        "code": "FW-FR",
        "country": "FR",
        "contact_email": "wholesale@fashionwf.fr",
        "contact_phone": "+33 1 23 45 67 89",
        "notes": "Mayorista de moda Nike, Adidas y Zara para mercado europeo.",
        "active": True,
    },
    {
        "name": "Discontinued Supplier",
        "code": "OLD-SUP",
        "country": "CN",
        "contact_email": None,
        "contact_phone": None,
        "notes": "Proveedor discontinuado en 2025.",
        "active": False,
    },
]

# Logistics data for some products: sku → fields
PRODUCT_LOGISTICS = {
    "PHONE-S24-BLK": {
        "base_unit": "pieza", "box_units": 20, "pallet_boxes": 50,
        "height_mm": 147, "width_mm": 70, "depth_mm": 7,
        "weight_gross_g": 190, "weight_net_g": 167,
        "packaging_type": "Caja retail", "stackable": True, "adr": False,
    },
    "PHONE-IP15-WHT": {
        "base_unit": "pieza", "box_units": 12, "pallet_boxes": 60,
        "height_mm": 147, "width_mm": 71, "depth_mm": 8,
        "weight_gross_g": 205, "weight_net_g": 187,
        "packaging_type": "Caja retail", "stackable": True, "adr": False,
    },
    "LAPTOP-MBP-14": {
        "base_unit": "pieza", "box_units": 5, "pallet_boxes": 20,
        "height_mm": 312, "width_mm": 221, "depth_mm": 16,
        "weight_gross_g": 1800, "weight_net_g": 1610,
        "packaging_type": "Caja de carton reforzada", "stackable": False, "adr": False,
    },
    "AUDIO-SONY-WH": {
        "base_unit": "pieza", "box_units": 24, "pallet_boxes": 40,
        "height_mm": 220, "width_mm": 185, "depth_mm": 80,
        "weight_gross_g": 400, "weight_net_g": 255,
        "packaging_type": "Caja retail con estuche", "stackable": True, "adr": False,
    },
    "HOGAR-INS-OLLA32": {
        "base_unit": "pieza", "box_units": 4, "pallet_boxes": 8,
        "height_mm": 330, "width_mm": 320, "depth_mm": 320,
        "weight_gross_g": 6200, "weight_net_g": 5200,
        "packaging_type": "Caja carton doble canal", "stackable": False, "adr": False,
    },
}

# Compliance data for some products: sku → fields
PRODUCT_COMPLIANCE = {
    "PHONE-S24-BLK": {
        "certifications": ["CE", "FCC", "RoHS", "WEEE"],
        "country_of_origin": "KR", "hs_code": "8517120000",
        "has_lot_traceability": False, "has_expiry_date": False,
        "legal_warnings": "Mantener alejado del alcance de los ninos menores de 3 anos.",
    },
    "PHONE-IP15-WHT": {
        "certifications": ["CE", "FCC", "RoHS", "MFi"],
        "country_of_origin": "CN", "hs_code": "8517120000",
        "has_lot_traceability": False, "has_expiry_date": False,
    },
    "LAPTOP-MBP-14": {
        "certifications": ["CE", "FCC", "RoHS", "Energy Star"],
        "country_of_origin": "CN", "hs_code": "8471300000",
        "has_lot_traceability": False, "has_expiry_date": False,
    },
    "AUDIO-SONY-WH": {
        "certifications": ["CE", "FCC", "RoHS"],
        "country_of_origin": "CN", "hs_code": "8518300000",
        "has_lot_traceability": False, "has_expiry_date": False,
    },
    "HOGAR-INS-OLLA32": {
        "certifications": ["CE", "RoHS", "UL"],
        "country_of_origin": "CN", "hs_code": "8516600000",
        "legal_warnings": "No sumergir en agua. Leer el manual antes de usar.",
        "has_lot_traceability": False, "has_expiry_date": False,
    },
}

# Channel catalog for some products
CHANNELS = [
    {
        "name": "Tienda B2C",
        "code": "b2c",
        "description": "Canal directo al consumidor final",
        "active": True,
        "connection_type": "ftp",
        "connection_config": {
            "host": "ftp.tienda.com",
            "port": 21,
            "username": "pim_user",
            "password": "",
            "remote_path": "/products/export/",
            "passive": True,
        },
    },
    {
        "name": "B2B / Distribuidores",
        "code": "b2b",
        "description": "Canal para clientes empresariales y distribuidores",
        "active": True,
        "connection_type": "ssh",
        "connection_config": {
            "host": "sftp.distribuidores.com",
            "port": 22,
            "username": "pim_sync",
            "password": "",
            "remote_path": "/data/products/",
            "private_key": None,
        },
    },
    {
        "name": "Amazon",
        "code": "amazon",
        "description": "Marketplace Amazon EU",
        "active": True,
        "connection_type": "http_post",
        "connection_config": {
            "url": "https://api.amazon.com/products",
            "timeout": 30,
            "auth_type": "bearer",
            "token": "",
            "headers": {},
        },
    },
    {
        "name": "Miravia",
        "code": "miravia",
        "description": "Marketplace Miravia",
        "active": True,
        "connection_type": "http_post",
        "connection_config": {
            "url": "https://api.miravia.es/catalog/products",
            "timeout": 30,
            "auth_type": "bearer",
            "token": "",
            "headers": {},
        },
    },
    {
        "name": "eBay",
        "code": "ebay",
        "description": "Marketplace eBay",
        "active": True,
        "connection_type": "http_post",
        "connection_config": {
            "url": "https://api.ebay.com/sell/inventory/v1/bulk_create_or_replace_inventory_item",
            "timeout": 30,
            "auth_type": "bearer",
            "token": "",
            "headers": {"Content-Language": "es-ES"},
        },
    },
    {
        "name": "Otros",
        "code": "other",
        "description": "Canal genérico",
        "active": True,
        "connection_type": None,
        "connection_config": {},
    },
]

# Channel data for some products: sku → list of channel dicts (using channel_code)
PRODUCT_CHANNELS = {
    "PHONE-S24-BLK": [
        {"channel_code": "b2c",    "name": "Samsung Galaxy S24 Negro",            "active": True},
        {"channel_code": "amazon", "name": "Samsung Galaxy S24 Black 256GB",       "active": True, "country_restrictions": ["DE", "FR", "ES", "IT"]},
    ],
    "PHONE-IP15-WHT": [
        {"channel_code": "b2c",    "name": "iPhone 15 Pro Natural White",          "active": True},
        {"channel_code": "amazon", "name": "Apple iPhone 15 Pro 128GB White",      "active": True},
        {"channel_code": "b2b",    "name": "iPhone 15 Pro (Business)",             "active": False},
    ],
    "LAPTOP-MBP-14": [
        {"channel_code": "b2c",    "name": "MacBook Pro 14 M3",                    "active": True},
        {"channel_code": "b2b",    "name": 'MacBook Pro 14" for Business',         "active": True},
    ],
    "AUDIO-SONY-WH": [
        {"channel_code": "b2c",    "name": "Sony WH-1000XM5 Negro",               "active": True},
        {"channel_code": "amazon", "name": "Sony WH1000XM5 Wireless Headphones",   "active": True},
    ],
}

# Supplier links: sku → list of {supplier_code, is_primary, ...}
PRODUCT_SUPPLIER_LINKS = {
    "PHONE-S24-BLK":  [{"code": "TD-ES",  "is_primary": True,  "moq": 50,  "lead_time_days": 7,  "purchase_price": 720.00, "currency": "EUR"}],
    "PHONE-IP15-WHT": [{"code": "APR-EU", "is_primary": True,  "moq": 12,  "lead_time_days": 5,  "purchase_price": 950.00, "currency": "EUR"}],
    "PHONE-PIX8-GRN": [{"code": "GI-HK",  "is_primary": True,  "moq": 100, "lead_time_days": 21, "purchase_price": 380.00, "currency": "USD"}],
    "PHONE-XIA-BLU":  [{"code": "GI-HK",  "is_primary": True,  "moq": 200, "lead_time_days": 21, "purchase_price": 290.00, "currency": "USD"}],
    "AUDIO-SONY-WH":  [{"code": "TD-ES",  "is_primary": True,  "moq": 24,  "lead_time_days": 10, "purchase_price": 230.00, "currency": "EUR"}],
    "ROPA-NKE-TEE-M": [{"code": "FW-FR",  "is_primary": True,  "moq": 100, "lead_time_days": 14, "purchase_price": 18.50, "currency": "EUR"}],
    "ROPA-ADI-JACK-L":[{"code": "FW-FR",  "is_primary": True,  "moq": 50,  "lead_time_days": 14, "purchase_price": 32.00, "currency": "EUR"}],
}

EXTERNAL_TAXONOMIES = [
    {
        "name": "GS1 GPC",
        "provider": "GS1",
        "description": "Global Product Classification de GS1. Estandar internacional para clasificacion de productos de consumo.",
    },
    {
        "name": "Amazon Browse Tree",
        "provider": "Amazon",
        "description": "Arbol de navegacion de Amazon para categorizar productos en el marketplace.",
    },
    {
        "name": "Google Product Taxonomy",
        "provider": "Google",
        "description": "Taxonomia de Google Shopping para anuncios de productos.",
    },
]

# Product → external taxonomy mappings: sku → list of {taxonomy_name, node_code, node_name, node_path}
PRODUCT_TAXONOMIES = {
    "PHONE-S24-BLK": [
        {"taxonomy": "GS1 GPC", "node_code": "60060000", "node_name": "Smartphones", "node_path": "IT Products > Mobile Phones > Smartphones"},
        {"taxonomy": "Amazon Browse Tree", "node_code": "2335752011", "node_name": "Unlocked Cell Phones", "node_path": "Electronics > Cell Phones & Accessories > Cell Phones > Unlocked Phones"},
        {"taxonomy": "Google Product Taxonomy", "node_code": "267", "node_name": "Telefonos moviles", "node_path": "Electronics > Communications > Telefonos > Telefonos moviles"},
    ],
    "PHONE-IP15-WHT": [
        {"taxonomy": "GS1 GPC", "node_code": "60060000", "node_name": "Smartphones", "node_path": "IT Products > Mobile Phones > Smartphones"},
        {"taxonomy": "Amazon Browse Tree", "node_code": "2335752011", "node_name": "Unlocked Cell Phones", "node_path": "Electronics > Cell Phones & Accessories > Cell Phones > Unlocked Phones"},
    ],
    "LAPTOP-MBP-14": [
        {"taxonomy": "GS1 GPC", "node_code": "60050000", "node_name": "Laptops", "node_path": "IT Products > Computers > Portable Computers > Laptops"},
        {"taxonomy": "Google Product Taxonomy", "node_code": "328", "node_name": "Ordenadores portatiles", "node_path": "Electronics > Computers > Ordenadores portatiles"},
    ],
    "AUDIO-SONY-WH": [
        {"taxonomy": "GS1 GPC", "node_code": "60080000", "node_name": "Headphones", "node_path": "IT Products > Audio Equipment > Headphones"},
        {"taxonomy": "Amazon Browse Tree", "node_code": "172541", "node_name": "Over-Ear Headphones", "node_path": "Electronics > Headphones > Over-Ear Headphones"},
    ],
}

QUALITY_RULE_SETS = [
    {
        "name": "Ecommerce Estandar",
        "description": "Reglas para publicacion en tienda online. Media y SEO tienen peso doble. Para productos 'ready' se exige score minimo en todas las dimensiones.",
        "active": True,
        "rules": [
            {"dimension": "brand", "weight": 1.0, "min_score": 0.0, "required_status": None},
            {"dimension": "category", "weight": 1.0, "min_score": 1.0, "required_status": "ready"},
            {"dimension": "seo", "weight": 2.0, "min_score": 0.5, "required_status": "ready"},
            {"dimension": "attributes", "weight": 1.5, "min_score": 0.0, "required_status": None},
            {"dimension": "media", "weight": 2.0, "min_score": 1.0, "required_status": "ready"},
            {"dimension": "i18n", "weight": 1.0, "min_score": 0.0, "required_status": None},
        ],
    },
    {
        "name": "Catalogo Basico",
        "description": "Reglas minimas para catalogo interno. Solo valida que haya marca, categoria y al menos un atributo.",
        "active": False,
        "rules": [
            {"dimension": "brand", "weight": 1.0, "min_score": 1.0, "required_status": None},
            {"dimension": "category", "weight": 1.0, "min_score": 1.0, "required_status": None},
            {"dimension": "attributes", "weight": 1.0, "min_score": 1.0, "required_status": None},
        ],
    },
    {
        "name": "Marketplace Premium",
        "description": "Exigencias altas para marketplaces premium. Todas las dimensiones son obligatorias con peso elevado.",
        "active": False,
        "rules": [
            {"dimension": "brand", "weight": 1.0, "min_score": 1.0, "required_status": None},
            {"dimension": "category", "weight": 1.0, "min_score": 1.0, "required_status": None},
            {"dimension": "seo", "weight": 3.0, "min_score": 1.0, "required_status": None},
            {"dimension": "attributes", "weight": 2.0, "min_score": 1.0, "required_status": None},
            {"dimension": "media", "weight": 3.0, "min_score": 1.0, "required_status": None},
            {"dimension": "i18n", "weight": 2.0, "min_score": 1.0, "required_status": None},
        ],
    },
]


# ── Engine ─────────────────────────────────────────────────────────────────────

engine = create_async_engine(settings.DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ── Helpers ────────────────────────────────────────────────────────────────────

async def wipe_product_data(db: AsyncSession) -> None:
    """Elimina solo los datos de muestra (NO el usuario admin)."""
    for table in (
        AuditLog, ProductI18n, MediaAsset,
        ProductExternalTaxonomy, ProductSupplier,
        ProductChannel, ProductCompliance, ProductLogistics,
        Product, Category, SyncJob, QualityRule, QualityRuleSet,
        Supplier, ExternalTaxonomy, Brand, Channel,
    ):
        await db.execute(delete(table))
    await db.commit()
    print("  [wipe] Datos previos eliminados")


async def seed_brands(db: AsyncSession) -> None:
    """Crea el catalogo de marcas."""
    for b in BRANDS:
        brand = Brand(
            name=b["name"],
            slug=b["slug"],
            description=b.get("description"),
            website=b.get("website"),
            active=True,
        )
        db.add(brand)
        print(f"  [brand] {b['name']}")
    await db.commit()


async def seed_suppliers(db: AsyncSession) -> dict[str, str]:
    """Crea proveedores y devuelve code→id."""
    code_to_id: dict[str, str] = {}
    for s in SUPPLIERS:
        supplier = Supplier(
            name=s["name"],
            code=s.get("code"),
            country=s.get("country"),
            contact_email=s.get("contact_email"),
            contact_phone=s.get("contact_phone"),
            notes=s.get("notes"),
            active=s.get("active", True),
        )
        db.add(supplier)
        await db.flush()
        if s.get("code"):
            code_to_id[s["code"]] = supplier.id
        status = "activo" if s["active"] else "inactivo"
        print(f"  [supplier] {s['name']} ({status})")
    await db.commit()
    return code_to_id


async def seed_channels(db: AsyncSession) -> dict[str, str]:
    """Crea el catálogo de canales y devuelve code→id."""
    code_to_id: dict[str, str] = {}
    for c in CHANNELS:
        channel = Channel(
            name=c["name"],
            code=c["code"],
            description=c.get("description"),
            active=c.get("active", True),
            connection_type=c.get("connection_type"),
            connection_config=c.get("connection_config") or {},
        )
        db.add(channel)
        await db.flush()
        code_to_id[c["code"]] = channel.id
        status = "activo" if c["active"] else "inactivo"
        conn = c.get("connection_type") or "sin conexión"
        print(f"  [channel] {c['name']} ({status}) — {conn}")
    await db.commit()
    return code_to_id


async def seed_categories(db: AsyncSession) -> dict[str, str]:
    slug_to_id: dict[str, str] = {}
    for slug, name, parent_slug, attr_schema in CATEGORIES:
        parent_id = slug_to_id.get(parent_slug) if parent_slug else None
        cat = Category(
            name=name,
            slug=slug,
            parent_id=parent_id,
            attribute_schema=attr_schema,
        )
        db.add(cat)
        await db.flush()
        slug_to_id[slug] = cat.id
        print(f"  [cat] {('  ' if parent_slug else '')}{name}")
    await db.commit()
    return slug_to_id


async def seed_products(db: AsyncSession, slug_to_id: dict[str, str]) -> None:
    """Crea productos con traducciones y media."""
    for p in PRODUCTS:
        cat_id = slug_to_id[p["category_slug"]]
        product = Product(
            sku=p["sku"],
            brand=p["brand"],
            status=p["status"],
            category_id=cat_id,
            seo=p.get("seo", {}),
            attributes=p.get("attributes", {}),
        )
        product.translations = []
        db.add(product)
        await db.flush()

        # Traducciones
        for locale, (title, desc) in p.get("translations", {}).items():
            i18n = ProductI18n(
                sku=p["sku"],
                locale=locale,
                title=title,
                description_rich={"text": desc} if desc else None,
            )
            db.add(i18n)

        # Media (URLs de placeholder)
        for url in p.get("media_urls", []):
            asset = MediaAsset(
                sku=p["sku"],
                kind="image",
                url=url,
                filename=url.split("/")[-1],
                metadata_extra={"source": "seed"},
            )
            db.add(asset)

        quality_pct = _estimate_quality(p)
        print(f"  [prod] {p['sku']:<22} {p['brand']:<10} {p['status']:<7} calidad≈{quality_pct}%")

    await db.commit()


def _estimate_quality(p: dict) -> int:
    score = 0
    if p.get("brand"):                                   score += 1
    if p.get("category_slug"):                           score += 1
    seo = p.get("seo", {})
    if seo.get("title") and seo.get("description"):      score += 1
    elif seo.get("title"):                               score += 0
    if p.get("attributes"):                              score += 1
    if p.get("media_urls"):                              score += 1
    if p.get("translations"):                            score += 1
    return round(score / 6 * 100)


async def seed_sync_jobs(db: AsyncSession, channel_code_to_id: dict[str, str]) -> None:
    """Crea jobs de sincronización de ejemplo en distintos estados."""
    from datetime import datetime

    # Build a code→channel-data map for inherited connection info
    channel_data_map = {c["code"]: c for c in CHANNELS}

    for j in SYNC_JOBS:
        code = j["channel_code"]
        channel_id = channel_code_to_id.get(code)
        if not channel_id:
            print(f"  [WARN] Canal '{code}' no encontrado, omitiendo sync job")
            continue
        ch_data = channel_data_map[code]
        started = datetime.fromisoformat(j["started_at"]) if j["started_at"] else None
        finished = datetime.fromisoformat(j["finished_at"]) if j["finished_at"] else None
        job = SyncJob(
            channel_id=channel_id,
            channel_code=ch_data["code"],
            channel_name=ch_data["name"],
            connection_type=ch_data.get("connection_type"),
            connection_config=ch_data.get("connection_config") or {},
            status=j["status"],
            filters=j["filters"],
            started_at=started,
            finished_at=finished,
            metrics=j["metrics"],
            error_message=j["error_message"],
        )
        db.add(job)
        filters_str = ", ".join(f"{k}={v}" for k, v in j["filters"].items()) if j["filters"] else "sin filtros"
        conn = ch_data.get("connection_type") or "http"
        print(f"  [sync] {ch_data['name']:<20} {j['status']:<8} {conn:<10} ({filters_str})")
    await db.commit()


async def seed_quality_rules(db: AsyncSession) -> None:
    """Crea conjuntos de reglas de calidad de ejemplo."""
    for rs_data in QUALITY_RULE_SETS:
        rule_set = QualityRuleSet(
            name=rs_data["name"],
            description=rs_data["description"],
            active=rs_data["active"],
        )
        db.add(rule_set)
        await db.flush()
        for r in rs_data["rules"]:
            rule = QualityRule(
                rule_set_id=rule_set.id,
                dimension=r["dimension"],
                weight=r["weight"],
                min_score=r["min_score"],
                required_status=r["required_status"],
            )
            db.add(rule)
        status = " (ACTIVO)" if rs_data["active"] else ""
        print(f"  [qrule] {rs_data['name']:<25} {len(rs_data['rules'])} reglas{status}")
    await db.commit()


async def seed_logistics_compliance_channels_taxonomies(
    db: AsyncSession,
    taxonomy_name_to_id: dict[str, str],
    supplier_code_to_id: dict[str, str],
    channel_code_to_id: dict[str, str],
) -> None:
    """Crea datos de logistica, cumplimiento, canales, proveedores y taxonomias."""
    # Logistics
    for sku, data in PRODUCT_LOGISTICS.items():
        obj = ProductLogistics(sku=sku, **data)
        db.add(obj)
        print(f"  [logistics] {sku}")

    # Compliance
    for sku, data in PRODUCT_COMPLIANCE.items():
        obj = ProductCompliance(sku=sku, **data)
        db.add(obj)
        print(f"  [compliance] {sku}")

    # Channels
    for sku, channels in PRODUCT_CHANNELS.items():
        for ch in channels:
            channel_id = channel_code_to_id.get(ch["channel_code"])
            if not channel_id:
                print(f"  [WARN] Canal '{ch['channel_code']}' no encontrado, omitiendo")
                continue
            obj = ProductChannel(
                sku=sku,
                channel_id=channel_id,
                name=ch.get("name"),
                active=ch.get("active", True),
                country_restrictions=ch.get("country_restrictions", []),
                marketplace_fields=ch.get("marketplace_fields", {}),
            )
            db.add(obj)
        print(f"  [channels] {sku} — {len(channels)} canales")

    await db.flush()

    # Supplier links
    for sku, links in PRODUCT_SUPPLIER_LINKS.items():
        for link in links:
            supplier_id = supplier_code_to_id.get(link["code"])
            if not supplier_id:
                continue
            obj = ProductSupplier(
                sku=sku,
                supplier_id=supplier_id,
                is_primary=link.get("is_primary", False),
                moq=link.get("moq"),
                lead_time_days=link.get("lead_time_days"),
                purchase_price=link.get("purchase_price"),
                currency=link.get("currency"),
            )
            db.add(obj)
        print(f"  [supplier-link] {sku} — {len(links)} proveedores")

    # External taxonomy mappings
    for sku, mappings in PRODUCT_TAXONOMIES.items():
        for m in mappings:
            taxonomy_id = taxonomy_name_to_id.get(m["taxonomy"])
            if not taxonomy_id:
                continue
            obj = ProductExternalTaxonomy(
                sku=sku,
                taxonomy_id=taxonomy_id,
                node_code=m.get("node_code"),
                node_name=m.get("node_name"),
                node_path=m.get("node_path"),
            )
            db.add(obj)
        print(f"  [taxonomy] {sku} — {len(mappings)} mapeos")

    await db.commit()


async def seed_external_taxonomies(db: AsyncSession) -> dict[str, str]:
    """Crea las taxonomias externas y devuelve name→id."""
    name_to_id: dict[str, str] = {}
    for t in EXTERNAL_TAXONOMIES:
        obj = ExternalTaxonomy(
            name=t["name"],
            provider=t["provider"],
            description=t.get("description"),
        )
        db.add(obj)
        await db.flush()
        name_to_id[t["name"]] = obj.id
        print(f"  [taxonomy-catalog] {t['name']} ({t['provider']})")
    await db.commit()
    return name_to_id


# ── Main ───────────────────────────────────────────────────────────────────────

async def main() -> None:
    print("\n═══════════════════════════════════════════")
    print("  PIM — Carga de datos de ejemplo")
    print("═══════════════════════════════════════════\n")

    # Recrear todas las tablas (drop + create) para reflejar cambios de esquema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        print("1/9  Limpiando datos previos…")
        await wipe_product_data(db)

        print(f"\n2/9  Creando {len(BRANDS)} marcas…")
        await seed_brands(db)

        print(f"\n3/9  Creando {len(SUPPLIERS)} proveedores…")
        supplier_code_to_id = await seed_suppliers(db)

        print(f"\n3b/9  Creando {len(CHANNELS)} canales…")
        channel_code_to_id = await seed_channels(db)

        print(f"\n4/9  Creando {len(EXTERNAL_TAXONOMIES)} taxonomias externas…")
        taxonomy_name_to_id = await seed_external_taxonomies(db)

        print("\n5/9  Creando categorias…")
        slug_to_id = await seed_categories(db)

        print(f"\n6/9  Creando {len(PRODUCTS)} productos…")
        await seed_products(db, slug_to_id)

        print("\n7/9  Creando logistica, cumplimiento, canales y taxonomias de productos…")
        await seed_logistics_compliance_channels_taxonomies(db, taxonomy_name_to_id, supplier_code_to_id, channel_code_to_id)

        print(f"\n8/9  Creando {len(SYNC_JOBS)} sync jobs de ejemplo…")
        await seed_sync_jobs(db, channel_code_to_id)

        print(f"\n9/9  Creando {len(QUALITY_RULE_SETS)} conjuntos de reglas de calidad…")
        await seed_quality_rules(db)

    await engine.dispose()

    print(f"\n✓ Listo — {len(BRANDS)} marcas · {len(SUPPLIERS)} proveedores · {len(CHANNELS)} canales")
    print(f"          {len(CATEGORIES)} categorias · {len(PRODUCTS)} productos")
    print(f"          {len(EXTERNAL_TAXONOMIES)} taxonomias · {len(SYNC_JOBS)} sync jobs · {len(QUALITY_RULE_SETS)} rule sets")
    print("  Abre http://localhost:8000/docs para explorar la API")
    print("  Abre http://localhost:5173 para ver el frontend\n")


if __name__ == "__main__":
    asyncio.run(main())
