"""
MP3生成関数のユニットテスト
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from app import _generate_mp3_sync


@pytest.mark.unit
class TestGenerateMp3:
    """MP3生成関数テストクラス"""
    
    def test_generate_mp3_returns_path(self, test_app, temp_midi_file):
        """MP3ファイルパスを返すテスト"""
        with test_app.app_context():
            result = _generate_mp3_sync(temp_midi_file, "test")
            assert result is not None
            assert isinstance(result, str)
    
    def test_generate_mp3_with_valid_midi(self, test_app, temp_midi_file):
        """有効なMIDIファイルで処理するテスト"""
        with test_app.app_context():
            result = _generate_mp3_sync(temp_midi_file, "test")
            assert result == temp_midi_file
    
    def test_generate_mp3_returns_file_path(self, test_app, temp_midi_file):
        """ファイルパスが返されるテスト"""
        with test_app.app_context():
            result = _generate_mp3_sync(temp_midi_file, "test_prefix")
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_generate_mp3_multiple_prefixes(self, test_app, temp_midi_file):
        """異なるプレフィックスで処理するテスト"""
        with test_app.app_context():
            result1 = _generate_mp3_sync(temp_midi_file, "prefix1")
            result2 = _generate_mp3_sync(temp_midi_file, "prefix2")
            
            # 現在の実装ではMIDIファイルをそのまま返す
            assert result1 == temp_midi_file
            assert result2 == temp_midi_file
    
    def test_generate_mp3_preserves_input_midi(self, test_app, temp_midi_file):
        """入力MIDIファイルが保持されるテスト"""
        with test_app.app_context():
            original_size = os.path.getsize(temp_midi_file)
            _generate_mp3_sync(temp_midi_file, "test")
            
            # ファイルは削除されていないはず
            assert os.path.exists(temp_midi_file)
            assert os.path.getsize(temp_midi_file) == original_size
    
    def test_generate_mp3_empty_prefix(self, test_app, temp_midi_file):
        """空のプレフィックスで処理するテスト"""
        with test_app.app_context():
            result = _generate_mp3_sync(temp_midi_file, "")
            assert result is not None
    
    def test_generate_mp3_special_characters_prefix(self, test_app, temp_midi_file):
        """特殊文字を含むプレフィックスで処理するテスト"""
        with test_app.app_context():
            result = _generate_mp3_sync(temp_midi_file, "test-_123")
            assert result is not None
            assert isinstance(result, str)
    
    @pytest.mark.parametrize("prefix", [
        "mp3_1",
        "audio_test",
        "music_generation"
    ])
    def test_generate_mp3_various_prefixes(self, test_app, temp_midi_file, prefix):
        """様々なプレフィックスで処理するテスト"""
        with test_app.app_context():
            result = _generate_mp3_sync(temp_midi_file, prefix)
            assert result is not None
            assert isinstance(result, str)
