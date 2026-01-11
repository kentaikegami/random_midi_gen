"""
テスト共有フィクスチャとユーティリティ
"""
import pytest
import os
import sys
import tempfile
import shutil

# テスト実行時に親ディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from flask import Flask
from app import app, generate_random_midi


@pytest.fixture
def test_app():
    """Flask テストアプリケーション"""
    app.config['TESTING'] = True
    app.config['SESSION_TYPE'] = 'filesystem'
    
    # 一時ディレクトリを使用
    temp_dir = tempfile.mkdtemp()
    app.config['UPLOAD_FOLDER'] = temp_dir
    
    yield app
    
    # クリーンアップ
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def client(test_app):
    """Flask テストクライアント"""
    with test_app.app_context():
        with test_app.test_client() as test_client:
            yield test_client


@pytest.fixture
def runner(test_app):
    """Flask CLI テストランナー"""
    return test_app.test_cli_runner()


@pytest.fixture
def temp_dir():
    """一時ディレクトリフィクスチャ"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def temp_midi_file(test_app):
    """一時MIDI ファイルフィクスチャ"""
    with test_app.app_context():
        midi_file = generate_random_midi("major", 60, "test")
        yield midi_file
        # クリーンアップ
        if os.path.exists(midi_file):
            os.remove(midi_file)


@pytest.fixture
def session_with_generated_music(client, test_app):
    """MIDI生成済みセッション"""
    with test_app.test_request_context():
        response = client.post('/generate_music', data={
            'scale': 'major',
            'base_note': '60'
        })
        assert response.status_code == 200
    
    yield client
    
    # クリーンアップ
    response = client.post('/clear_session')


@pytest.fixture
def mock_mido_file(mocker):
    """mido.MidiFile のモック"""
    mock = mocker.MagicMock()
    mock.tracks = [mocker.MagicMock()]
    return mock
