"""
Título        : Proyecto Tiendita
Autor         : Jorge Edwin Guevara Ayala
Fecha de creación : 7/10/2026
Descripción   : API REST con FastAPI para administrar los productos de una
                pequeña tienda. La API se comunica con un cliente web (otro
                servidor, puerto 3000) que la consume mediante fetch(),
                demostrando la comunicación entre dos servidores diferentes.

                Aplica principios de programación concurrente y distribuida:
                - Endpoints asíncronos (async/await) que comparten el mismo
                  bucle de eventos de asyncio.
                - Middleware de limitación de peticiones (máximo 5 por segundo
                  por IP) implementado con asyncio.Lock.

                Buena práctica: los comentarios explican el POR QUÉ de cada
                decisión, no solo el QUÉ.
"""

import asyncio
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# =============================================================================
#  APLICACIÓN
# =============================================================================
app = FastAPI()


# -----------------------------------------------------------------------------
#  Middleware de Limitación de Peticiones (Rate Limiting)
# -----------------------------------------------------------------------------
class RateLimitMiddleware:
    """
    Limita la API a un máximo de `max_requests` peticiones por segundo
    (ventana de `window` segundos), calculado por IP del cliente.

    Implementación concurrente (programación concurrente y distribuida):
    - `asyncio.Lock` protege la estructura compartida `_timestamps` para
      evitar condiciones de carrera entre corrutinas que corren de forma
      concurrente sobre el mismo bucle de eventos.
    - `time.monotonic()` mide el tiempo real transcurrido sin depender del
      reloj del sistema (un cambio de fecha/hora no altera la ventana).

    Si el límite se supera, responde HTTP 429 (Too Many Requests) con un
    cuerpo JSON, sin llegar a procesar la petición.
    """

    def __init__(self, app, max_requests: int = 5, window: float = 1.0):
        self.app = app                    # Aplicación ASGI que se envuelve
        self.max_requests = max_requests  # Máximo de peticiones permitidas
        self.window = window              # Ventana de tiempo en segundos
        self._timestamps = {}             # IP -> lista de marcas de tiempo
        self._lock = asyncio.Lock()       # Candado para la sección crítica

    async def __call__(self, scope, receive, send):
        # Solo se limita el tráfico HTTP; el resto de los protocolos ASGI
        # (websockets, lifespan) se delegan tal cual.
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Dirección IP de la que proviene la petición.
        client = scope.get("client")
        ip = client[0] if client else "desconocida"

        # ============ SECCIÓN CRÍTICA (exclusividad con asyncio.Lock) ============
        async with self._lock:
            ahora = time.monotonic()

            # 1. Se conservan únicamente las marcas dentro de la ventana actual.
            marcas = [
                t for t in self._timestamps.get(ip, [])
                if ahora - t < self.window
            ]

            # 2. Si ya se alcanzó el límite, se rechaza la petición (HTTP 429).
            if len(marcas) >= self.max_requests:
                cuerpo = b'{"detail": "Demasiadas peticiones. Maximo 5 por segundo."}'
                await send({
                    "type": "http.response.start",
                    "status": 429,
                    "headers": [(b"content-type", b"application/json")],
                })
                await send({"type": "http.response.body", "body": cuerpo})
                return

            # 3. Se registra la petición actual como aceptada.
            marcas.append(ahora)
            self._timestamps[ip] = marcas
        # ===========================================================================

        # Límite no superado: la petición continúa al resto de la aplicación.
        await self.app(scope, receive, send)


# -----------------------------------------------------------------------------
#  Registro de Middlewares (el orden importa)
# -----------------------------------------------------------------------------
# Importante: FastAPI/Starlette apilan los middlewares "al revés": el ÚLTIMO
# en agregarse queda en la capa EXTERNA (es el primero que recibe la petición).
#
# 1) Limitador de peticiones primero (capa interna): valida el límite de
#    5 peticiones por segundo antes de delegar en la aplicación.
app.add_middleware(RateLimitMiddleware, max_requests=5, window=1.0)

# 2) CORS al final (capa externa): de este modo las peticiones de verificación
#    "preflight" (OPTIONS) que envía el navegador se resuelven aquí sin contar
#    para el límite, y además toda respuesta (incluido el 429 del limitador)
#    sale con los encabezados CORS necesarios para el cliente en el puerto 3000.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
#  INVENTARIO (en memoria; en producción sería una base de datos)
# =============================================================================
inventario = [
    {"id": 1, "nombre": "Coca-Cola", "precio": 20, "cantidad": 25},
    {"id": 2, "nombre": "Papas", "precio": 15, "cantidad": 40},
    {"id": 3, "nombre": "Café", "precio": 18, "cantidad": 15},
]

# =============================================================================
#  ENDPOINTS ASÍNCRONOS (async/await)
# =============================================================================

@app.get("/")
async def home():
    """
    Endpoint de bienvenida (GET /).

    OJO: aunque la función es `async`, NO siempre se debe usar `await`.
    Aquí la respuesta es inmediata y no hay ninguna operación de E/S
    (archivos, red, base de datos) que justifique esperar algo.
    """
    return {"Message": "Hola bienvenido"}


@app.get("/productos")
async def getProductos():
    """
    Consulta y muestra todos los productos del inventario (GET /productos).

    Igual que `home`: el acceso a una lista en memoria es una operación
    síncrona y rapidísima, por lo que este caso tampoco requiere `await`.
    Si el inventario viviera en una base de datos, aquí iría un
    `await db.obtener_todos()`.
    """
    return inventario


@app.post("/productos")
async def addProducto(producto: dict):
    """
    Registra (agrega) un nuevo producto al inventario (POST /productos).

    Aquí SÍ se usa `await`: se simula una operación asíncrona de E/S
    (por ejemplo, esperar la confirmación de una base de datos o de un
    servicio externo). Mientras esta corrutina espera, el bucle de eventos
    de asyncio atiende otras peticiones concurrentes sin bloquearse.
    """
    # Pausa breve que representa una operación de E/S asíncrona real
    # (p. ej. INSERT en una base de datos con await).
    await asyncio.sleep(0.05)

    # Se genera un id nuevo para el producto. Se asume que los ids son
    # consecutivos respecto a la cantidad de elementos actuales.
    nuevo_id = len(inventario) + 1
    nuevo_producto = {
        "id": nuevo_id,
        "nombre": producto["nombre"],
        "precio": producto["precio"],
        "cantidad": producto["cantidad"],
    }

    inventario.append(nuevo_producto)

    return inventario


@app.delete("/productos/{producto_id}")
async def deleteProducto(producto_id: int):
    """
    Elimina un producto del inventario según su id (DELETE /productos/{id}).

    También se usa `await` para simular la confirmación asíncrona de la
    operación (p. ej. DELETE en una base de datos) y ceder el control al
    bucle de eventos mientras tanto.
    """
    await asyncio.sleep(0.05)

    for producto in inventario:
        if producto["id"] == producto_id:
            inventario.remove(producto)
            return {"Message": "El producto fue eliminado"}
    return {"Message": "No fue encontrado el producto"}
