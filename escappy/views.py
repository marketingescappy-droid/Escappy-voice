import calendar
from collections import defaultdict
from datetime import date
from html import escape

import streamlit as st

from escappy.chat import ChatError, OpenAIChatProvider
from escappy.config import openai_settings
from escappy.integrations import PLANNED_INTEGRATIONS, ChatMessage, CreativeNote
from escappy.storage import FORMATS, MEMORY_TYPES, STATUSES, Storage

MONTHS = (
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
)
WEEKDAYS = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")


def saved(message: str):
    st.session_state["flash"] = message
    st.rerun()


def shift_month(delta: int):
    current = st.session_state["editorial_month"]
    year, month = divmod(current.year * 12 + current.month - 1 + delta, 12)
    st.session_state["editorial_month"] = date(year, month + 1, 1)


def calendar_grid(month: date, ideas):
    by_day = defaultdict(list)
    for idea in ideas:
        by_day[int(idea["planned_date"][-2:])].append(idea["title"])

    headers = "".join(f"<th scope='col'>{day}</th>" for day in WEEKDAYS)
    rows = []
    for week in calendar.Calendar().monthdayscalendar(month.year, month.month):
        cells = []
        for weekday, day in zip(WEEKDAYS, week):
            if day == 0:
                cells.append("<td class='empty-day'></td>")
                continue
            titles = "".join(f"<li>{escape(title)}</li>" for title in by_day[day])
            entries = f"<ul>{titles}</ul>" if titles else ""
            cells.append(
                f"<td><strong><span class='mobile-day'>{weekday} </span>{day}</strong>"
                f"{entries}</td>"
            )
        rows.append(f"<tr>{''.join(cells)}</tr>")
    st.html(
        f"<table class='editorial-grid' aria-label='Calendario mensual'>"
        f"<thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"
    )


def idea_form(store: Storage, default_date: date, idea=None):
    idea_id = idea["id"] if idea else None
    with st.form(f"idea-{idea_id}", clear_on_submit=idea is None):
        title = st.text_input("Título", value=idea["title"] if idea else "")
        planned = st.date_input(
            "Fecha editorial",
            value=date.fromisoformat(idea["planned_date"]) if idea else default_date,
            min_value=date(1, 1, 1),
            max_value=date(9999, 12, 31),
            format="DD/MM/YYYY",
        )
        format_ = st.selectbox("Formato", FORMATS, index=FORMATS.index(idea["format"]) if idea else 0)
        status = st.selectbox("Estado", STATUSES, index=STATUSES.index(idea["status"]) if idea else 0)
        notes = st.text_area("Notas", value=idea["notes"] if idea else "")
        if st.form_submit_button("Guardar idea", type="primary"):
            try:
                if planned is None:
                    raise ValueError("Selecciona una fecha editorial.")
                store.save_idea(title, planned, format_, status, notes, idea_id)
            except ValueError as error:
                st.error(str(error))
            else:
                st.session_state["editorial_month"] = planned.replace(day=1)
                saved("Idea guardada.")


def editorial(store: Storage):
    st.title("Calendario editorial")
    st.caption("Planifica y actualiza las ideas de Instagram de Escappy Travel.")
    today = date.today()
    month = st.session_state.setdefault("editorial_month", today.replace(day=1))
    prior, now, later = st.columns(3)
    prior.button("Mes anterior", on_click=shift_month, args=(-1,), disabled=month == date(1, 1, 1))
    now.button("Este mes", on_click=lambda: st.session_state.update(editorial_month=today.replace(day=1)))
    later.button("Mes siguiente", on_click=shift_month, args=(1,), disabled=month == date(9999, 12, 1))

    last = month.replace(day=calendar.monthrange(month.year, month.month)[1])
    ideas = store.ideas(month, last)
    st.subheader(f"{MONTHS[month.month - 1]} de {month.year}")
    calendar_grid(month, ideas)
    with st.expander("Nueva idea"):
        idea_form(store, today if month == today.replace(day=1) else month)

    st.subheader("Ideas del mes")
    if not ideas:
        st.info("Todavía no hay ideas para este mes.")
    for idea in ideas:
        planned = date.fromisoformat(idea["planned_date"])
        title = escape(idea["title"], quote=False)
        with st.expander(f"{planned:%d/%m} · {title} · {idea['status']}"):
            idea_form(store, planned, idea)


