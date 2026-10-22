"""Failures must leave the editor usable and preserve the last valid state."""

import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from PIL import Image

import main
from main import AvatarEditorApp


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(main.messagebox, "showerror", Mock())
    return SimpleNamespace(
        image_path="previous.png",
        original_img=Image.new("RGBA", (2, 2)),
        current_img=Mock(),
        undo_stack=["undo"],
        redo_stack=["redo"],
        lbl_status=Mock(),
        load_image=Mock(),
        reset_zoom=Mock(),
        update_canvas=Mock(),
        update=Mock(),
        push_state=Mock(),
    )


def test_failed_load_preserves_previous_image_and_history(app, monkeypatch):
    original, current = app.original_img, app.current_img
    monkeypatch.setattr(main.Image, "open", Mock(side_effect=OSError("corrupt image")))

    AvatarEditorApp.load_image(app, "broken.png")

    assert app.image_path == "previous.png"
    assert app.original_img is original
    assert app.current_img is current
    assert app.undo_stack == ["undo"]
    assert app.redo_stack == ["redo"]
    app.update_canvas.assert_not_called()
    main.messagebox.showerror.assert_called_once()


def test_successful_load_closes_source_file(app, tmp_path, monkeypatch):
    path = tmp_path / "image.png"
    Image.new("RGB", (3, 4)).save(path)
    source = Image.open(path)
    file_handle = source.fp
    monkeypatch.setattr(main.Image, "open", Mock(return_value=source))

    AvatarEditorApp.load_image(app, str(path))

    assert app.image_path == str(path)
    assert app.current_img.mode == "RGBA"
    assert app.current_img.size == (3, 4)
    assert app.undo_stack == []
    assert app.redo_stack == []
    assert file_handle.closed
    main.messagebox.showerror.assert_not_called()


def test_conversion_failure_closes_file_and_preserves_state(app, tmp_path, monkeypatch):
    path = tmp_path / "image.png"
    Image.new("RGB", (3, 4)).save(path)
    source = Image.open(path)
    file_handle = source.fp
    original, current = app.original_img, app.current_img
    monkeypatch.setattr(source, "convert", Mock(side_effect=OSError("decode failed")))
    monkeypatch.setattr(main.Image, "open", Mock(return_value=source))

    AvatarEditorApp.load_image(app, str(path))

    assert file_handle.closed
    assert app.image_path == "previous.png"
    assert app.original_img is original
    assert app.current_img is current
    assert app.undo_stack == ["undo"]
    assert app.redo_stack == ["redo"]
    main.messagebox.showerror.assert_called_once()


def test_failed_save_as_does_not_commit_destination(app, monkeypatch):
    app.image_path = None
    monkeypatch.setattr(main.filedialog, "asksaveasfilename", Mock(return_value="denied.png"))
    app.current_img.save.side_effect = PermissionError("denied")

    AvatarEditorApp.save_image(app)

    assert app.image_path is None
    main.messagebox.showerror.assert_called_once()


def test_save_without_image_does_not_open_dialog(app, monkeypatch):
    app.image_path = None
    app.current_img = None
    dialog = Mock()
    monkeypatch.setattr(main.filedialog, "asksaveasfilename", dialog)

    AvatarEditorApp.save_image(app)

    dialog.assert_not_called()
    app.lbl_status.configure.assert_called_once()


@pytest.mark.parametrize("handler,dialog_name", [
    (AvatarEditorApp.open_image_dialog, "askopenfilename"),
    (AvatarEditorApp.save_image, "asksaveasfilename"),
])
@pytest.mark.parametrize("error", [main.tk.TclError("dialog unavailable"), OSError("unavailable")])
def test_dialog_failure_is_reported(app, monkeypatch, handler, dialog_name, error):
    app.image_path = None
    monkeypatch.setattr(main.filedialog, dialog_name, Mock(side_effect=error))

    handler(app)

    assert app.image_path is None
    app.load_image.assert_not_called()
    app.current_img.save.assert_not_called()
    main.messagebox.showerror.assert_called_once()
    assert main.messagebox.showerror.call_args.kwargs["parent"] is app


def test_failed_ai_processing_does_not_change_history(app, monkeypatch):
    original = app.current_img
    remove = Mock(side_effect=RuntimeError("processing failed"))
    monkeypatch.setitem(sys.modules, "rembg", SimpleNamespace(remove=remove))

    AvatarEditorApp.apply_rembg(app)

    assert app.current_img is original
    app.push_state.assert_not_called()
    app.update_canvas.assert_not_called()
    main.messagebox.showerror.assert_called_once()
