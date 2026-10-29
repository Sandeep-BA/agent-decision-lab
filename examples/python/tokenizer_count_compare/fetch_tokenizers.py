"""Download the three tokenizer.json files at the pinned revisions used in the article (network).

Author: Sandeep Belgavi. Files go to ./tokenizer_files; their SHA-256 is printed so a rerun can be compared.
"""
import hashlib, os, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PINNED = (('Qwen/Qwen2.5-0.5B-Instruct', '7ae557604adf67be50417f59c2c2f167def9a775'),
          ('microsoft/Phi-3.5-mini-instruct', '2fe192450127e6a83f7441aef6e3ca586c338b77'),
          ('deepseek-ai/DeepSeek-V3', 'e815299b0bcbac849fa540c768ef21845365c9eb'))


def main():
    os.makedirs(os.path.join(HERE, 'tokenizer_files'), exist_ok=True)
    for repo, rev in PINNED:
        url = 'https://huggingface.co/%s/resolve/%s/tokenizer.json' % (repo, rev)
        path = os.path.join(HERE, 'tokenizer_files', repo.replace('/', '_') + '.json')
        data = urllib.request.urlopen(url, timeout=120).read()
        open(path, 'wb').write(data)
        print(repo, rev[:7], len(data), hashlib.sha256(data).hexdigest()[:16])


if __name__ == '__main__':
    main()
