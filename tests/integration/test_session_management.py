"""
セッション管理の統合テスト
"""
import pytest
import os


@pytest.mark.integration
class TestSessionManagement:
    """セッション管理統合テストクラス"""
    
    def test_session_stores_midi_file(self, client, test_app):
        """セッションにMIDIファイルが格納されるテスト"""
        response = client.post('/generate_music', data={
            'scale': 'major',
            'base_note': '60'
        })
        assert response.status_code == 200
        
        with client.session_transaction() as session:
            assert 'midi_file' in session
            midi_file = session['midi_file']
            assert midi_file is not None
            assert midi_file.endswith('.mid')
    
    def test_session_stores_mp3_file(self, client, test_app):
        """セッションにMP3ファイルが格納されるテスト"""
        response = client.post('/generate_music', data={
            'scale': 'major',
            'base_note': '60'
        })
        assert response.status_code == 200
        
        with client.session_transaction() as session:
            assert 'mp3_file' in session
            mp3_file = session['mp3_file']
            assert mp3_file is not None
    
    def test_session_file_exists(self, client, test_app):
        """セッションのファイルが実際に存在するテスト"""
        response = client.post('/generate_music', data={
            'scale': 'major',
            'base_note': '60'
        })
        assert response.status_code == 200
        
        with client.session_transaction() as session:
            midi_file = session.get('midi_file')
            if midi_file:
                assert os.path.exists(midi_file)
    
    def test_session_update_on_new_generation(self, client, test_app):
        """新しい生成でセッションが更新されるテスト"""
        # 1回目の生成
        response1 = client.post('/generate_music', data={
            'scale': 'major',
            'base_note': '60'
        })
        assert response1.status_code == 200
        
        with client.session_transaction() as session:
            midi_file1 = session.get('midi_file')
        
        # 2回目の生成
        response2 = client.post('/generate_music', data={
            'scale': 'minor',
            'base_note': '48'
        })
        assert response2.status_code == 200
        
        with client.session_transaction() as session:
            midi_file2 = session.get('midi_file')
        
        # ファイルが更新されている
        assert midi_file1 != midi_file2
    
    def test_session_clear_removes_files(self, client, test_app):
        """セッションクリアでファイルが削除されるテスト"""
        # 音楽を生成
        response = client.post('/generate_music', data={
            'scale': 'major',
            'base_note': '60'
        })
        assert response.status_code == 200
        
        with client.session_transaction() as session:
            midi_file = session.get('midi_file')
        
        # セッションクリア
        clear_response = client.post('/clear_session')
        assert clear_response.status_code == 200
        
        # セッションからファイルが削除される
        with client.session_transaction() as session:
            assert 'midi_file' not in session
    
    def test_session_isolated_between_clients(self, test_app):
        """異なるクライアント間でセッションが分離されるテスト"""
        with test_app.test_client() as client1:
            with test_app.test_client() as client2:
                # client1で生成
                response1 = client1.post('/generate_music', data={
                    'scale': 'major',
                    'base_note': '60'
                })
                assert response1.status_code == 200
                
                with client1.session_transaction() as session1:
                    midi_file1 = session1.get('midi_file')
                
                # client2では生成していない
                with client2.session_transaction() as session2:
                    midi_file2 = session2.get('midi_file')
                
                # セッションが異なる
                assert midi_file1 != midi_file2
    
    def test_multiple_generations_in_session(self, client, test_app):
        """セッション内での複数回の生成テスト"""
        for i in range(3):
            response = client.post('/generate_music', data={
                'scale': 'major',
                'base_note': str(60 + i * 12)
            })
            assert response.status_code == 200
        
        # 最後の生成後のセッションを確認
        with client.session_transaction() as session:
            assert 'midi_file' in session
    
    def test_session_file_path_format(self, client, test_app):
        """セッションのファイルパスフォーマットのテスト"""
        response = client.post('/generate_music', data={
            'scale': 'major',
            'base_note': '60'
        })
        assert response.status_code == 200
        
        with client.session_transaction() as session:
            midi_file = session.get('midi_file')
            # パスが static フォルダを含む
            assert 'static' in midi_file or midi_file.startswith('/')
    
    @pytest.mark.parametrize("scale,base_note", [
        ("major", "60"),
        ("minor", "48"),
        ("major", "72"),
    ])
    def test_session_with_various_parameters(self, client, test_app, scale, base_note):
        """様々なパラメータでのセッション管理テスト"""
        response = client.post('/generate_music', data={
            'scale': scale,
            'base_note': base_note
        })
        assert response.status_code == 200
        
        with client.session_transaction() as session:
            assert 'midi_file' in session
            assert session['midi_file'] is not None
