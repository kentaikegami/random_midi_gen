"""
MIDI解析関数のユニットテスト
"""
import pytest
import os
from mido import MidiFile, MidiTrack, Message
from app import parse_midi, generate_random_midi


@pytest.mark.unit
class TestParseMidi:
    """MIDI解析関数テストクラス"""
    
    def test_parse_midi_returns_list(self, test_app, temp_midi_file):
        """リストを返すテスト"""
        with test_app.app_context():
            result = parse_midi(temp_midi_file)
            assert isinstance(result, list)
    
    def test_parse_midi_returns_notes(self, test_app, temp_midi_file):
        """ノート情報を返すテスト"""
        with test_app.app_context():
            result = parse_midi(temp_midi_file)
            assert len(result) >= 0
            
            # ノート形式の確認
            for note in result:
                assert isinstance(note, str)
    
    def test_parse_midi_note_format(self, test_app, temp_midi_file):
        """ノートフォーマットが正しいテスト"""
        with test_app.app_context():
            result = parse_midi(temp_midi_file)
            
            for note in result:
                # フォーマット: "C/4,q" など
                assert '/' in note or note == ""
    
    def test_parse_midi_nonexistent_file(self, test_app):
        """存在しないファイルの処理テスト"""
        with test_app.app_context():
            result = parse_midi("nonexistent_file.mid")
            assert result is None
    
    def test_parse_midi_invalid_file(self, test_app, temp_dir):
        """無効なMIDIファイルの処理テスト"""
        with test_app.app_context():
            invalid_file = os.path.join(temp_dir, "invalid.mid")
            with open(invalid_file, 'w') as f:
                f.write("This is not a valid MIDI file")
            
            result = parse_midi(invalid_file)
            assert result is None
    
    def test_parse_midi_empty_tracks(self, test_app, temp_dir):
        """空のトラックを持つMIDIファイルの処理テスト"""
        with test_app.app_context():
            empty_midi_file = os.path.join(temp_dir, "empty.mid")
            mid = MidiFile()
            mid.tracks.append(MidiTrack())
            mid.save(empty_midi_file)
            
            result = parse_midi(empty_midi_file)
            assert isinstance(result, list)
    
    def test_parse_midi_multiple_tracks(self, test_app, temp_dir):
        """複数トラックを持つMIDIファイルの処理テスト"""
        with test_app.app_context():
            multi_track_file = os.path.join(temp_dir, "multi.mid")
            mid = MidiFile()
            
            # トラック1
            track1 = MidiTrack()
            track1.append(Message('note_on', note=60, velocity=100, time=0))
            track1.append(Message('note_off', note=60, velocity=0, time=480))
            mid.tracks.append(track1)
            
            # トラック2
            track2 = MidiTrack()
            track2.append(Message('note_on', note=64, velocity=100, time=0))
            track2.append(Message('note_off', note=64, velocity=0, time=480))
            mid.tracks.append(track2)
            
            mid.save(multi_track_file)
            
            result = parse_midi(multi_track_file)
            assert isinstance(result, list)
            assert len(result) > 0
    
    def test_parse_midi_with_note_off(self, test_app, temp_dir):
        """note_off メッセージを含むテスト"""
        with test_app.app_context():
            test_file = os.path.join(temp_dir, "notes.mid")
            mid = MidiFile()
            track = MidiTrack()
            
            track.append(Message('note_on', note=60, velocity=100, time=0))
            track.append(Message('note_off', note=60, velocity=0, time=240))
            mid.tracks.append(track)
            mid.save(test_file)
            
            result = parse_midi(test_file)
            assert len(result) > 0
    
    def test_parse_midi_large_file(self, test_app):
        """大量のノートを含むMIDIファイルの処理テスト"""
        with test_app.app_context():
            # 多数のノートを生成
            midi_file = generate_random_midi("major", 60, "test_large")
            result = parse_midi(midi_file)
            
            assert isinstance(result, list)
            assert len(result) > 0
            
            os.remove(midi_file)
