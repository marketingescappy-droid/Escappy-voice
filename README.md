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
- **Conversaciones.** Crea una conversación, guarda mensajes y vuelve a abrirla desde el historial. Los mensajes se guardan en SQLite y las respuestas automáticas quedan para la integración con IA.
- **Memoria creativa.** Registra y actualiza instrucciones, preferencias y correcciones.
- **Integraciones.** Consulta el estado de Canva, Google Drive, ClickUp, Higgsfield y el proveedor de IA. Los conectores están pendientes.

## Configuración y datos

SQLite crea `data/escappy.sqlite3` automáticamente. Si quieres cambiar la ubicación, copia `.env.example` a `.env` y ajusta `ESCAPPY_DB_PATH`. Una variable de entorno con ese nombre tiene prioridad. Las rutas relativas se interpretan desde la raíz del repositorio. La configuración local y las bases SQLite se excluyen de Git. Para respaldar los datos, detén Streamlit y copia el archivo de la base.

## Arquitectura

- `app.py` configura la apariencia, la navegación y la ubicación de SQLite.
- `escappy/views.py` contiene las pantallas y formularios de Streamlit.
- `escappy/storage.py` administra el esquema y el acceso a SQLite. El modelo de mensajes admite los roles de usuario y asistente.
- `escappy/integrations.py` enumera las integraciones previstas y define el contrato `ChatProvider`. Un proveedor futuro recibirá el historial ordenado y la memoria creativa. Su respuesta podrá persistirse con el rol `assistant`. Los adaptadores de servicios externos pueden incorporarse a este módulo o su propio paquete, fuera de las pantallas.

## Pruebas

En PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

En macOS o Linux usa `.venv/bin/python` en ambos comandos. Las pruebas usan bases temporales y cubren las operaciones de SQLite y los flujos principales de Streamlit.
