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
from app.models.category import Category
from app.models.media import MediaAsset
from app.models.product import Product, ProductI18n
from app.models.quality_rule import QualityRule, QualityRuleSet
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
    # Job completado con éxito — CSV con filtro "ready"
    {
        "channel": "csv",
        "status": "done",
        "filters": {"status": "ready"},
        "started_at": "2026-03-10T08:00:00",
        "finished_at": "2026-03-10T08:00:12",
        "metrics": {"total_products": 8, "exported": 8, "skipped": 0, "errors": []},
        "error_message": None,
    },
    # Job completado — CSV sin filtros (todos los productos)
    {
        "channel": "csv",
        "status": "done",
        "filters": {},
        "started_at": "2026-03-09T14:30:00",
        "finished_at": "2026-03-09T14:30:25",
        "metrics": {"total_products": 18, "exported": 18, "skipped": 0, "errors": []},
        "error_message": None,
    },
    # Job completado con skips — HTTP con filtro de marca
    {
        "channel": "http",
        "status": "done",
        "filters": {"brand": "Apple"},
        "started_at": "2026-03-10T10:15:00",
        "finished_at": "2026-03-10T10:15:45",
        "metrics": {"total_products": 4, "exported": 3, "skipped": 1, "errors": ["AUDIO-AIRPD-PRO: HTTP 503"]},
        "error_message": None,
    },
    # Job fallido — HTTP endpoint no disponible
    {
        "channel": "http",
        "status": "failed",
        "filters": {"status": "ready", "brand": "Samsung"},
        "started_at": "2026-03-11T07:00:00",
        "finished_at": "2026-03-11T07:00:03",
        "metrics": {"total_products": 0, "exported": 0, "skipped": 0, "errors": ["ConnectionError: endpoint no accesible"]},
        "error_message": "ConnectionError: All connection attempts failed — endpoint https://api.example.com/products no accesible",
    },
    # Job en cola (aún no ha arrancado)
    {
        "channel": "csv",
        "status": "queued",
        "filters": {"status": "draft"},
        "started_at": None,
        "finished_at": None,
        "metrics": {},
        "error_message": None,
    },
    # Job completado — HTTP exportación masiva exitosa
    {
        "channel": "http",
        "status": "done",
        "filters": {"status": "ready"},
        "started_at": "2026-03-08T16:00:00",
        "finished_at": "2026-03-08T16:02:30",
        "metrics": {"total_products": 8, "exported": 8, "skipped": 0, "errors": []},
        "error_message": None,
    },
    # Job completado — CSV filtrado por categoría
    {
        "channel": "csv",
        "status": "done",
        "filters": {"brand": "Sony"},
        "started_at": "2026-03-07T09:00:00",
        "finished_at": "2026-03-07T09:00:05",
        "metrics": {"total_products": 1, "exported": 1, "skipped": 0, "errors": []},
        "error_message": None,
    },
]

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
    for table in (AuditLog, ProductI18n, MediaAsset, Product, Category, SyncJob, QualityRule, QualityRuleSet):
        await db.execute(delete(table))
    await db.commit()
    print("  [wipe] Datos previos eliminados")


async def seed_categories(db: AsyncSession) -> dict[str, str]:
    """Crea el árbol de categorías y devuelve slug→id."""
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


async def seed_sync_jobs(db: AsyncSession) -> None:
    """Crea jobs de sincronización de ejemplo en distintos estados."""
    from datetime import datetime

    for j in SYNC_JOBS:
        started = datetime.fromisoformat(j["started_at"]) if j["started_at"] else None
        finished = datetime.fromisoformat(j["finished_at"]) if j["finished_at"] else None
        job = SyncJob(
            channel=j["channel"],
            status=j["status"],
            filters=j["filters"],
            started_at=started,
            finished_at=finished,
            metrics=j["metrics"],
            error_message=j["error_message"],
        )
        db.add(job)
        filters_str = ", ".join(f"{k}={v}" for k, v in j["filters"].items()) if j["filters"] else "sin filtros"
        print(f"  [sync] {j['channel']:<6} {j['status']:<8} ({filters_str})")
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
        print("1/5  Limpiando datos previos…")
        await wipe_product_data(db)

        print("\n2/5  Creando categorías…")
        slug_to_id = await seed_categories(db)

        print(f"\n3/5  Creando {len(PRODUCTS)} productos…")
        await seed_products(db, slug_to_id)

        print(f"\n4/5  Creando {len(SYNC_JOBS)} sync jobs de ejemplo…")
        await seed_sync_jobs(db)

        print(f"\n5/5  Creando {len(QUALITY_RULE_SETS)} conjuntos de reglas de calidad…")
        await seed_quality_rules(db)

    await engine.dispose()

    print(f"\n✓ Listo — {len(CATEGORIES)} categorías · {len(PRODUCTS)} productos · {len(SYNC_JOBS)} sync jobs · {len(QUALITY_RULE_SETS)} rule sets")
    print("  Abre http://localhost:8000/docs para explorar la API")
    print("  Abre http://localhost:5173 para ver el frontend\n")


if __name__ == "__main__":
    asyncio.run(main())
