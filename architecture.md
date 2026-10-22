# Artemis Background Remover — アーキテクチャ図

## 1. 全体構成（コンポーネント依存関係）

```mermaid
graph TD
    subgraph EntryPoint["エントリポイント"]
        MAIN["main.py\n__main__ block\nL924"]
    end

    subgraph App["AvatarEditorApp クラス (main.py L57)"]
        INIT["__init__()\nL58\n初期化・状態変数定義"]
        SETUP["setup_ui()\nL108\nウィジェット構築"]
        LOAD["load_image()\nL396\n画像読み込み・状態初期化"]
        FALLBACK["load_fallback_image()\nL412\nフォールバック画像生成"]
        DIALOG["open_image_dialog()\nL433\nファイル選択ダイアログ"]
        SAVE["save_image()\nL444\nPNG保存"]
        UNDO["undo() / redo()\nL486 / L495\n履歴操作"]
        PUSH["push_state()\nL479\n編集前スナップショット保存"]

        subgraph Editing["編集ロジック"]
            REMBG["apply_rembg()\nL539\nAI背景除去"]
            FLOOD["apply_smart_flood_fill()\nL568\nフラッドフィル消去"]
            BRUSH["apply_brush()\nL625\n手動ブラシ編集"]
        end

        subgraph Viewport["ビューポート・レンダリングエンジン"]
            CANVAS_UPDATE["update_canvas()\nL788\n描画エンジン本体"]
            ZOOM_IN["zoom_in() / zoom_out()\nL377 / L387"]
            RESET_ZOOM["reset_zoom()\nL652"]
            PAN["start_pan() / pan_image()\nL704 / L708\nドラッグパン"]
        end

        subgraph Events["イベントハンドラ"]
            CLICK["on_canvas_click()\nL746"]
            DRAG["on_canvas_drag()\nL764"]
            SCROLL["on_scroll_y/x() / on_zoom()\nL676 / L681 / L686"]
            RESIZE["on_canvas_resize()\nL778"]
        end
    end

    subgraph Config["設定ファイル"]
        THEME["theme.py\nカラーパレット・フォント定数"]
    end

    subgraph ExternalLibs["外部ライブラリ"]
        PILLOW["Pillow\n画像操作・RGBA合成\nImage, ImageTk"]
        REMBG_LIB["rembg\nAI背景除去エンジン"]
        NUMPY["numpy\nピクセルマスク処理"]
        CTK["customtkinter\nモダンGUIウィジェット"]
        TK["tkinter\nキャンバス・イベント・ダイアログ"]
    end

    %% 起動フロー
    MAIN --> INIT
    INIT --> SETUP
    INIT --> FALLBACK

    %% テーマ読み込み
    THEME -->|"カラー定数 import"| INIT

    %% UI操作 → ロジック
    DIALOG --> LOAD
    LOAD --> CANVAS_UPDATE
    FALLBACK --> CANVAS_UPDATE

    %% 編集操作フロー
    CLICK --> FLOOD
    CLICK --> BRUSH
    DRAG --> BRUSH
    REMBG --> PUSH
    FLOOD --> PUSH
    BRUSH --> PUSH
    PUSH --> UNDO

    %% 編集後 → 再描画
    REMBG --> CANVAS_UPDATE
    FLOOD --> CANVAS_UPDATE
    BRUSH --> CANVAS_UPDATE
    UNDO --> CANVAS_UPDATE

    %% ビューポート操作
    SCROLL --> ZOOM_IN
    SCROLL --> CANVAS_UPDATE
    ZOOM_IN --> CANVAS_UPDATE
    RESET_ZOOM --> CANVAS_UPDATE
    PAN --> CANVAS_UPDATE
    RESIZE --> CANVAS_UPDATE

    %% 外部ライブラリ依存
    CANVAS_UPDATE -->|"crop / resize / paste"| PILLOW
    CANVAS_UPDATE -->|"ImageTk.PhotoImage"| PILLOW
    LOAD -->|"Image.open / convert(RGBA)"| PILLOW
    REMBG -->|"remove(image)"| REMBG_LIB
    FLOOD -->|"numpy配列操作"| NUMPY
    BRUSH -->|"numpy配列操作"| NUMPY
    SETUP -->|"CTkButton / CTkSlider 等"| CTK
    SETUP -->|"Canvas / filedialog"| TK
```

