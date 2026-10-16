# Tiendita — API + Cliente + Pruebas de Carga (Programación 4)

Proyecto de administración de productos de una pequeña tienda, compuesto por dos servidores y una herramienta de pruebas de carga:

1. **API REST** (FastAPI, puerto `8000`) — gestión de inventario con modelos de Pydantic y `asyncio.Lock` para evitar condiciones de carrera.
2. **Cliente web** (HTML + Bootstrap + JavaScript, puerto `3000`) — consume la API con `fetch()`.
3. **Locust** — prueba de carga concurrente del endpoint de compra (venta flash).

## Estructura

```
tiendita/
├── backend/
│   └── main.py          # API con FastAPI (Pydantic + asyncio.Lock + CORS)
├── frontend/
│   ├── index.html       # Interfaz de la tiendita (Bootstrap)
│   └── app.js           # Consumo de la API con fetch()
└── locust.py            # Prueba de carga (Locust)
```

## Productos del inventario (simulación)

| ID | Producto        | Precio | Cantidad |
|----|-----------------|--------|----------|
| 1  | Galletas Maria  | 12     | 30       |
| 2  | Fanta           | 18     | 25       |
| 3  | Jugo de Naranja | 22     | 40       |
| 4  | Chocolate       | 25     | 20       |
| 5  | Agua Mineral    | 10     | 50       |
| 6  | Pan Blanco      | 15     | 12       |

## Endpoints de la API

| Método | Ruta                       | Descripción |
|--------|----------------------------|-------------|
| GET    | `/`                        | Mensaje de bienvenida (nótese la demostración de manejo de errores con try/except) |
| GET    | `/productos`               | Muestra todos los productos del inventario |
| POST   | `/productos`               | Agrega un producto (validado con Pydantic, responde 201) |
| POST   | `/productos/{producto_id}` | Compra un producto (descuenta stock con `asyncio.Lock`) |
| DELETE | `/productos/{producto_id}` | Elimina un producto |
| GET    | `/prueba-asyncio`          | Espera asíncrona de 5 segundos |
| GET    | `/prueba-asyncio-3segundos`| Espera asíncrona de 3 segundos |
| GET    | `/prueba-asyncio-1segundo` | Espera asíncrona de 1 segundo |

## Modelos de Pydantic

- `crearProducto`: valida la petición del cliente (`nombre` obligatorio, `precio > 0`, `cantidad >= 0`).
- `respuestaProducto`: define la estructura de la respuesta de la API.

La compra usa `asyncio.Lock` para que, ante compras concurrentes, el stock no baje de cero (condición de carrera).

## Cómo ejecutar

### 1. Iniciar la API (puerto 8000)

```bash
cd backend
pip install fastapi uvicorn
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Iniciar el cliente (puerto 3000)

```bash
cd frontend
python -m http.server 3000 --bind 127.0.0.1
```

Abrir en el navegador: http://127.0.0.1:3000

### 3. Prueba de carga con Locust

```bash
pip install locust
# IMPORTANTE: ejecutar desde otra carpeta (el archivo locust.py no debe
# ocultar el paquete locust):
cd ..
locust -f locust.py --host http://127.0.0.1:8000
```

Abrir la interfaz web de Locust en http://127.0.0.1:8089, elegir número de usuarios y tiempo de rampa, y comenzar la prueba.

También se puede correr sin interfaz (modo headless):

```bash
locust -f locust.py --host http://127.0.0.1:8000 --headless -u 10 -r 2 -t 30s --html locust_report.html
```

La prueba simula usuarios comprando el producto id 3 (Jugo de Naranja). Cuando el stock llega a cero, las compras fallan, demostrando la protección contra condiciones de carrera.
