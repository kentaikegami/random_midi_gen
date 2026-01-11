"""
E2E（エンドツーエンド）テスト
"""
import pytest
import os
from mido import MidiFile


@pytest.mark.e2e
class TestWorkflow:
    """エンドツーエンドワークフロー テストクラス"""
    
    def test_complete_workflow(self, client, test_app):
        """完全なワークフローのテスト"""
        # 1. ホームページにアクセス
        response = client.get('/')
        assert response.status_code == 200
        
        # 2. 音楽生成リクエスト
        response = client.post('/generate_music', data={
            'scale': 'major',
            'base_note': '60'
        })
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'notes' in data
        assert 'midi_file' in data
        notes = data['notes']
        assert len(notes) > 0
        
        # 3. ファイルが有効なMIDIファイルであることを確認
        with client.session_transaction() as session:
            midi_file = session.get('midi_file')
            if midi_file and os.path.exists(midi_file):
                midi = MidiFile(midi_file)
                assert len(midi.tracks) > 0
        
        # 4. セッションクリア
        response = client.post('/clear_session')
        assert response.status_code == 200
        assert response.status_code == 200
    
    def test_workflow_major_scale(self, client, test_app):
        """メジャースケールを使用したワークフロー"""
        # 生成
        response = client.post('/generate_music', data={
            'scale': 'major',
            'base_note': '60'
        })
        assert response.status_code == 200
        
        # セッションファイル確認
        with client.session_transaction() as session:
            assert 'midi_file' in session
        
        # クリア
        response = client.post('/clear_session')
        assert response.status_code == 200
    
    def test_workflow_minor_scale(self, client, test_app):
        """マイナースケールを使用したワークフロー"""
        # 生成
        response = client.post('/generate_music', data={
            'scale': 'minor',
            'base_note': '48'
        })
        assert response.status_code == 200
        
        # セッションファイル確認
        with client.session_transaction() as session:
            assert 'midi_file' in session
        
        # クリア
        response = client.post('/clear_session')
        assert response.status_code == 200
    
    def test_workflow_multiple_generations(self, client, test_app):
        """複数回の生成を含むワークフロー"""
        for i in range(3):
            # 生成
            response = client.post('/generate_music', data={
                'scale': 'major' if i % 2 == 0 else 'minor',
                'base_note': str(60 + i * 12)
            })
            assert response.status_code == 200
        
        # 最後の生成後のセッション確認
        with client.session_transaction() as session:
            assert 'midi_file' in session
        
        # クリア
        response = client.post('/clear_session')
        assert response.status_code == 200
    
    def test_workflow_with_all_base_notes(self, client, test_app):
        """全ての基準音を使用したワークフロー"""
        base_notes = ['60', '62', '64', '65', '67', '69', '71']
        
        for base_note in base_notes:
            response = client.post('/generate_music', data={
                'scale': 'major',
                'base_note': base_note
            })
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'notes' in data
            assert len(data['notes']) > 0
    
    def test_workflow_response_structure(self, client, test_app):
        """レスポンス構造のテスト"""
        response = client.post('/generate_music', data={
            'scale': 'major',
            'base_note': '60'
        })
        assert response.status_code == 200
        
        data = response.get_json()
        
        # 必須フィールド確認
        assert isinstance(data, dict)
        assert 'notes' in data
        assert 'wav_file' in data
        assert 'midi_file' in data
        
        # データ型確認
        assert isinstance(data['notes'], list)
        assert isinstance(data['wav_file'], str)
        assert isinstance(data['midi_file'], str)
    
    def test_workflow_download_before_generation(self, client):
        """生成前のダウンロード試行テスト"""
        response = client.get('/download/midi')
        assert response.status_code == 404
    
    def test_workflow_clear_twice(self, client, test_app):
        """セッションクリアの重複実行テスト"""
        # 生成
        client.post('/generate_music', data={
            'scale': 'major',
            'base_note': '60'
        })
        
        # クリア1回目
        response = client.post('/clear_session')
        assert response.status_code == 200
        
        # クリア2回目（エラーが発生しないか）
        response = client.post('/clear_session')
        assert response.status_code == 200
    
    @pytest.mark.parametrize("scale,base_note", [
        ("major", "36"),
        ("minor", "48"),
        ("major", "60"),
        ("minor", "72"),
        ("major", "84"),
    ])
    def test_workflow_parametrized(self, client, test_app, scale, base_note):
        """パラメータ化されたワークフロー"""
        # 生成
        response = client.post('/generate_music', data={
            'scale': scale,
            'base_note': base_note
        })
        assert response.status_code == 200
        
        # セッションファイル確認
        with client.session_transaction() as session:
            assert 'midi_file' in session
        
        # クリア
        response = client.post('/clear_session')
        assert response.status_code == 200
