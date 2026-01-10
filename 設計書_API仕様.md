# ランダムMIDI音楽生成アプリケーション - API仕様書

## 1. エンドポイント一覧

| メソッド | パス | 説明 | 認証 |
|---------|------|------|------|
| GET | `/` | トップページ表示 | 不要 |
| POST | `/generate_music` | 音楽生成 | 不要 |
| GET | `/random.mp3` | MP3ファイル取得 | 不要 |
| GET | `/download/midi` | MIDIファイルダウンロード | 不要 |
| POST | `/clear_session` | セッションクリア | 不要 |

## 2. リクエスト/レスポンス詳細

### 2.1 GET /
**説明**: トップページ（index.html）を表示

**リクエスト**:
- クエリパラメータ: なし

**レスポンス（成功）**:
- Status: 200 OK
- Content-Type: text/html
- Body: index.htmlの内容

### 2.2 POST /generate_music
**説明**: ランダム音楽生成

**リクエスト**:
- Content-Type: `application/x-www-form-urlencoded`
- Body:
  - `scale`: "major" | "minor"（デフォルト: "major"）
  - `base_note`: "C" | "C#" | "D" | ... | "B"（デフォルト: "C"）

**入力バリデーション**:
- **scale**: 値が "major" または "minor" 以外の場合は HTTP 400 エラー返却
- **base_note**: 値が C, C#, D, D#, E, F, F#, G, G#, A, A#, B 以外の場合は HTTP 400 エラー返却

**処理フロー**:
1. パラメータ取得・バリデーション（無効な値の場合は HTTP 400で終了）
2. base_noteを音名からMIDIノート番号に変換
3. MIDI生成、MP3変換、楽譜解析を実行
4. セッションにファイルパスを保存
5. JSONレスポンス返却

**レスポンス（成功）**:
- Status: 200 OK
- Content-Type: application/json
- Body:
```json
{
  "wav_file": "mp3_file",
  "midi_file": "/download/midi",
  "notes": ["C/4,q", "D/4,h", "E/4,w", ...]
}
```

**レスポンス（バリデーションエラー）**:
- Status: 400 Bad Request
- Content-Type: application/json
- Body:
```json
{
  "error": "Invalid scale. Must be one of: major, minor" | "Invalid base note. Must be one of: A, A#, B, C, ..."
}
```

**レスポンス（その他エラー）**:
- Status: 500 Internal Server Error
- Content-Type: application/json
- Body:
```json
{
  "error": "Failed to generate MIDI file" | "Failed to generate MP3 file" | "Failed to generate score" | "MP3 generation error: ..."
}
```

### 2.3 GET /random.mp3
**説明**: MP3ファイル取得（セッション内の最新MP3）

**リクエスト**:
- クエリパラメータ: `タイムスタンプ`（キャッシュ回避用、例: ?1703001600000）

**処理フロー**:
1. セッションからmp3_fileパスを取得
2. ファイルパスのセキュリティチェック（UPLOAD_FOLDER内か確認）
3. ファイル存在確認
4. ファイルを送信

**レスポンス（成功）**:
- Status: 200 OK
- Content-Type: audio/mpeg
- Content-Disposition: inline (ブラウザ再生)
- Body: MP3ファイルのバイナリデータ

**レスポンス（セッションなし）**:
- Status: 404 Not Found
- Content-Type: application/json
- Body:
```json
{
  "error": "MP3 file not found"
}
```

**レスポンス（ファイル削除済み）**:
- Status: 404 Not Found
- Content-Type: application/json
- Body:
```json
{
  "error": "MP3 file not found"
}
```

**レスポンス（パストラバーサル試行）**:
- Status: 403 Forbidden
- Content-Type: application/json
- Body:
```json
{
  "error": "Invalid file path"
}
```

**レスポンス（その他エラー）**:
- Status: 500 Internal Server Error
- Content-Type: application/json
- Body:
```json
{
  "error": "MP3 file not found"
}
```

### 2.4 GET /download/midi
**説明**: MIDIファイルダウンロード

**リクエスト**:
- クエリパラメータ: なし

**処理フロー**:
1. セッションからmidi_fileパスを取得
2. ファイルパスのセキュリティチェック（UPLOAD_FOLDER内か確認）
3. ファイルを送信（ダウンロード属性付き）

**レスポンス（成功）**:
- Status: 200 OK
- Content-Type: audio/midi
- Content-Disposition: attachment; filename="music.mid"
- Body: MIDIファイルのバイナリデータ

**レスポンス（セッションなし）**:
- Status: 404 Not Found
- Content-Type: application/json
- Body:
```json
{
  "error": "MIDI file not found"
}
```

