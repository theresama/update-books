import os
import subprocess
import tempfile

import requests
import xmltodict
import yaml


def get_goodreads_data(key):
    params = {'key': key, 'user_id': '8086458-theresa', 'per_page': 200, 'shelf': 'currently-reading', 'v': 2}
    currently_reading_xml = requests.get('https://www.goodreads.com/review/list/8086458.xml', params).text

    params['shelf'] = 'read'
    read_xml = requests.get('https://www.goodreads.com/review/list/8086458.xml', params).text

    return currently_reading_xml, read_xml


def convert_to_yaml(xml):
    book_data = []

    xml_data = xmltodict.parse(xml, xml_attribs=True)

    for book_review in xml_data['GoodreadsResponse']['reviews']['review']:
        book = book_review['book']
        book_data.append({
            'title': book['title'],
            'author': book['authors']['author']['name'],
            'goodreads_url': book['link'],
            'photo_url': book['image_url'],
            'started_reading': book_review['started_at'],
            'finished_reading': book_review['read_at'],
            'rating': book_review['rating'],
        })

    return yaml.safe_dump(book_data, default_flow_style=False, allow_unicode=True, indent=4)


def main():
    goodreads_key = os.environ['GOODREADS_KEY']
    token = os.environ['GH_TOKEN']
    user = 'theresama'
    repo = 'theresama/theresama.github.io'

    currently_reading_xml, read_xml = get_goodreads_data(goodreads_key)

    currently_reading_yaml = convert_to_yaml(currently_reading_xml)
    read_yaml = convert_to_yaml(read_xml)

    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.check_call((
            'git', 'clone', '-q',
            f'https://{user}:{token}@github.com/{repo}', tmpdir,
        ))

        def _writefile(fname, data):
            with open(os.path.join(tmpdir, '_data', fname), 'w') as f:
                f.write(data)

        _writefile('currently_reading.yaml', currently_reading_yaml)
        _writefile('read.yaml', read_yaml)

        if subprocess.call(('git', '-C', tmpdir, 'diff', '--quiet')):
            subprocess.check_call(('git', '-C', tmpdir, 'add', '_data'))

            subprocess.check_call((
                'git', '-C', tmpdir, 'commit', '--quiet',
                '-m', 'Update books!',
            ))

            subprocess.check_call((
                'git', '-C', tmpdir, 'push',
                '--quiet', 'origin', 'HEAD',
            ))


if __name__ == '__main__':
    exit(main())
