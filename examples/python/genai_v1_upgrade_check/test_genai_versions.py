"""Pin what google-genai 3.0.0 sends, offline: API version per platform, HTTP client and request paths.

Author: Sandeep Belgavi. Companion to "google-genai 3.0.0 for Python: v1 by Default, httpx2 and What Breaks on
Upgrade" (aicassindra.com). Needs `pip install -r requirements.txt`. A placeholder key and an httpx2 mock transport
are used, so nothing is sent to Google. Real server responses are not tested here.
"""
import os
import unittest

for name in ('GOOGLE_GENAI_API_VERSION', 'GOOGLE_GENAI_HTTP_CLIENT', 'GOOGLE_API_KEY', 'GEMINI_API_KEY'):
    os.environ.pop(name, None)

import httpx2
from google import genai
import google.genai.errors  # noqa: F401  (genai.errors.ClientError)
from google.genai import types

OK = {'candidates': [{'content': {'role': 'model', 'parts': [{'text': 'ok'}]}, 'finishReason': 'STOP'}]}


def recording_client(seen, **http):
    def handler(request):
        seen.append(request.url.path)
        if 'cachedContents' in request.url.path:
            return httpx2.Response(404, json={'error': {'code': 404, 'message': 'mock', 'status': 'NOT_FOUND'}})
        return httpx2.Response(200, json=OK)
    opts = types.HttpOptions(client_args={'transport': httpx2.MockTransport(handler)}, **http)
    return genai.Client(api_key='placeholder', http_options=opts)


class Defaults(unittest.TestCase):
    def tearDown(self):
        os.environ.pop('GOOGLE_GENAI_API_VERSION', None)

    def test_installed_version(self):
        self.assertEqual(genai.__version__, '3.0.0')

    def test_developer_api_defaults_to_v1(self):
        seen = []
        client = recording_client(seen)  # keep a reference: a collected Client closes its HTTP client
        client.models.generate_content(model='gemini-2.5-flash', contents='CASE-1042')
        self.assertEqual(seen, ['/v1/models/gemini-2.5-flash:generateContent'])

    def test_environment_variable_beta_restores_v1beta(self):
        os.environ['GOOGLE_GENAI_API_VERSION'] = 'beta'
        seen = []
        client = recording_client(seen)  # keep a reference: a collected Client closes its HTTP client
        client.models.generate_content(model='gemini-2.5-flash', contents='CASE-1042')
        self.assertEqual(seen, ['/v1beta/models/gemini-2.5-flash:generateContent'])

    def test_code_overrides_environment(self):
        os.environ['GOOGLE_GENAI_API_VERSION'] = 'beta'
        seen = []
        client = recording_client(seen, api_version='v1alpha')
        client.models.generate_content(model='gemini-2.5-flash', contents='x')
        self.assertTrue(seen[0].startswith('/v1alpha/'))

    def test_cache_create_is_not_guarded_on_v1(self):
        seen = []
        client = recording_client(seen)
        with self.assertRaises(genai.errors.ClientError):
            client.caches.create(model='gemini-2.5-flash',
                                 config=types.CreateCachedContentConfig(contents=['catalogue'], ttl='300s'))
        self.assertEqual(seen, ['/v1/cachedContents'])

    def test_explicit_v1beta_client_for_caching(self):
        seen = []
        client = recording_client(seen, api_version='v1beta')
        with self.assertRaises(genai.errors.ClientError):
            client.caches.create(model='gemini-2.5-flash',
                                 config=types.CreateCachedContentConfig(contents=['catalogue'], ttl='300s'))
        self.assertEqual(seen, ['/v1beta/cachedContents'])

    def test_vertex_client_keeps_v1beta1(self):
        client = genai.Client(vertexai=True, project='demo-project', location='us-central1')
        self.assertEqual(client._api_client._http_options.api_version, 'v1beta1')

    def test_default_http_client_is_httpx2(self):
        client = genai.Client(api_key='placeholder')
        self.assertIn('Httpx2', type(client._api_client._httpx_client).__name__)


if __name__ == '__main__':
    unittest.main()
