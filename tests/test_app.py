from datetime import date
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_editorial_create_edit_and_browse(monkeypatch, tmp_path):
    monkeypatch.setenv("ESCAPPY_DB_PATH", str(tmp_path / "test.sqlite3"))
    app = AppTest.from_file(str(APP)).run()
    assert not app.exception
    assert app.title[0].value == "Calendario editorial"

    app.text_input[0].set_value("Escapadas en tren")
    app.button(key="FormSubmitter:idea-None-Guardar idea").click().run()
    assert not app.exception
    assert any("Escapadas en tren" in item.label for item in app.expander)
    app.text_input[1].set_value("Rutas de fin de semana")
    app.selectbox[3].select("En preparación")
    app.button(key="FormSubmitter:idea-1-Guardar idea").click().run()
    assert any("Rutas de fin de semana · En preparación" in item.label for item in app.expander)

    app.button[2].click().run()
    assert len(app.expander) == 1
    app.button[0].click().run()
    assert len(app.expander) == 2
    assert app.date_input[1].value == date.today()


def test_conversations_memory_and_integrations(monkeypatch, tmp_path):
    monkeypatch.setenv("ESCAPPY_DB_PATH", str(tmp_path / "test.sqlite3"))
    app = AppTest.from_file(str(APP)).run()
    app.sidebar.radio[0].set_value("Conversaciones").run()
    app.text_input[0].set_value("Campaña de otoño")
    app.button[0].click().run()
    app.chat_input[0].set_value("Ideas para un carrusel").run()
    app.text_input[0].set_value("Nueva campaña")
    app.button[0].click().run()
    assert not app.exception
    assert app.selectbox[0].value == 2
    assert len(app.chat_message) == 0

    reopened = AppTest.from_file(str(APP)).run()
    reopened.sidebar.radio[0].set_value("Conversaciones").run()
    reopened.selectbox[0].select(1).run()
    assert reopened.chat_message[0].text[0].value == "Ideas para un carrusel"

    reopened.sidebar.radio[0].set_value("Memoria creativa").run()
    reopened.selectbox[0].select("Preferencia")
    reopened.text_area[0].set_value("Usar un tono cercano")
    reopened.button[0].click().run()
    assert reopened.text[0].value == "Usar un tono cercano"

    reopened.sidebar.radio[0].set_value("Integraciones").run()
    assert {"Canva", "Google Drive", "ClickUp", "Higgsfield", "Proveedor de IA"} == {
        heading.value for heading in reopened.subheader
    }
    assert not reopened.exception
