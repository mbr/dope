from hashlib import sha1
import os
from urllib import quote

from boto.s3.key import Key

from simplekv.fs import FilesystemStore, WebFilesystemStore

from .model import db, File


class Storage(object):
    def store_uploaded_file(self, file):
        h = sha1()

        BUFSIZE = h.block_size * 64
        filesize = 0

        # compute digest first, maybe we do not need to store the file
        for chunk in iter(lambda: file.stream.read(BUFSIZE), b''):
            h.update(chunk)
            filesize += len(chunk)

        digest = h.hexdigest()

        db.session.connection(execution_options={
            # note: with a little extra care, we could probably be using
            # read-committed as well
            'isolation_level': 'SERIALIZABLE',
        })

        # check if we need to upload
        filename = unicode(file.filename)
        if File.get_refcount(digest) == 0:
            # this should not block until the upload is complete, because the
            # db can figure out that reading other stuff is fine. hopefully
            file.stream.seek(0)
            self._store_file(digest, file.stream)

        f = File(
            hash=digest,
            size=filesize,
            filename=filename,
        )
        db.session.add(f)
        db.session.commit()

        return f


class FilesystemStorage(Storage):
    def __init__(self, path, storage_url_prefix=None):
        if not os.path.exists(path):
            raise RuntimeError('Path {} does not exist'.format(path))

        if storage_url_prefix is None:
            self.store = FilesystemStore(path)
        else:
            self.store = WebFilesystemStore(path, storage_url_prefix)

    def _store_file(self, hash, file):
        self.store.put_file(hash, file)

    def get_download_url(self, file):
        if hasattr(self.store, 'url_for'):
            return self.store.url_for(file.hash)


class BotoStorage(Storage):
    def __init__(self, bucket, reduced_redundancy=False):
        self.bucket = bucket
        self.reduced_redundancy = reduced_redundancy

    def _store_file(self, hash, file):
        k = Key(self.bucket, hash)
        k.set_contents_from_file(
            file,
            reduced_redundancy=self.reduced_redundancy,
        )
        k.set_acl('public-read')

    def get_download_url(self, file):
        k = Key(self.bucket, file.hash)
        url = k.generate_url(
            expires_in=60,  # valid for one minute
            query_auth=True,
            response_headers={
                'response-content-disposition': 'attachment; filename="{}"'
                .format(quote(file.filename.encode('utf8')))}
        )
        return url
