"""Issue #01 regression tests using real handlers without starting Tk."""

import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import main
from main import AvatarEditorApp


@pytest.fixture
def app():
    state = {"-topmost": False}

    def attributes(name, value=None):
        if value is not None:
            state[name] = value
        return state[name]

    return SimpleNamespace(
        attributes=Mock(side_effect=attributes),
        image_path=None,
        current_img=Mock(),
        lbl_status=Mock(),
        load_image=Mock(),
        update=Mock(),
        push_state=Mock(),
        update_canvas=Mock(),
    )


def assert_not_topmost(app):
    assert app.attributes("-topmost") is False, (
        "ダイアログ終了後も最前面固定が有効になっています"
    )
    assert not any(
        call.args == ("-topmost", True)
        for call in app.attributes.call_args_list
    )


@pytest.mark.parametrize("path", ["selected.png", ""], ids=["selected", "cancelled"])
def test_open_image_dialog_does_not_enable_topmost(app, monkeypatch, path):
    dialog = Mock(return_value=path)
    monkeypatch.setattr(main.filedialog, "askopenfilename", dialog)

    AvatarEditorApp.open_image_dialog(app)

    assert_not_topmost(app)
    assert dialog.call_args.kwargs["parent"] is app
    if path:
        app.load_image.assert_called_once_with(path)
    else:
        app.load_image.assert_not_called()


@pytest.mark.parametrize("path", ["saved.png", ""], ids=["selected", "cancelled"])
def test_save_image_dialog_does_not_enable_topmost(app, monkeypatch, path):
    dialog = Mock(return_value=path)
    monkeypatch.setattr(main.filedialog, "asksaveasfilename", dialog)

    AvatarEditorApp.save_image(app)

    assert_not_topmost(app)
    assert dialog.call_args.kwargs["parent"] is app
    if path:
        app.current_img.save.assert_called_once_with(path, "PNG")
        assert app.image_path == path
    else:
        app.current_img.save.assert_not_called()
        assert app.image_path is None


def test_load_image_error_does_not_enable_topmost(app, monkeypatch):
    monkeypatch.setattr(main.Image, "open", Mock(side_effect=OSError("bad image")))
    error_dialog = Mock()
    monkeypatch.setattr(main.messagebox, "showerror", error_dialog)

    AvatarEditorApp.load_image(app, "broken.png")

    assert_not_topmost(app)
    error_dialog.assert_called_once()
    assert error_dialog.call_args.kwargs["parent"] is app


@pytest.mark.parametrize("error", [PermissionError("denied"), OSError("disk full")])
def test_save_error_does_not_enable_topmost(app, monkeypatch, error):
    app.image_path = "existing.png"
    app.current_img.save.side_effect = error
    error_dialog = Mock()
    monkeypatch.setattr(main.messagebox, "showerror", error_dialog)

    AvatarEditorApp.save_image(app)

    assert_not_topmost(app)
    app.current_img.save.assert_called_once_with("existing.png", "PNG")
    error_dialog.assert_called_once()
    assert error_dialog.call_args.kwargs["parent"] is app


@pytest.mark.parametrize("missing_dependency", [True, False], ids=["import-error", "processing-error"])
def test_rembg_error_does_not_enable_topmost(app, monkeypatch, missing_dependency):
    # Avoid importing rembg or downloading a model, even when installed.
    remove = Mock(side_effect=RuntimeError("processing failed"))
    monkeypatch.setitem(
        sys.modules, "rembg",
        None if missing_dependency else SimpleNamespace(remove=remove),
    )
    error_dialog = Mock()
    monkeypatch.setattr(main.messagebox, "showerror", error_dialog)

    AvatarEditorApp.apply_rembg(app)

    assert_not_topmost(app)
    error_dialog.assert_called_once()
    assert error_dialog.call_args.kwargs["parent"] is app
    if missing_dependency:
        app.push_state.assert_not_called()
    else:
        remove.assert_called_once_with(app.current_img)
