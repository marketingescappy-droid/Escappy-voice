# Escappy Voice

Espacio editorial de Escappy Travel para organizar contenido de Instagram. La primera fase reúne el calendario, el historial de conversaciones y la memoria creativa en una aplicación local de Streamlit con SQLite.

## Ejecutar en Windows

Desde la raíz del repositorio, con Python 3.11 o superior, ejecuta en PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

En macOS o Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Abre [http://127.0.0.1:8501](http://127.0.0.1:8501). La aplicación escucha en la interfaz local y está pensada para uso individual.

## Flujo de trabajo

- **Calendario editorial.** Recorre los meses, crea ideas y modifica su fecha, formato, estado o notas desde «Ideas del mes».
- **Conversaciones.** Crea una conversación, guarda mensajes y vuelve a abrirla desde el historial. Después de guardar un mensaje puedes pedir una respuesta de OpenAI. Tanto el mensaje como la respuesta se conservan en SQLite.
- **Memoria creativa.** Registra y actualiza instrucciones, preferencias y correcciones.
- **Integraciones.** Consulta la configuración de OpenAI y las integraciones previstas con Canva, Google Drive, ClickUp y Higgsfield.

## Configuración y datos

SQLite crea `data/escappy.sqlite3` automáticamente. Si quieres cambiar la ubicación, copia `.env.example` a `.env` y ajusta `ESCAPPY_DB_PATH`. Una variable de entorno con ese nombre tiene prioridad. Las rutas relativas se interpretan desde la raíz del repositorio. La configuración local y las bases SQLite se excluyen de Git. Para respaldar los datos, detén Streamlit y copia el archivo de la base.

## Activar el chat con OpenAI

1. Crea una clave de proyecto desde [la plataforma de la API de OpenAI](https://platform.openai.com/api-keys). Las llamadas usan el saldo o la facturación del proyecto de la API.
2. En la carpeta de la aplicación, abre tu archivo privado `.env`. Si aún no existe, crea una copia de `.env.example` con el nombre `.env`. Conserva el valor existente de `ESCAPPY_DB_PATH` para acceder a tu memoria e historial.
3. Escribe la clave después de `OPENAI_API_KEY=`. Puedes elegir un modelo compatible con Responses mediante `ESCAPPY_AI_MODEL`; el valor inicial es `gpt-4.1-mini`. También puedes definir ambos valores como variables de entorno.
4. Abre **Conversaciones**, guarda una pregunta y pulsa **Pedir respuesta a OpenAI**. Por ejemplo, pide una propuesta de portada que explique qué pauta de la memoria aplicaría. Ese botón envía el historial de la conversación seleccionada y las entradas de la memoria creativa a OpenAI. La solicitud usa `store=false`. La memoria que recibe el modelo es la de la base de datos de esa instalación.

Si falla la consulta, el mensaje sigue disponible y puedes volver a pulsar el botón. Sin clave, las funciones locales siguen disponibles.

## Arquitectura

- `app.py` configura la apariencia, la navegación y la ubicación de SQLite.
- `escappy/views.py` contiene las pantallas y formularios de Streamlit.
- `escappy/storage.py` administra el esquema y el acceso a SQLite. El modelo de mensajes admite los roles de usuario y asistente.
- `escappy/integrations.py` define el contrato `ChatProvider` y los tipos de mensaje y pauta.
- `escappy/chat.py` implementa el proveedor con el SDK oficial de OpenAI y la API Responses.

## Pruebas

En PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

En macOS o Linux usa `.venv/bin/python` en ambos comandos. Las pruebas usan bases temporales y cubren las operaciones de SQLite y los flujos principales de Streamlit.
