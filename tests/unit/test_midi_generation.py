"""
MIDI生成関数のユニットテスト
"""
import pytest
import os
from mido import MidiFile
from app import generate_random_midi, app


@pytest.mark.unit
class TestGenerateRandomMidi:
    """MIDI生成関数テストクラス"""
    
    def test_returns_valid_path(self, test_app):
        """有効なファイルパスを返すテスト"""
        with test_app.app_context():
            midi_file = generate_random_midi("major", 60, "test")
            assert midi_file is not None
            assert isinstance(midi_file, str)
            assert midi_file.endswith('.mid')
    
    def test_file_exists(self, test_app):
        """生成されたファイルが存在するテスト"""
        with test_app.app_context():
            midi_file = generate_random_midi("major", 60, "test")
            assert os.path.exists(midi_file)
            assert os.path.isfile(midi_file)
            # クリーンアップ
            os.remove(midi_file)
    
    def test_file_has_valid_size(self, test_app):
        """生成されたファイルサイズが妥当なテスト"""
        with test_app.app_context():
            midi_file = generate_random_midi("major", 60, "test")
            file_size = os.path.getsize(midi_file)
            assert file_size > 0
            assert file_size < 1024 * 1024  # 1MB未満
            os.remove(midi_file)
    
    def test_can_be_parsed_by_mido(self, test_app):
        """mido で読込可能なMIDIファイルテスト"""
        with test_app.app_context():
            midi_file = generate_random_midi("major", 60, "test")
            midi = MidiFile(midi_file)
            assert len(midi.tracks) > 0
            assert any(msg.type in ['note_on', 'note_off'] for track in midi.tracks for msg in track)
            os.remove(midi_file)
    
    def test_contains_note_messages(self, test_app):
        """ノートメッセージが含まれるテスト"""
        with test_app.app_context():
            midi_file = generate_random_midi("major", 60, "test")
            midi = MidiFile(midi_file)
            
            has_note_on = False
            has_note_off = False
            
            for track in midi.tracks:
                for msg in track:
                    if msg.type == 'note_on':
                        has_note_on = True
                    if msg.type == 'note_off':
                        has_note_off = True
            
            assert has_note_on or has_note_off
            os.remove(midi_file)
    
    @pytest.mark.parametrize("scale,base_note", [
        ("major", 60),
        ("minor", 48),
        ("major", 72),
        ("minor", 84),
        ("major", 36),
    ])
    def test_all_scales_and_notes(self, test_app, scale, base_note):
        """全スケール・基準音のテスト"""
        with test_app.app_context():
            midi_file = generate_random_midi(scale, base_note, "test")
            assert os.path.exists(midi_file)
            
            midi = MidiFile(midi_file)
            assert len(midi.tracks) > 0
            
            os.remove(midi_file)
    
    def test_base_note_in_range(self, test_app):
        """生成されるノートが範囲内のテスト"""
        with test_app.app_context():
            midi_file = generate_random_midi("major", 60, "test")
            midi = MidiFile(midi_file)
            
            for track in midi.tracks:
                for msg in track:
                    if msg.type == 'note_on' and msg.note > 0:
                        assert 0 <= msg.note <= 127, f"Note {msg.note} is out of MIDI range"
            
            os.remove(midi_file)
    
    def test_note_on_velocity_in_range(self, test_app):
        """note_on ベロシティが範囲内のテスト"""
        with test_app.app_context():
            midi_file = generate_random_midi("major", 60, "test")
            midi = MidiFile(midi_file)
            
            for track in midi.tracks:
                for msg in track:
                    if msg.type == 'note_on':
                        assert 40 <= msg.velocity <= 100
            
            os.remove(midi_file)
    
    def test_program_change_message_exists(self, test_app):
        """プログラムチェンジメッセージが存在するテスト"""
        with test_app.app_context():
            midi_file = generate_random_midi("major", 60, "test")
            midi = MidiFile(midi_file)
            
            has_program_change = False
            for track in midi.tracks:
                for msg in track:
                    if msg.type == 'program_change':
                        has_program_change = True
                        assert msg.program == 0  # ピアノ
            
            assert has_program_change
            os.remove(midi_file)
    
    def test_unique_filenames(self, test_app):
        """生成されるファイル名が一意であるテスト"""
        with test_app.app_context():
            midi_file1 = generate_random_midi("major", 60, "test")
            midi_file2 = generate_random_midi("major", 60, "test")
            
            assert midi_file1 != midi_file2
            
            os.remove(midi_file1)
            os.remove(midi_file2)
