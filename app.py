import sqlite3

import streamlit as st

from escappy.config import database_path
from escappy.storage import Storage
from escappy.views import conversations, editorial, integrations, memory

PAGES = {
    "Calendario editorial": editorial,
    "Conversaciones": conversations,
    "Memoria creativa": memory,
    "Integraciones": integrations,
}

st.set_page_config(page_title="Escappy Voice", page_icon="🌿", layout="wide")
st.html("""
<style>
    .stMainBlockContainer { max-width: 72rem; }
    .editorial-grid { width: 100%; table-layout: fixed; border-collapse: collapse; }
    .editorial-grid td, .editorial-grid th {
        border: 1px solid #d8e6d4; padding: .55rem; vertical-align: top;
    }
    .editorial-grid th { background: #eaf3e7; }
    .editorial-grid td { background: white; height: 3rem; overflow-wrap: anywhere; }
    .editorial-grid .empty-day { background: #f1f6ef; }
    .editorial-grid li { margin: .25rem 0; border-left: 3px solid #49b232; padding-left: .35rem; }
    .editorial-grid ul { list-style: none; margin: 0; padding: 0; }
    .mobile-day { display: none; }
    @media (max-width: 600px) {
        .editorial-grid, .editorial-grid tbody, .editorial-grid tr { display: block; }
        .editorial-grid thead, .editorial-grid .empty-day { display: none; }
        .editorial-grid td { display: block; height: auto; }
        .editorial-grid tr + tr { margin-top: .5rem; }
        .mobile-day { display: inline; }
    }
</style>
""")

st.sidebar.header("Escappy Voice")
st.sidebar.caption("Escappy Travel · Contenido de Instagram")
page = st.sidebar.radio("Navegación", tuple(PAGES))
if flash := st.session_state.pop("flash", None):
    st.success(flash)

store = Storage(database_path())
try:
    store.initialize()
    PAGES[page](store)
except (OSError, sqlite3.Error):
    st.error("No se pudo acceder a la base de datos. Revisa la ruta y los permisos y vuelve a intentarlo.")
