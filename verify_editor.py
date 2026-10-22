import os
import sys
import unittest
import tkinter as tk
from main import AvatarEditorApp

class TestAvatarEditor(unittest.TestCase):
    def test_launch_with_argument(self):
        """引数にサンプル画像パスを指定して起動した場合の動作確認"""
        sample_path = "assets/samples/sample_portrait.png"
        self.assertTrue(os.path.exists(sample_path), "Sample image must exist")
        
        app = AvatarEditorApp(sample_path)
        app.update_idletasks()
        
        # 1. 画像がロードされているか
        self.assertIsNotNone(app.original_img, "original_img must be loaded")
        self.assertIsNotNone(app.current_img, "current_img must be loaded")
        self.assertEqual(app.current_img.size, (1024, 1024))
        
        # 2. reset_zoom による初期化計算
        app.reset_zoom()
        app.update_idletasks()
        
        # 3. キャンバスに画像アイテムが描画されているか
        items = app.canvas.find_all()
        self.assertGreater(len(items), 0, "Canvas must contain rendered items")
        item_type = app.canvas.type(items[0])
        self.assertEqual(item_type, "image", "Canvas item must be of type 'image'")
        
        # 4. PhotoImageの参照がCanvasおよびアプリ本体に保持されているか
        self.assertIsNotNone(app.photo_img, "photo_img must be retained")
        self.assertIsNotNone(app.canvas.image, "canvas.image reference must be retained")
        
        # 5. ステータスバー表示
        status_text = app.lbl_status.cget("text")
        self.assertIn("読込完了: sample_portrait.png", status_text)
        
        app.destroy()
        print("✓ 引数指定起動 (sample_portrait.png) の検証に成功しました")

    def test_launch_without_argument_fallback(self):
        """引数なしで起動した場合に preset_01.png が自動ロードされるかの動作確認"""
        app = AvatarEditorApp(None)
        app.update_idletasks()
        
        # プリセット画像がロードされているか
        self.assertIsNotNone(app.original_img)
        self.assertEqual(app.current_img.size, (1024, 1024))
        
        app.reset_zoom()
        app.update_idletasks()
        
        items = app.canvas.find_all()
        self.assertGreater(len(items), 0)
        
        status_text = app.lbl_status.cget("text")
        self.assertIn("preset_01.png", status_text)
        
        app.destroy()
        print("✓ 引数なし起動 (preset_01.png 自動フォールバック) の検証に成功しました")

    def test_flood_fill_interaction(self):
        """背景塗りつぶし（クリックで背景削除）の動作確認"""
        sample_path = "assets/samples/sample_shapes.png"
        app = AvatarEditorApp(sample_path)
        app.update_idletasks()
        app.reset_zoom()
        
        # 初期状態: 背景ピクセル (10, 10) は不透明 (240, 244, 248, 255)
        pixel_before = app.current_img.getpixel((10, 10))
        self.assertEqual(pixel_before[3], 255)
        
        # 自動塗りつぶしツールで背景をクリック
        app.active_tool = "flood_fill"
        app.apply_smart_flood_fill(10, 10)
        
        # 処理後: 背景ピクセル (10, 10) が透過 (A=0) されていること
        pixel_after = app.current_img.getpixel((10, 10))
        self.assertEqual(pixel_after[3], 0, "Background pixel must be made transparent (Alpha=0)")
        
        # Undoスタックに積まれていること
        self.assertEqual(len(app.undo_stack), 1)
        
        # Undoの動作確認
        app.undo()
        pixel_undone = app.current_img.getpixel((10, 10))
        self.assertEqual(pixel_undone[3], 255, "Undo must restore transparent pixel to original")
        
        app.destroy()
        print("✓ 背景削除（Flood Fill透過処理 & Undo）の検証に成功しました")

if __name__ == "__main__":
    unittest.main()
