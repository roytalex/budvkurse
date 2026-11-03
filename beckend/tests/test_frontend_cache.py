from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from core.frontend_delivery import FrontendFiles, asset_version
from core.config import get_settings
from services import max_bot


async def test_html_not_stored_and_assets_revalidated(tmp_path):
    (tmp_path / 'index.html').write_text('<html>Current app</html>')
    (tmp_path / 'app.css').write_text('body{color:blue}')
    app = FastAPI()
    app.mount('/', FrontendFiles(directory=tmp_path, html=True))
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        for path in ('/', '/?v=fresh', '/index.html'):
            result = await client.get(path)
            assert result.status_code == 200
            assert 'no-store' in result.headers['cache-control']
        css = await client.get('/app.css')
        assert 'must-revalidate' in css.headers['cache-control']
        cached = await client.get('/app.css', headers={'If-None-Match': css.headers['etag']})
        assert cached.status_code == 304
        assert 'no-cache' in cached.headers['cache-control']
        (tmp_path / 'app.css').write_text('body{color:darkblue;background:white}')
        changed = await client.get('/app.css', headers={'If-None-Match': css.headers['etag']})
        assert changed.status_code == 200
        assert 'darkblue' in changed.text


def test_version_changes_with_styles_but_not_file_order(tmp_path):
    (tmp_path / 'index.html').write_text('<html>app</html>')
    (tmp_path / 'style.css').write_text('body{}')
    initial = asset_version(tmp_path)
    assert asset_version(tmp_path) == initial
    (tmp_path / 'style.css').write_text('body{color:blue}')
    assert asset_version(tmp_path) != initial


def test_bot_only_opens_miniapp_even_with_public_url():
    with patch.object(get_settings(), 'public_base_url', 'https://example.org'):
        buttons = max_bot.welcome('school_bot')['attachments'][0]['payload']['buttons']
        assert len(buttons) == 1
        assert buttons[0][0]['type'] == 'open_app'
