import sqlite3
from datetime import date

import pytest

from escappy.storage import Storage


@pytest.fixture
def store(tmp_path):
    store = Storage(tmp_path / "data" / "test.sqlite3")
    store.initialize()
    return store


def test_save_edit_and_filter_ideas(store):
    november = date(2026, 11, 20)
    december = date(2026, 12, 2)
    idea = store.save_idea(" Escapada ", november, "Carrusel", "Idea", " Costas ")
    assert store.ideas(november, november)[0]["notes"] == "Costas"

    store.save_idea("Viaje en tren", december, "Reel", "Programada", "", idea)
    assert store.ideas(november, november) == []
    updated = store.ideas(december, december)[0]
    assert (updated["id"], updated["title"], updated["format"], updated["status"]) == (
        idea, "Viaje en tren", "Reel", "Programada"
    )


def test_conversations_persist_and_preserve_message_order(store):
    first = store.create_conversation("Calendario")
    second = store.create_conversation("Destinos")
    store.add_message(first, "Hola")
    store.add_message(first, "Respuesta de prueba", role="assistant")
    store.add_message(second, "Otra conversación")

    reopened = Storage(store.path)
    reopened.initialize()
    assert [thread["id"] for thread in reopened.conversations()] == [second, first]
    assert [(row["role"], row["content"]) for row in reopened.messages(first)] == [
        ("user", "Hola"), ("assistant", "Respuesta de prueba")
    ]
    with pytest.raises(sqlite3.IntegrityError):
        reopened.add_message(999, "Mensaje huérfano")


@pytest.mark.parametrize("kind", ["Instrucción", "Preferencia", "Corrección"])
def test_creative_memory_persists_and_updates(store, kind):
    note_id = store.save_memory(kind, "Usar un tono cercano")
    reopened = Storage(store.path)
    assert reopened.memory()[0]["kind"] == kind
    reopened.save_memory(kind, "Usar ejemplos concretos", note_id)
    assert [(row["id"], row["content"]) for row in store.memory()] == [
        (note_id, "Usar ejemplos concretos")
    ]


def test_empty_text_is_rejected(store):
    with pytest.raises(ValueError):
        store.create_conversation(" ")
    with pytest.raises(ValueError):
        store.save_memory("Corrección", "\n")
    with pytest.raises(ValueError):
        store.save_idea("", date.today(), "Reel", "Idea", "")
    thread = store.create_conversation("Contenido")
    with pytest.raises(ValueError):
        store.add_message(thread, " ")
    assert store.messages(thread) == []