---

## 2. 画像アップロード → プレビュー表示のデータフロー

```mermaid
sequenceDiagram
    actor User as ユーザー
    participant Dialog as open_image_dialog()<br/>L433
    participant Loader as load_image()<br/>L396
    participant State as AvatarEditorApp<br/>内部状態
    participant Engine as update_canvas()<br/>L788
    participant Pillow as Pillow (Image/ImageTk)
    participant Canvas as tkinter.Canvas

    User->>Dialog: 「開く」ボタンをクリック
    Dialog->>Dialog: filedialog.askopenfilename() でパス取得
    Dialog->>Loader: load_image(path) を呼び出し
    Loader->>Pillow: Image.open(path).convert("RGBA")
    Pillow-->>Loader: PIL Image (RGBA)
    Loader->>State: original_img / current_img をセット
    Loader->>State: undo_stack / redo_stack をクリア
    Loader->>State: reset_zoom() でズームを初期化
    Loader->>Engine: update_canvas() を呼び出し

    Engine->>Engine: キャンバスの可視領域 (Viewport) を計算
    Engine->>Engine: ズーム後サイズ計算 (iw × zoom_level)
    Engine->>Pillow: current_img.crop(可視領域) — 見える部分のみ切り出し
    Engine->>Pillow: 背景画像生成（市松模様 / 黒 / 白）
    Engine->>Pillow: cropped_img.resize() でリサイズ
    Engine->>Pillow: bg.paste(resized_crop, mask=alpha) で合成
    Engine->>Pillow: ImageTk.PhotoImage(bg) に変換
    Pillow-->>Engine: PhotoImage オブジェクト
    Engine->>Canvas: canvas.create_image(cx, cy, image=photo)
    Canvas-->>User: 画像がプレビュー表示される
```

---

## 3. 編集操作のデータフロー（Undo/Redo 含む）

```mermaid
sequenceDiagram
    actor User as ユーザー
    participant Click as on_canvas_click()<br/>L746
    participant PushState as push_state()<br/>L479
    participant EditOp as 編集関数<br/>(flood_fill / brush / rembg)
    participant State as current_img<br/>(PIL Image RGBA)
    participant UndoStack as undo_stack / redo_stack
    participant Engine as update_canvas()<br/>L788

    User->>Click: キャンバスをクリック
    Click->>PushState: 編集前スナップショットを保存
    PushState->>UndoStack: current_img.copy() を push
    Click->>EditOp: apply_smart_flood_fill() or apply_brush()
    EditOp->>State: numpy でアルファ値を書き換え
    State-->>EditOp: 更新済み current_img
    EditOp->>Engine: update_canvas()
    Engine-->>User: 編集結果がリアルタイムで反映

    Note over User, UndoStack: Undo 操作
    User->>UndoStack: undo()  [L486]
    UndoStack-->>State: スタックから current_img を復元
    State->>Engine: update_canvas()
    Engine-->>User: 1つ前の状態に戻る
```

---

## 4. ファイル構成

```
artemis-bg-remover/
├── main.py           # アプリ全体（AvatarEditorApp クラス、936行）
├── theme.py          # カラーパレット・フォント・レイアウト定数
├── requirements.txt  # 依存ライブラリ定義
├── README.md         # セットアップ・使い方ドキュメント
├── architecture.md   # このファイル（アーキテクチャ図）
├── mkdocs.yml        # ドキュメントサイト設定
├── docs/             # ドキュメント格納ディレクトリ
└── .github/          # GitHub Actions 等の設定
```
