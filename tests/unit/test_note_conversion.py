"""
音符変換関数（notetoname）のユニットテスト
"""
import pytest
from app import notetoname


@pytest.mark.unit
class TestNoteToName:
    """音符変換関数テストクラス"""
    
    def test_notetoname_returns_string(self):
        """文字列を返すテスト"""
        result = notetoname(0)
        assert isinstance(result, str)
    
    def test_notetoname_c_note(self):
        """C音のテスト"""
        assert notetoname(0) == "C"
        assert notetoname(12) == "C"
        assert notetoname(24) == "C"
        assert notetoname(36) == "C"
    
    def test_notetoname_d_note(self):
        """D音のテスト"""
        assert notetoname(2) == "D"
        assert notetoname(14) == "D"
        assert notetoname(26) == "D"
    
    def test_notetoname_e_note(self):
        """E音のテスト"""
        assert notetoname(4) == "E"
        assert notetoname(16) == "E"
        assert notetoname(28) == "E"
    
    def test_notetoname_f_note(self):
        """F音のテスト"""
        assert notetoname(5) == "F"
        assert notetoname(17) == "F"
        assert notetoname(29) == "F"
    
    def test_notetoname_g_note(self):
        """G音のテスト"""
        assert notetoname(7) == "G"
        assert notetoname(19) == "G"
        assert notetoname(31) == "G"
    
    def test_notetoname_a_note(self):
        """A音のテスト"""
        assert notetoname(9) == "A"
        assert notetoname(21) == "A"
        assert notetoname(33) == "A"
    
    def test_notetoname_b_note(self):
        """B音のテスト"""
        assert notetoname(11) == "B"
        assert notetoname(23) == "B"
        assert notetoname(35) == "B"
    
    def test_notetoname_sharp_notes(self):
        """シャープ音のテスト"""
        assert notetoname(1) == "C#"
        assert notetoname(3) == "D#"
        assert notetoname(6) == "F#"
        assert notetoname(8) == "G#"
        assert notetoname(10) == "A#"
    
    def test_notetoname_octave_wrapping(self):
        """オクターブラップアラウンドのテスト"""
        # 同じ相対音は同じ名前を返す
        assert notetoname(0) == notetoname(12) == notetoname(24) == notetoname(36)
        assert notetoname(1) == notetoname(13) == notetoname(25)
        assert notetoname(11) == notetoname(23) == notetoname(35)
    
    @pytest.mark.parametrize("note,expected", [
        (0, "C"),
        (1, "C#"),
        (2, "D"),
        (3, "D#"),
        (4, "E"),
        (5, "F"),
        (6, "F#"),
        (7, "G"),
        (8, "G#"),
        (9, "A"),
        (10, "A#"),
        (11, "B"),
    ])
    def test_notetoname_all_chromatic_notes(self, note, expected):
        """全クロマティック音のパラメータ化テスト"""
        assert notetoname(note) == expected
    
    def test_notetoname_midi_range(self):
        """MIDI範囲内のテスト"""
        # MIDI範囲は0-127
        for note in [0, 60, 127]:
            result = notetoname(note)
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_notetoname_out_of_range_positive(self):
        """MIDI範囲外（正）のテスト"""
        # 128以上でもモジュロで処理される
        assert notetoname(128) == "G#"  # 128 % 12 = 8 -> G#
        assert notetoname(129) == "A"   # 129 % 12 = 9 -> A
        assert notetoname(140) == "G#"  # 140 % 12 = 8 -> G#
    
    def test_notetoname_out_of_range_negative(self):
        """MIDI範囲外（負）のテスト"""
        # 負数もモジュロで処理される
        assert notetoname(-1) == "B"
        assert notetoname(-12) == "C"
    
    def test_notetoname_middle_c(self):
        """中央C（C4）のテスト"""
        # MIDI note 60 = C4
        assert notetoname(60) == "C"
    
    def test_notetoname_concert_a(self):
        """コンサートA（A4）のテスト"""
        # MIDI note 69 = A4
        assert notetoname(69) == "A"
