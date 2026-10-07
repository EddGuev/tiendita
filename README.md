# Tiendita — API + Cliente (Programación 4)

Proyecto de administración de productos de una pequeña tienda, compuesto por dos servidores:

1. **API REST** (FastAPI, puerto `8000`) — implementa tres métodos HTTP:
   - `GET /productos` → consulta y muestra los productos del inventario.
   - `POST /productos` → agrega un nuevo producto.
   - `DELETE /productos/{id}` → elimina un producto.

2. **Cliente web** (HTML + Bootstrap + JavaScript, puerto `3000`) — consume la API mediante `fetch()`, demostrando la comunicación entre dos servidores diferentes (cliente ↔ API).

## Estructura

```
tiendita/
├── backend/
│   └── main.py          # API con FastAPI (GET, POST, DELETE)
└── frontend/
    ├── index.html       # Interfaz de la tiendita (Bootstrap)
    └── app.js           # Consumo de la API con fetch()
```

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

## Endpoints de la API

| Método | Ruta              | Descripción                            |
|--------|-------------------|----------------------------------------|
| GET    | `/`               | Mensaje de bienvenida                  |
| GET    | `/productos`      | Muestra todos los productos            |
| POST   | `/productos`      | Agrega un producto (JSON)              |
| DELETE | `/productos/{id}` | Elimina un producto por su id          |

> Nota: la API incluye middleware CORS (`allow_origins=["*"]`) para permitir la comunicación del cliente desde otro origen.
