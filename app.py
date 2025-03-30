from flask import Flask, render_template, send_file, jsonify, request, session, send_from_directory
import mido
import random
import os
import subprocess
import time
import string
from flask_cors import CORS
import datetime

app = Flask(__name__)

from flask_session import Session
# 音声ファイルの保存ディレクトリ
UPLOAD_FOLDER = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# セッションの設定
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(hours=1)
Session(app)

# 本番環境では、環境変数からセッションキーを取得
import datetime

app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24)

# 本番環境では、特定のオリジンのみを許可
allowed_origins = os.environ.get('ALLOWED_ORIGINS')
if allowed_origins:
    CORS(app, resources={r"/*": {"origins": allowed_origins.split(",")}})
else:
    CORS(app)  # すべてのオリジンを許可 (開発用)


# ポートを環境変数から取得
port = int(os.environ.get('PORT', 5001))

def generate_random_midi(scale, base_note, filename_prefix):
    # ファイル名に時分秒とランダム文字列を追加
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    filename = f"{filename_prefix}_{timestamp}_{random_str}.mid"
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # ピアノの音色を設定
    track.append(mido.Message('program_change', program=0, time=0))

    num_notes = random.randint(10, 30)
    prev_note = None
    if scale == "major":
        scale_notes = [0, 2, 4, 5, 7, 9, 11]  # Cメジャースケールの相対音程
    elif scale == "minor":
        scale_notes = [0, 2, 3, 5, 7, 8, 10]  # Cマイナースケールの相対音程
    else:
        scale_notes = [0, 2, 4, 5, 7, 9, 11]  # デフォルトはCメジャー
    note_probabilities = {}
    for i in range(12):
        if i in scale_notes:
            note_probabilities[i] = 0.95 / len(scale_notes)  # スケールの音程は80%の確率で均等に選択
        else:
            note_probabilities[i] = 0.05 / (12 - len(scale_notes))  # それ以外の音程は20%の確率で均等に選択

    for _ in range(num_notes):
        velocity = random.randint(40, 100)
        duration = random.choice([120, 240, 480])  # Quarter, half, whole notes
        if prev_note is not None:
            # 確率に基づいて音程を選択
            note_offset = random.choices(list(note_probabilities.keys()), weights=list(note_probabilities.values()), k=1)[0]
            note = max(24, min(base_note + note_offset, 108))
        else:
            # 最初の音符は確率に基づいて選択
            note_offset = random.choices(list(note_probabilities.keys()), weights=list(note_probabilities.values()), k=1)[0]
            note = base_note + note_offset  # C4を基準とする
        track.append(mido.Message('note_on', note=note, velocity=velocity, time=0))
        track.append(mido.Message('note_off', note=note, velocity=0, time=duration))
        prev_note = note


    mid.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    print(f"MIDI file '{filename}' created.")
    return filename

async def generate_mp3(midi_file, mp3_file_prefix):
    # ファイル名に時分秒とランダム文字列を追加
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    mp3_file = f'{mp3_file_prefix}_{timestamp}_{random_str}.mp3'
    print(f'⚫︎Generating MP3 file: {mp3_file}')
    timidity_path = "/usr/bin/timidity"
    lame_path = "/usr/bin/lame"
    timidity_process = None  # 初期化
    try:
        midi_file = os.path.abspath(midi_file)
        from pydub import AudioSegment

        if os.path.exists(mp3_file):
            os.remove(mp3_file)
        wav_file = "temp.wav"
        timidity_process = subprocess.Popen(
            [timidity_path, midi_file, "-Ow", "-s", "44100", "-d", "16", "-o", wav_file],
            stderr=subprocess.PIPE,
        )
        timidity_stdout, timidity_stderr = timidity_process.communicate()

        if timidity_process.returncode != 0:
            print(f"Timidity エラー: {timidity_stderr.decode('utf-8') if timidity_stderr else ''}")
            print(f"Timidity return code: {timidity_process.returncode}")
            return None
        try:
            # pydubを使用してwavファイルをmp3ファイルに変換
            sound = AudioSegment.from_wav(wav_file)
            mp3_file_path = os.path.join(app.config['UPLOAD_FOLDER'], mp3_file)
            sound.export(mp3_file_path, format="mp3")

            print(f"MP3 file '{mp3_file}' created.")
            if os.path.exists(mp3_file_path):
                print("生成されてるよ")
            else:
                print("生成されてないよ")
            mp3_file = os.path.abspath(mp3_file_path)
            print(f"MP3ファイルの絶対パス: {mp3_file}")
            return mp3_file
        except Exception as e:
            print(f"pydubエラー: {e}")
            print(f"pydubエラーの詳細: {str(e)}")
            return None
    except FileNotFoundError as e:
        print(f"必要なファイルが見つかりません: {e}")
        return None
    except subprocess.CalledProcessError as e:
        print(f"MIDI to MP3変換エラー: {e}")
        print(f"Error: {e.stderr.decode('utf-8') if e.stderr else ''}")
        print(f"Return Code: {e.returncode}")
        return None
    except Exception as e:
        print(f"MIDI to MP3変換エラー: {e}")
        return None
    finally:
        if timidity_process is not None and timidity_process.stdout is not None:
            timidity_process.stdout.close()

