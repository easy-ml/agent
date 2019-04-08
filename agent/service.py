from mimetypes import MimeTypes

import requests


class CoreService(object):
    def __init__(self, url, access_token):
        self._url = url[:-1] if url.endswith('/') else url
        self._access_toke = access_token
        self._headers = {'Authorization': f'Bearer {access_token}'}
        self._mime = MimeTypes()

    def get(self, url):
        return requests.get(url, headers=self._headers)

    def storage_get(self, _id: str):
        return self.get(f'{self._url}storage/{_id}')

    def storage_upload(self, path):
        upload_url = f'{self._url}/storage'
        with open(path, 'rb') as file:
            files = {'file': (
                'second-menu.bg.png',
                file,
                self._mime.guess_type('second-menu.bg.png')[0],
            )}
        return requests.post(upload_url, files=files, headers=self._headers)