**レスポンス（パストラバーサル試行）**:
- Status: 403 Forbidden
- Content-Type: application/json
- Body:
```json
{
  "error": "Invalid file path"
}
```

### 2.5 POST /clear_session
**説明**: セッションクリア（生成ファイル削除）

**リクエスト**:
- Content-Type: `application/x-www-form-urlencoded` または空

**処理フロー**:
1. セッション内のmidi_file, mp3_fileパスを取得
2. ファイルシステムからファイルを削除（エラーは無視）
3. セッションキーを削除
4. 成功メッセージを返却

**レスポンス（成功）**:
- Status: 200 OK
- Content-Type: application/json
- Body:
```json
{
  "message": "Session cleared"
}
```

## 3. セッション管理

### 3.1 セッション設定
- **タイプ**: ファイルシステムベース（Flask-Session）
- **有効期限**: 1時間（3600秒）
- **保存ディレクトリ**: `flask_session/`（サーバー起動時に自動作成）
- **保存データ**:
  - `midi_file`: MIDIファイルの絶対パス（string）
  - `mp3_file`: MP3ファイルの絶対パス（string）

### 3.2 セッションキー
- 環境変数`SECRET_KEY`から取得
- 未設定時は`os.urandom(24)`で24バイトのランダムキーを生成
- **本番環境での推奨**: 環境変数に固定値を設定

### 3.3 セッション有効期限の扱い
```python
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(hours=1)
```
- 1時間アクセスがない場合、セッションは自動削除される
- セッションクリア時に手動でファイルも削除される

## 4. CORS設定

### 4.1 開発環境
```python
CORS(app)  # すべてのオリジンを許可
```

### 4.2 本番環境
```python
allowed_origins = os.environ.get('ALLOWED_ORIGINS')
if allowed_origins:
    CORS(app, resources={r"/*": {"origins": allowed_origins.split(",")}})
```

**設定例**:
```bash
export ALLOWED_ORIGINS="https://example.com,https://www.example.com,https://api.example.com"
```

## 5. エラーハンドリング

### 5.1 HTTPステータスコード
| コード | 説明 | シナリオ |
|--------|------|---------|
| 200 | OK | リクエスト成功 |
| 400 | Bad Request | 無効なパラメータ（scale, base_note） |
| 403 | Forbidden | パストラバーサル試行など不正なファイルアクセス |
| 404 | Not Found | セッション/ファイルなし |
| 500 | Internal Server Error | MIDI/MP3生成失敗、予期しない例外 |

### 5.2 エラーレスポンス形式
```json
{
  "error": "エラーメッセージ（英語）"
}
```

**エラーメッセージ例**:
- `"Invalid scale. Must be one of: major, minor"`
- `"Invalid base note. Must be one of: A, A#, B, C, ..."`
- `"Failed to generate MIDI file"`
- `"Failed to generate MP3 file"`
- `"Failed to generate score"`
- `"MP3 generation error: ..."`
- `"MP3 file not found"`
- `"MIDI file not found"`
- `"Invalid file path"`

### 5.3 エラーの優先順位
POST /generate_music での処理順序に従う：
1. パラメータバリデーション失敗 → HTTP 400 (Invalid scale/base note)
2. MIDI生成失敗 → HTTP 500 (Failed to generate MIDI file)
3. MP3生成失敗 → HTTP 500 (Failed to generate MP3 file)
4. MIDI解析失敗 → HTTP 500 (Failed to generate score)

## 6. セキュリティ仕様

### 6.1 セッションセキュリティ
- **セッションキー**: 環境変数`SECRET_KEY`から取得（本番環境推奨）
- **セッションタイプ**: ファイルシステムベース（サーバー側保存）
- **有効期限**: 1時間で自動削除
- **同時実行**: 複数ブラウザ・タブは独立したセッション

### 6.2 ファイルセキュリティ
- **ファイル名**: タイムスタンプ + ランダム文字列で一意性を確保
- **ファイルアクセス制限**: セッション経由でのみアクセス可能
- **パストラバーサル対策**: `is_safe_path()` 関数でファイルパスを検証し、UPLOAD_FOLDER内にあることを確認
- **ファイル削除**: `safe_remove_file()` 関数で権限チェック・ログ記録を実施
  - セッションクリア時・有効期限切れ時に自動削除
  - 削除失敗時はログに記録し、エラーは無視
- **ディレクトリ制限**: `static/`ディレクトリのみにファイルを保存

### 6.3 CORS設定
- **開発環境**: すべてのオリジンを許可
- **本番環境**: 環境変数で指定したオリジンのみ許可