def conversations(store: Storage):
    st.title("Conversaciones")
    st.caption("Guarda tus mensajes y vuelve a cualquier conversación desde el historial.")
    with st.expander("Nueva conversación"):
        with st.form("create-conversation", clear_on_submit=True):
            title = st.text_input("Nombre")
            if st.form_submit_button("Crear conversación", type="primary"):
                try:
                    st.session_state["conversation"] = store.create_conversation(title)
                except ValueError as error:
                    st.error(str(error))
                else:
                    saved("Conversación creada.")

    threads = {row["id"]: row["title"] for row in store.conversations()}
    if not threads:
        st.info("Crea una conversación para empezar a guardar mensajes.")
        return

    selected = st.selectbox(
        "Historial de conversaciones", list(threads), key="conversation",
        format_func=lambda thread_id: f"{threads[thread_id]} (n.º {thread_id})",
    )
    settings = openai_settings()
    if settings.api_key:
        st.caption("Al pedir una respuesta se envían a OpenAI este historial y la memoria creativa.")
    else:
        st.caption("Puedes guardar mensajes. Para pedir una respuesta, configura la clave indicada en Integraciones.")
    messages = store.messages(selected)
    for message in messages:
        with st.chat_message(message["role"]):
            st.text(message["content"])
            st.caption(f"{message['created_at']} UTC")
    if settings.api_key and messages and messages[-1]["role"] == "user":
        last_id = messages[-1]["id"]
        if st.button("Pedir respuesta a OpenAI", key=f"reply-{selected}-{last_id}"):
            history = [ChatMessage(row["role"], row["content"]) for row in messages]
            notes = [CreativeNote(row["kind"], row["content"]) for row in store.memory()]
            try:
                with st.spinner("Preparando respuesta…"):
                    reply = OpenAIChatProvider(settings).reply(history, notes)
            except ChatError as error:
                st.error(str(error))
            else:
                if not store.save_reply(selected, last_id, reply):
                    saved("La conversación cambió durante la consulta. Revisa los últimos mensajes.")
                st.rerun()
    if prompt := st.chat_input("Escribe un mensaje", key=f"chat-{selected}"):
        try:
            store.add_message(selected, prompt)
        except ValueError as error:
            st.error(str(error))
        else:
            st.rerun()


def memory_form(store: Storage, note=None):
    note_id = note["id"] if note else None
    with st.form(f"memory-{note_id}", clear_on_submit=note is None):
        kind = st.selectbox("Tipo", MEMORY_TYPES, index=MEMORY_TYPES.index(note["kind"]) if note else 0)
        content = st.text_area("Contenido", value=note["content"] if note else "")
        if st.form_submit_button("Guardar en memoria", type="primary"):
            try:
                store.save_memory(kind, content, note_id)
            except ValueError as error:
                st.error(str(error))
            else:
                saved("Memoria guardada.")


def memory(store: Storage):
    st.title("Memoria creativa")
    st.caption("Registra las pautas que el agente deberá tener en cuenta al crear contenido.")
    with st.expander("Nueva entrada"):
        memory_form(store)
    notes = store.memory()
    if not notes:
        st.info("Añade una instrucción, preferencia o corrección para empezar.")
    for note in notes:
        with st.expander(note["kind"]):
            st.text(note["content"])
            memory_form(store, note)


def integrations(_store: Storage):
    st.title("Integraciones")
    settings = openai_settings()
    with st.container(border=True):
        st.subheader("OpenAI")
        if settings.api_key:
            st.write(f"Modelo configurado · {settings.model}")
            st.caption("La clave se valida al pedir una respuesta desde Conversaciones.")
        else:
            st.write("Pendiente de configurar")
            st.caption("Guarda tu clave de la API en OPENAI_API_KEY en el archivo local .env.")

    for name, description in PLANNED_INTEGRATIONS.items():
        with st.container(border=True):
            st.subheader(name)
            st.write(description)
            st.caption("Estado · Pendiente")
