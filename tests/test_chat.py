import json
from pathlib import Path

import httpx
from streamlit.testing.v1 import AppTest

from escappy.storage import Storage


def test_chat_sends_selected_context_and_retries_without_duplicating(monkeypatch, tmp_path):
    database = tmp_path / "phase1.sqlite3"
    monkeypatch.setenv("ESCAPPY_DB_PATH", str(database))
    monkeypatch.setenv("OPENAI_API_KEY", "clave-de-prueba")
    monkeypatch.setenv("ESCAPPY_AI_MODEL", "modelo-de-prueba")
    store = Storage(database)
    store.initialize()
    other = store.create_conversation("Otra campaña")
    store.add_message(other, "Esta conversación es independiente")
    selected = store.create_conversation("Campaña de prueba")
    store.add_message(selected, "Propón una portada")
    store.save_memory("Preferencia", "Usar un fondo limpio")
    calls = []

    def send(client, request, **kwargs):
        assert str(request.url) == "https://api.openai.com/v1/responses"
        calls.append(json.loads(request.content))
        if len(calls) == 1:
            return httpx.Response(429, json={"error": {"message": "Prueba"}}, request=request)
        return httpx.Response(200, request=request, json={
            "id": "resp_prueba", "object": "response", "status": "completed",
            "model": "modelo-de-prueba", "created_at": 1,
            "output": [{"type": "message", "id": "msg_prueba", "role": "assistant",
                        "status": "completed", "content": [
                            {"type": "output_text", "text": "Propuesta de prueba", "annotations": []}
                        ]}],
        })

    monkeypatch.setattr(httpx.Client, "send", send)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=15).run()
    app.sidebar.radio[0].set_value("Conversaciones").run()
    last_id = store.messages(selected)[-1]["id"]
    key = f"reply-{selected}-{last_id}"
    assert not calls
    app.button(key=key).click().run()
    assert "429" in app.error[0].value
    assert len(store.messages(selected)) == 1
    app.button(key=key).click().run()
    assert not app.exception
    assert app.chat_message[-1].text[0].value == "Propuesta de prueba"
    assert len(calls) == 2
    assert calls[0] == calls[1]
    assert calls[0]["model"] == "modelo-de-prueba"
    assert calls[0]["store"] is False
    context = calls[0]["input"]
    assert len(context) == 2
    assert "Usar un fondo limpio" in context[0]["content"]
    assert context[1] == {"role": "user", "content": "Propón una portada"}
    app.run()
    assert len(calls) == 2
    assert [row["role"] for row in store.messages(selected)] == ["user", "assistant"]


def test_late_or_duplicate_reply_does_not_change_history(tmp_path):
    store = Storage(tmp_path / "test.sqlite3")
    store.initialize()
    thread = store.create_conversation("Ideas")
    store.add_message(thread, "Primer mensaje")
    old_id = store.messages(thread)[-1]["id"]
    store.add_message(thread, "Mensaje más reciente")
    new_id = store.messages(thread)[-1]["id"]
    assert not store.save_reply(thread, old_id, "Respuesta desactualizada")
    assert store.save_reply(thread, new_id, "Respuesta actual")
    assert not store.save_reply(thread, new_id, "Respuesta duplicada")
    assert [row["content"] for row in store.messages(thread)] == [
        "Primer mensaje", "Mensaje más reciente", "Respuesta actual"
    ]
