"""
    Download QuickPic photos from the CM Cloud
    before it's too late.
"""
import imghdr
import os
import sys
import time

from functools import partial
from itertools import count
from getpass import getpass

import dateparser
import requests


BASE_URL = 'https://cloud.cmcm.com/{}'
LOGIN_URL = BASE_URL.format('cmbpc/login/login')
API_URL = BASE_URL.format('cmbpc/disk/file')


def login(session, email, password):
    """Perform a login."""
    print('Authenticating...')
    resp = session.post(LOGIN_URL, data={'email': email, 'password': password})
    return resp.json().get('ret', 0) == 0


def fetch_metadata_page(login_fn, post_fn, page_size, offset):
    """Fetch a metadata page."""
    for attempt in range(1, 10):
        resp = post_fn(API_URL, data=dict(id='cm_photo', pagesize=page_size, offset=offset))
        assert resp.status_code == 200
        json = resp.json()
        if json.get('ret', 0) == 0:
            return json['data']
        print('Metadata fetch attempt #{} failed, will retry...'.format(attempt))
        login_fn()
    raise RuntimeError('Failed to fetch metadata page with offset={}.'.format(offset))


def get_metadata_catalogue(login_fn, post_fn):
    """Fetch the entire metadata catalogue."""
    page_size = 100
    for offset in count(start=0, step=page_size):
        data = fetch_metadata_page(login_fn, post_fn, page_size, offset)
        if offset < data.get('itemTotal', 0):
            yield from iter(data['list'])
        else:
            print('No more files.')
            return


def file_exists(fname):
    """Return True if the file already exists."""
    return os.path.isfile(fname) and os.path.getsize(fname) > 0


def download_image(login_fn, get_fn, url, fname):
    """Download individual image."""
    print('Downloading {}...'.format(fname))
    for attempt in range(1, 10):
        resp = get_fn(BASE_URL.format(url))
        assert resp.status_code == 200
        if imghdr.what(None, h=resp.content) == 'jpeg':
            with open(fname, 'wb') as file:
                file.write(resp.content)
            return
        print('Image download attempt #{} failed, will retry...'.format(attempt))
        login_fn()
    raise RuntimeError('Image download failed for {}'.format(fname))


def all_file_metadata(login_fn, post_fn):
    """Consequently fetch metadata pages, format metadata for the individual files."""
    for meta in get_metadata_catalogue(login_fn, post_fn):
        for file in meta['list']:
            yield dict(**file, date=meta['groupname'])


def get_image_url(login_fn, post_fn, date, md5):
    """Fetch the download URL of an image."""
    payload = (
        # welcome to the world of PHP!
        'id=cm_photo_download&groups%5B0%5D%5Bgroupname%5D={date}'
        '&groups%5B0%5D%5Ball%5D=0&groups%5B0%5D%5Bkeys%5D%5B%5D={md5}'
    )
    for attempt in range(1, 10):
        resp = post_fn(
            API_URL,
            data=payload.format(date=date, md5=md5),
            headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        )
        assert resp.status_code == 200
        if resp.json().get('ret', 0) == 0:
            return resp.json()['data']['url']
        print('Download attempt #{} failed, will retry...'.format(attempt))
        login_fn()
    raise RuntimeError('Failed to fetch image URL.')


def set_file_mtime(fname, date):
    """Set file creation/modification time."""
    ts = time.mktime(dateparser.parse(date).timetuple())
    os.utime(fname, (ts, ts))


def run(email, password):
    """Run the downloader."""
    with requests.Session() as session:
        login_fn = partial(login, session, email, password)
        post_fn = partial(session.post)
        get_fn = partial(session.get)
        for meta in all_file_metadata(login_fn, post_fn):
            fname, date, md5 = meta['file_name'], meta['date'], meta['key']
            if not file_exists(fname):
                url = get_image_url(login_fn, post_fn, date, md5)
                download_image(login_fn, get_fn, url, fname)
                set_file_mtime(fname, date)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('Usage: python download_all.py <email> [password]')
        sys.exit(1)
    email, password = sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else getpass()
    run(email, password)
