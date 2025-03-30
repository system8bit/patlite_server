# パトライト制御 API

HIDAPIを使用してパトライトデバイスを制御するためのRESTful APIです。FastAPIフレームワークを使用して実装されています。

## 必要条件

- Python 3.7以上
- パトライトデバイス
- hidapiをサポートする環境

## インストール

### Mac環境向け

1. リポジトリをクローン:
   ```
   git clone https://github.com/system8bit/patlite_server.git
   cd patlite_server
   ```

2. Pythonの仮想環境を作成:
   ```
   alias python=python3
   python -m venv venv
   source venv/bin/activate
   ```

3. 依存関係をインストール:
   ```
   pip install -r requirements.txt
   ```

4. パトライトデバイスのVendor IDとProduct IDを設定:
   `app/patlite_controller.py` ファイルを開き、`VENDOR_ID`と`PRODUCT_ID`を実際のデバイスの値に変更します。
   (デフォルトでは VendorID: 0x191a, ProductID: 0x8003 に設定されています)

## 使用方法

アプリケーションを起動:
```
python run.py
```

サーバーが起動したら、以下のAPIエンドポイントが利用可能になります:

### 基本エンドポイント:
- `GET /status` - デバイス接続状態を取得
- `POST /connect` - デバイスに接続
- `POST /disconnect` - デバイスから切断
- `POST /light` - 単一の色でライトを設定
- `POST /leds` - 複数のLEDを同時に制御
- `POST /buzzer` - ブザーを設定
- `POST /buzzer/stop` - ブザーを停止
- `POST /all` - LEDとブザーをすべて一度に設定
- `POST /reset` - 全てのライトをオフにする

### シンプル操作エンドポイント:
- `POST /turn_on_red` - 赤色LEDを点灯
- `POST /turn_on_yellow` - 黄色LEDを点灯
- `POST /turn_on_green` - 緑色LEDを点灯
- `POST /turn_off_LED` - すべてのLEDを消灯
- `POST /play_buzzer` - ブザーを鳴らす (デフォルト: D7音、3回鳴動)
- `POST /buzzer/stop` - ブザーを停止

API ドキュメントは以下のURLで確認できます:
```
http://localhost:8000/docs
```

## APIの使用例

### ライトを設定する (単一の色):
```bash
curl -X POST "http://localhost:8000/light" -H "Content-Type: application/json" -d '{"color": 1, "pattern": 1}'
```

### 複数のLEDを同時に制御:
```bash
curl -X POST "http://localhost:8000/leds" -H "Content-Type: application/json" -d '{"leds": ["RED", "BLUE"]}'
```

### ブザーを設定する:
```bash
curl -X POST "http://localhost:8000/buzzer" -H "Content-Type: application/json" -d '{"sound": 6, "mode": 1}'
```

### ブザーを停止する:
```bash
curl -X POST "http://localhost:8000/buzzer/stop"
```

### LEDとブザーを同時に設定:
```bash
curl -X POST "http://localhost:8000/all" -H "Content-Type: application/json" -d '{"leds": ["RED", "GREEN"], "buzzer_sound": 6, "buzzer_mode": 3}'
```

### シンプル操作の例:

#### 赤色LEDを点灯:
```bash
curl -X POST "http://localhost:8000/turn_on_red"
```

#### 黄色LEDを点灯:
```bash
curl -X POST "http://localhost:8000/turn_on_yellow"
```

#### 緑色LEDを点灯:
```bash
curl -X POST "http://localhost:8000/turn_on_green"
```

#### すべてのLEDを消灯:
```bash
curl -X POST "http://localhost:8000/turn_off_LED"
```

#### ブザーを鳴らす (デフォルト設定):
```bash
curl -X POST "http://localhost:8000/play_buzzer"
```

#### ブザーを鳴らす (カスタム設定):
```bash
curl -X POST "http://localhost:8000/play_buzzer" -H "Content-Type: application/json" -d '{"sound": 4, "mode": 5}'
```

## パラメータ一覧

### 色と点灯パターン:
- 色 (Color):
  - 0: オフ
  - 1: 赤
  - 2: 緑
  - 3: 青
  - 4: 黄
  - 5: 紫
  - 6: シアン
  - 7: 白

- パターン (Pattern):
  - 0: オフ
  - 1: 点灯
  - 2: 点滅
  - 3: フラッシュ

### LED個別制御:
複数のLEDを同時に制御する場合は、以下の値を配列で指定します:
- "RED": 赤LED
- "YELLOW": 黄LED
- "GREEN": 緑LED
- "BLUE": 青LED
- "WHITE": 白LED

例: `{"leds": ["RED", "GREEN", "BLUE"]}`

### ブザー音階:
- 0: OFF
- 1: A6
- 2: B♭6
- 3: B6
- 4: C7
- 5: D♭7
- 6: D7
- 7: E♭7
- 8: E7
- 9: F7
- 10: G♭7
- 11: G7
- 12: A♭7
- 13: A7
- 14: デフォルト値（D7: 2349.3Hz）
- 15: 現在の設定を維持

### ブザー動作モード:
- 0: 連続動作
- 1〜15: 1〜15回動作

## コマンドデータ構造

パトライトへのコマンドは以下の形式で送信されます:

```
data[0]  = 0            # インデックス0（hidapiが自動的に追加）
data[1]  = 0x00         # コマンドバージョン（固定）
data[2]  = 0x00         # コマンドID（固定）
data[3]  = buzzer_mode  # ブザー制御
data[4]  = buzzer_sound # ブザー音階
data[5]  = led_r_y      # LED制御 (赤・黄)
data[6]  = led_g_b      # LED制御 (緑・青)
data[7]  = led_white    # LED C(白)
data[8]  = 0x00         # 予備（固定）
```

## ライセンス

[MIT License](LICENSE) 