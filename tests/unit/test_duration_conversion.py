"""
音符長変換関数（noteduration）のユニットテスト
"""
import pytest
from app import noteduration


@pytest.mark.unit
class TestNoteDuration:
    """音符長変換関数テストクラス"""
    
    def test_noteduration_returns_string(self):
        """文字列を返すテスト"""
        result = noteduration(120)
        assert isinstance(result, str)
    
    def test_noteduration_quarter_note(self):
        """4分音符（quarter note）のテスト"""
        assert noteduration(120) == "q"
    
    def test_noteduration_half_note(self):
        """2分音符（half note）のテスト"""
        assert noteduration(240) == "h"
    
    def test_noteduration_whole_note(self):
        """全音符（whole note）のテスト"""
        assert noteduration(480) == "w"
    
    def test_noteduration_valid_durations(self):
        """有効な長さのテスト"""
        valid_durations = {120: "q", 240: "h", 480: "w"}
        for duration, expected in valid_durations.items():
            assert noteduration(duration) == expected
    
    def test_noteduration_unknown_duration(self):
        """未知の長さのテスト"""
        # 定義されていない長さはデフォルト（"q"）を返す
        assert noteduration(100) == "q"
        assert noteduration(200) == "q"
        assert noteduration(999) == "q"
    
    @pytest.mark.parametrize("duration,expected", [
        (120, "q"),
        (240, "h"),
        (480, "w"),
    ])
    def test_noteduration_parametrized(self, duration, expected):
        """パラメータ化テスト"""
        assert noteduration(duration) == expected
    
    def test_noteduration_multiple_calls(self):
        """複数回呼び出しのテスト"""
        # 関数が純粋関数で、複数回呼び出しても同じ結果
        result1 = noteduration(120)
        result2 = noteduration(120)
        assert result1 == result2 == "q"
    
    def test_noteduration_zero(self):
        """0値のテスト"""
        result = noteduration(0)
        assert result == "q"
    
    def test_noteduration_negative(self):
        """負の値のテスト"""
        result = noteduration(-120)
        assert isinstance(result, str)
    
    def test_noteduration_large_value(self):
        """大きい値のテスト"""
        result = noteduration(10000)
        assert result == "q"
    
    def test_noteduration_return_type(self):
        """戻り値の型チェック"""
        for duration in [120, 240, 480, 100, 0]:
            result = noteduration(duration)
            assert isinstance(result, str)
            assert len(result) > 0