def parse_midi(midi_file):
    try:
        mid = mido.MidiFile(midi_file)
        notes = []
        for track in mid.tracks:
            for msg in track:
                if msg.type == 'note_off':
                    note_name = notetoname(msg.note)
                    note_duration = noteduration(msg.time)
                    notes.append(f'{note_name}/4,{note_duration}')  # 例: C/4, D#/5
        return notes
    except Exception as e:
        print(f"MIDI解析エラーが発生しました: {e}")
        return None

def notetoname(note):
    work=note%12
    match work:
        case 0:
            name = "C"
        case 1:
            name ="C#"
        case 2:
            name ="D"
        case 3:
            name ="D#"
        case 4:
            name = "E"
        case 5:
            name ="F"
        case 6:
            name ="F#"
        case 7:
            name ="G"
        case 8:
            name ="G#"
        case 9:
            name ="A"
        case 10:
            name ="A#"
        case 11:
            name ="B"
    return name

def noteduration(duration):
    match duration:
        case 120:
            val = "q"
        case 240:
            val = "h"
        case 480:
            val = "w"
    return val


@app.route('/')
def index():
    return render_template('index.html')

import asyncio

@app.route('/generate_music', methods=['POST'])
async def generate_music():
    print("generate_music関数が呼び出されました")  # ログ
    scale = request.form.get('scale', 'major')
    base_note = request.form.get('base_note', 'C')
    # 音名の文字列をMIDIノート番号に変換
    note_map = {
        "C": 60, "C#": 61, "D": 62, "D#": 63, "E": 64, "F": 65,
        "F#": 66, "G": 67, "G#": 68, "A": 69, "A#": 70, "B": 71
    }
    base_note_value = note_map.get(base_note, 60)  # デフォルトはC (60)
    midi_file_prefix = "random_midi"
    mp3_file_prefix = "random_mp3"


    midi_file_path = generate_random_midi(scale, base_note_value, midi_file_prefix)
    if midi_file_path: # midi_file_path が None でないことを確認
        if 'midi_file' in session:
            print("過去のmidiがあるよ")
            try:
                os.remove(session['midi_file'])
            except FileNotFoundError:
        # 以前のファイルを削除
                pass
            session.pop('midi_file', None)
        print(f'midi_file_path={midi_file_path}')
        if 'mp3_file' in session:
            try:
                os.remove(session['mp3_file'])
            except FileNotFoundError:
                pass
            session.pop('mp3_file', None)
        
        mp3_file_path = None  # 初期化
        print("generate_mp3関数を呼び出します")  # ログ
        try:
            mp3_file_path = await generate_mp3(midi_file_path, mp3_file_prefix)
            print(f"generate_mp3の戻り値：{mp3_file_path}")
        except Exception as e:
            print(f"MP3生成中にエラーが発生しました: {e}")
            return jsonify({'error': f"MP3生成中にエラーが発生しました: {e}"}), 500

        if mp3_file_path:
            print("MP3ファイルの生成に成功しました")
            notes = parse_midi(midi_file_path)
            if notes:
                print("楽譜の生成に成功しました")
                session['midi_file'] = midi_file_path
                session['mp3_file'] = mp3_file_path
                print(f"session['mp3_file']: {session['mp3_file']}")
                # MP3ファイルの実際のパスを返すように変更
                return jsonify({'wav_file': 'mp3_file', 'midi_file': '/download/midi', 'notes': notes})
            else:
                print("楽譜の生成に失敗しました")
                return jsonify({'error': 'Failed to generate score'}), 500
        else:
            print("MP3ファイルの生成に失敗しました")
            return jsonify({'error': 'Failed to generate MP3 file'}), 500
    else:
        print("MIDIファイルの生成に失敗しました")
        return jsonify({'error': 'Failed to generate MIDI file'}), 500

@app.route('/random.mp3')
def get_mp3():
    print("random.mp3にアクセスがありました")
    try:
        if 'mp3_file' in session:
            mp3_file_path = session['mp3_file']
            print(f"Attempting to send file: {mp3_file_path}")
            time.sleep(1)
            try:
                return send_file(mp3_file_path, mimetype="audio/mpeg")
            except FileNotFoundError as e:
                print("FileNotFoundErrorが発生しました")
                print(f"FileNotFoundErrorの詳細: {str(e)}")  # エラーの詳細を出力
                return jsonify({'error': 'MP3 file not found'}), 404
        else:
            print("MP3 file not found in session")
            return jsonify({'error': 'MP3 file not found'}), 404
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        print(f"エラーの詳細: {str(e)}")  # エラーの詳細を出力
        return jsonify({'error': 'MP3 file not found'}), 500

@app.route('/download/midi')
def download_midi():
    print("download midi function")
    if 'midi_file' in session:
        midi_file_path = session['midi_file']
        # ファイル名を取得
        filename = os.path.basename(midi_file_path)
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            filename,
            as_attachment=True,
            download_name='music.mid',  # ダウンロード時のファイル名
            mimetype='audio/midi'
        )
    else:
        return jsonify({'error': 'MIDI file not found'}), 404

@app.route('/clear_session', methods=['POST'])
def clear_session():
    # セッションクリア時にファイルを削除する処理を移動
    if 'midi_file' in session:
        try:
            os.remove(session['midi_file'])
        except FileNotFoundError:
            pass
        session.pop('midi_file', None)
    if 'mp3_file' in session:
        try:
            os.remove(session['mp3_file'])
        except FileNotFoundError:
            pass
        session.pop('mp3_file', None)
    return jsonify({'message': 'Session cleared'}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=port)
