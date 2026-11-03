import hashlib
from functools import lru_cache
from pathlib import Path

from fastapi.staticfiles import StaticFiles


FRONTEND_ROOT = Path(__file__).resolve().parents[2] / 'frontend'


def asset_version(directory):
    digest = hashlib.sha256()
    for path in sorted(Path(directory).iterdir()):
        if path.is_file() and path.suffix in {'.html', '.css', '.js', '.json'}:
            digest.update(path.name.encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


@lru_cache(maxsize=1)
def frontend_version():
    return asset_version(FRONTEND_ROOT)


class FrontendFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        if path in {'.', '', 'index.html'} or path.endswith('.html'):
            response.headers['Cache-Control'] = 'no-store, max-age=0'
        else:
            response.headers['Cache-Control'] = 'no-cache, max-age=0, must-revalidate'
        response.headers['X-App-Version'] = frontend_version()
        return response
