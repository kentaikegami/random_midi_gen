from flask import Flask, render_template, send_file, jsonify, request, session, send_from_directory, make_response
import mido
import random
import os
import subprocess
import time
import string
from flask_cors import CORS
import datetime
import logging

app = Flask(__name__)

from flask_session import Session

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
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

# ファイル操作の安全性チェック
def is_safe_path(filepath):
    """ファイルパスがUPLOAD_FOLDER内にあることを確認"""
    try:
        base = os.path.abspath(UPLOAD_FOLDER)
        target = os.path.abspath(filepath)
        return target.startswith(base) and os.path.isfile(target)
    except (ValueError, OSError):
        return False

def safe_remove_file(filepath):
    """安全にファイルを削除"""
    try:
        if is_safe_path(filepath):
            os.remove(filepath)
            logger.info(f"Deleted file: {filepath}")
            return True
        else:
            logger.warning(f"Unsafe path attempted: {filepath}")
            return False
    except PermissionError:
        logger.error(f"Permission denied deleting: {filepath}")
        return False
    except OSError as e:
        logger.error(f"Error deleting {filepath}: {e}")
        return False

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
    logger.info(f"MIDI file '{filename}' created.")
    return filename


def _generate_mp3_sync(midi_file, mp3_file_prefix):
    """MP3生成処理（実装簡略化版：MIDIファイルをそのまま返す）"""
    logger.info(f'MIDI file ready for playback: {midi_file}')
    return midi_file

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
        logger.error(f"MIDI parsing error: {e}")
        return None

def notetoname(note):
    work = note % 12
    notes_map = {
        0: "C",
        1: "C#",
        2: "D",
        3: "D#",
        4: "E",
        5: "F",
        6: "F#",
        7: "G",
        8: "G#",
        9: "A",
        10: "A#",
        11: "B"
    }
    return notes_map.get(work, "C")

def noteduration(duration):
    dur_map = {
        120: "q",
        240: "h",
        480: "w"
    }
    return dur_map.get(duration, "q")


@app.route('/')
def index():
    response = render_template('index.html')
    # キャッシュを無視するヘッダーを設定
    resp = make_response(response)
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    resp.headers['Last-Modified'] = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    return resp

# バリデーション定数
VALID_SCALES = {'major', 'minor'}
VALID_NOTES = {'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'}

@app.route('/generate_music', methods=['POST'])
def generate_music():
    logger.info("generate_music endpoint called")
    
    # パラメータ取得とバリデーション
    scale = request.form.get('scale', 'major').strip()
    base_note = request.form.get('base_note', '60').strip()
    
    # スケールのバリデーション
    if scale not in VALID_SCALES:
        logger.warning(f"Invalid scale received: {scale}")
        return jsonify({'error': f'Invalid scale. Must be one of: {", ".join(sorted(VALID_SCALES))}'}), 400
    
    # base_note を整数値として処理
    try:
        base_note_value = int(base_note)
        if not (0 <= base_note_value <= 127):
            logger.warning(f"base_note out of range: {base_note_value}")
            return jsonify({'error': 'base_note must be between 0 and 127'}), 400
    except ValueError:
        logger.warning(f"Invalid base note received: {base_note}")
        return jsonify({'error': 'base_note must be a valid integer'}), 400
    midi_file_prefix = "random_midi"
    mp3_file_prefix = "random_mp3"

    try:
        midi_file_path = generate_random_midi(scale, base_note_value, midi_file_prefix)
        if midi_file_path: # midi_file_path が None でないことを確認
            if 'midi_file' in session:
                logger.info("Previous MIDI file found in session, removing")
                safe_remove_file(session['midi_file'])
                session.pop('midi_file', None)
            
            logger.debug(f'midi_file_path={midi_file_path}')
            if 'mp3_file' in session:
                safe_remove_file(session['mp3_file'])
                session.pop('mp3_file', None)
            
            mp3_file_path = None  # 初期化
            logger.info("Calling generate_mp3 function")
            try:
                mp3_file_path = _generate_mp3_sync(midi_file_path, mp3_file_prefix)
                logger.info(f"generate_mp3 returned: {mp3_file_path}")
            except Exception as e:
                logger.error(f"Error during MP3 generation: {e}")
                logger.exception("Full traceback:")
                return jsonify({'error': f"MP3 generation error: {str(e)}"}), 500

            if mp3_file_path:
                logger.info("MP3 file generation succeeded")
                notes = parse_midi(midi_file_path)
                if notes:
                    logger.info("MIDI parsing succeeded")
                    session['midi_file'] = midi_file_path
                    session['mp3_file'] = mp3_file_path
                    logger.debug(f"session['mp3_file']: {session['mp3_file']}")
                    # MP3ファイルの実際のパスを返すように変更
                    return jsonify({'wav_file': 'mp3_file', 'midi_file': '/download/midi', 'notes': notes})
                else:
                    logger.error("MIDI parsing failed")
                    return jsonify({'error': 'Failed to generate score'}), 500
            else:
                logger.error("MP3 file generation failed")
                return jsonify({'error': 'Failed to generate MP3 file'}), 500
        else:
            logger.error("MIDI file generation failed")
            return jsonify({'error': 'Failed to generate MIDI file'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in generate_music: {e}")
        logger.exception("Full traceback:")
        return jsonify({'error': f"Unexpected error: {str(e)}"}), 500

@app.route('/random.mp3')
def get_mp3():
    logger.info("GET /random.mp3 requested")
    try:
        if 'mp3_file' in session:
            mp3_file_path = session['mp3_file']
            logger.debug(f"Attempting to send file: {mp3_file_path}")
            
            if not is_safe_path(mp3_file_path):
                logger.warning(f"Unsafe path access attempted: {mp3_file_path}")
                return jsonify({'error': 'Invalid file path'}), 403
            
            time.sleep(1)
            try:
                return send_file(mp3_file_path, mimetype="audio/mpeg")
            except FileNotFoundError as e:
                logger.warning("FileNotFoundError occurred")
                logger.debug(f"FileNotFoundError details: {str(e)}")
                return jsonify({'error': 'MP3 file not found'}), 404
        else:
            logger.warning("MP3 file not found in session")
            return jsonify({'error': 'MP3 file not found'}), 404
    except Exception as e:
        logger.error(f"Error in get_mp3: {e}")
        logger.debug(f"Error details: {str(e)}")
        return jsonify({'error': 'MP3 file not found'}), 500

@app.route('/download/midi')
def download_midi():
    logger.info("GET /download/midi requested")
    if 'midi_file' in session:
        midi_file_path = session['midi_file']
        
        if not is_safe_path(midi_file_path):
            logger.warning(f"Unsafe path access attempted: {midi_file_path}")
            return jsonify({'error': 'Invalid file path'}), 403
        
        # ファイル名を取得
        filename = os.path.basename(midi_file_path)
        logger.info(f"Sending MIDI file: {filename}")
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            filename,
            as_attachment=True,
            download_name='music.mid',  # ダウンロード時のファイル名
            mimetype='audio/midi'
        )
    else:
        logger.warning("MIDI file not found in session")
        return jsonify({'error': 'MIDI file not found'}), 404

@app.route('/clear_session', methods=['POST'])
def clear_session():
    logger.info("POST /clear_session requested")
    # セッションクリア時にファイルを削除する処理
    if 'midi_file' in session:
        safe_remove_file(session['midi_file'])
        session.pop('midi_file', None)
    if 'mp3_file' in session:
        safe_remove_file(session['mp3_file'])
        session.pop('mp3_file', None)
    logger.info("Session cleared successfully")
    return jsonify({'message': 'Session cleared'}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=port)
