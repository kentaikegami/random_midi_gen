from flask import Flask, render_template, send_file, jsonify, request, session, send_from_directory
import mido
import random
import os
import subprocess
import time
import string
from flask_cors import CORS

app = Flask(__name__)

# 本番環境では、環境変数からセッションキーを取得
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

    mid.save(filename)
    print(f"MIDI file '{filename}' created.")
    return filename

def generate_wav(midi_file, wav_file_prefix):
    # ファイル名に時分秒とランダム文字列を追加
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    wav_file = f"{wav_file_prefix}_{timestamp}_{random_str}.wav"
import os

def generate_wav(midi_file, wav_file_prefix):
    # ファイル名に時分秒とランダム文字列を追加
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    wav_file = f"{wav_file_prefix}_{timestamp}_{random_str}.wav"
    print(f"Generating WAV file: {wav_file}")  # WAVファイル生成前のログ
    try:
        result = subprocess.run(["timidity", midi_file, "-Ow", "-o", wav_file], check=True, capture_output=True, text=True)
        print(f"WAV file '{wav_file}' created.")
        print(f"WAV file generation result: {result}")  # WAVファイル生成後のログ
        return os.path.abspath(wav_file) # 絶対パスを返す
    except subprocess.CalledProcessError as e:
        print(f"MIDI to WAV変換エラー: {e}")
        print(f"Error: {e.stderr}")
        return None

def parse_midi(midi_file):
    try:
        mid = mido.MidiFile(midi_file)
        notes = []
        for track in mid.tracks:
            for msg in track:
                if msg.type == 'note_off':
                    note_name = notetoname(msg.note)
                    note_duration = noteduration(msg.time)
                    notes.append(f"{note_name}/4,{note_duration}")  # 例: C/4, D#/5
        return notes
    except Exception as e:
        print(f"MIDI解析エラー: {e}")
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

@app.route('/generate_music', methods=['POST'])
def generate_music():
    scale = request.form.get('scale', 'major')
    base_note = request.form.get('base_note', 'C')
    # 音名の文字列をMIDIノート番号に変換
    note_map = {
        "C": 60, "C#": 61, "D": 62, "D#": 63, "E": 64, "F": 65,
        "F#": 66, "G": 67, "G#": 68, "A": 69, "A#": 70, "B": 71
    }
    base_note_value = note_map.get(base_note, 60)  # デフォルトはC (60)
    midi_file_prefix = "random_midi"
    wav_file_prefix = "random_wav"

    midi_file_path = generate_random_midi(scale, base_note_value, midi_file_prefix)
    if midi_file_path: # midi_file_path が None でないことを確認
        # 以前のファイルを削除
        if 'midi_file' in session:
            try:
                os.remove(session['midi_file'])
            except FileNotFoundError:
                pass
            session.pop('midi_file', None)
        if 'wav_file' in session:
            try:
                os.remove(session['wav_file'])
            except FileNotFoundError:
                pass
            session.pop('wav_file', None)
        wav_file_path = generate_wav(midi_file_path, wav_file_prefix)

        if wav_file_path:
            notes = parse_midi(midi_file_path)
            session['midi_file'] = midi_file_path
            session['wav_file'] = os.path.abspath(wav_file_path)
            print(f"session['wav_file']: {session['wav_file']}")
            # WAVファイルの実際のパスを返すように変更
            print(wav_file_path)
            return jsonify({'wav_file': wav_file_path, 'midi_file': '/download/midi', 'notes': notes})
        else:
            print("Failed to generate WAV file")
            return jsonify({'error': 'Failed to generate WAV file'}), 500
    else:
        print("Failed to generate MIDI file")
        return jsonify({'error': 'Failed to generate MIDI file'}), 500

@app.route('/random.wav')
def get_wav():
    print("kk")
    print("random.wavにアクセスがありました")  # アクセスログ
    try:
        # WAVファイル
        # を生成した際に使用したファイル名を返す
        if 'wav_file' in session:
            print("kookk")
            wav_file_path = session['wav_file']
            print(f"Attempting to send file: {wav_file_path}")  # ファイルパスのログ
            if os.path.exists(wav_file_path):
                print("File exists, sending...")  # ファイル存在のログ
                return send_file(wav_file_path, mimetype="audio/wav", as_attachment=False)
            else:
                print("File not found, even though it's in session")  # ファイルが存在しない場合のログ
                return jsonify({'error': 'WAV file not found'}), 404
        else:
            print("kkkkooo")
            print("セッションにwav_fileが存在しません")  # セッションログ
            return jsonify({'error': 'WAV file not found'}), 404
    except FileNotFoundError:
        print("FileNotFoundErrorが発生しました")  # エラーログ
        return jsonify({'error': 'WAV file not found'}), 404

@app.route('/download/midi')
def download_midi():
    if 'midi_file' in session:
        try:
            print(session['midi_file'])
            return send_file(
                session['midi_file'],
                as_attachment=True,
                download_name='music.mid',  # ダウンロード時のファイル名
                mimetype='audio/midi'
            )
        except FileNotFoundError:
            return jsonify({'error': 'MIDI file not found'}), 404
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
    if 'wav_file' in session:
        try:
            os.remove(session['wav_file'])
        except FileNotFoundError:
            pass
        session.pop('wav_file', None)
    return jsonify({'message': 'Session cleared'}), 200

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=port)
