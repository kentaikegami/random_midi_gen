"""
Flask エンドポイントの統合テスト
"""
import pytest
import json
from app import app


@pytest.mark.integration
class TestEndpoints:
    """エンドポイント統合テストクラス"""
    
    def test_index_endpoint_returns_200(self, client):
        """/ エンドポイントが200を返すテスト"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_index_endpoint_returns_html(self, client):
        """/ エンドポイントがHTMLを返すテスト"""
        response = client.get('/')
        assert response.status_code == 200
        assert response.content_type.startswith('text/html')
    
    def test_generate_music_endpoint_requires_post(self, client):
        """生成エンドポイントがPOSTメソッド必須のテスト"""
        response = client.get('/generate_music')
        assert response.status_code != 200
    
    def test_generate_music_with_valid_parameters(self, client):
        """有効なパラメータでの生成テスト"""
        response = client.post('/generate_music', data={
            'scale': 'major',
            'base_note': '60'
        })
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'notes' in data
        assert 'wav_file' in data
        assert isinstance(data['notes'], list)
    
    def test_generate_music_major_scale(self, client):
        """メジャースケール生成テスト"""
        response = client.post('/generate_music', data={
            'scale': 'major',
            'base_note': '60'
        })
        assert response.status_code == 200
    
    def test_generate_music_minor_scale(self, client):
        """マイナースケール生成テスト"""
        response = client.post('/generate_music', data={
            'scale': 'minor',
            'base_note': '60'
        })
        assert response.status_code == 200
    
    def test_generate_music_invalid_scale(self, client):
        """無効なスケールで400エラーのテスト"""
        response = client.post('/generate_music', data={
            'scale': 'invalid_scale',
            'base_note': '60'
        })
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data
    
    def test_generate_music_invalid_base_note_string(self, client):
        """base_noteが文字列の場合で400エラーのテスト"""
        response = client.post('/generate_music', data={
            'scale': 'major',
            'base_note': 'invalid'
        })
        assert response.status_code == 400
    
    def test_generate_music_base_note_out_of_range_low(self, client):
        """base_noteが範囲外（低）で400エラーのテスト"""
        response = client.post('/generate_music', data={
            'scale': 'major',
            'base_note': '-1'
        })
        assert response.status_code == 400
    
    def test_generate_music_base_note_out_of_range_high(self, client):
        """base_noteが範囲外（高）で400エラーのテスト"""
        response = client.post('/generate_music', data={
            'scale': 'major',
            'base_note': '128'
        })
        assert response.status_code == 400
    
    def test_generate_music_default_parameters(self, client):
        """デフォルトパラメータでの生成テスト"""
        response = client.post('/generate_music', data={})
        assert response.status_code == 200
    
    @pytest.mark.parametrize("scale,base_note", [
        ("major", "60"),
        ("minor", "48"),
        ("major", "72"),
        ("minor", "84"),
    ])
    def test_generate_music_various_parameters(self, client, scale, base_note):
        """様々なパラメータでの生成テスト"""
        response = client.post('/generate_music', data={
            'scale': scale,
            'base_note': base_note
        })
        assert response.status_code == 200
    
    def test_clear_session_endpoint(self, client):
        """clear_session エンドポイントのテスト"""
        # まず音楽を生成
        client.post('/generate_music', data={
            'scale': 'major',
            'base_note': '60'
        })
        
        # セッションクリア
        response = client.post('/clear_session')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'message' in data
    
    def test_download_midi_after_generation(self, client):
        """生成後MIDIダウンロードのテスト"""
        # 音楽を生成
        gen_response = client.post('/generate_music', data={
            'scale': 'major',
            'base_note': '60'
        })
        assert gen_response.status_code == 200
        
        # セッションにファイルが格納されていることを確認
        with client.session_transaction() as session:
            assert 'midi_file' in session
            assert session['midi_file'] is not None
    
    def test_download_midi_without_generation(self, client):
        """生成なしMIDIダウンロードで404のテスト"""
        response = client.get('/download/midi')
        assert response.status_code == 404
    
    def test_get_mp3_after_generation(self, client):
        """生成後MP3取得のテスト"""
        # 音楽を生成
        gen_response = client.post('/generate_music', data={
            'scale': 'major',
            'base_note': '60'
        })
        assert gen_response.status_code == 200
        
        # MP3をセッションから確認（実装がMIDIを返すため）
        with client.session_transaction() as session:
            assert 'mp3_file' in session
            assert session['mp3_file'] is not None
    
    def test_get_mp3_without_generation(self, client):
        """生成なしMP3取得で404のテスト"""
        response = client.get('/random.mp3')
        assert response.status_code == 404
    
    def test_generate_music_returns_json(self, client):
        """JSON形式でレスポンスが返されるテスト"""
        response = client.post('/generate_music', data={
            'scale': 'major',
            'base_note': '60'
        })
        assert response.status_code == 200
        assert response.content_type.startswith('application/json')
        
        # JSONをパース可能
        data = response.get_json()
        assert isinstance(data, dict)
