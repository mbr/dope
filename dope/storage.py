from hashlib import sha1
import os

from simplekv.fs import FilesystemStore, WebFilesystemStore

from .model import db, File


class Storage(object):
    def __init__(self, store):
        # write-lock, required to avoid deletion of uploaded files before
        # refcount checking is complete
        self.store = store

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
        if File.get_refcount(digest) > 0:
            # this should not block until the upload is complete, because the
            # db can figure out that reading other stuff is fine. hopefully
            file.stream.seek(0)
            self.store.put_file(digest, file.stream)

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
            base_store = FilesystemStore(path)
        else:
            base_store = WebFilesystemStore(path, storage_url_prefix)
        super(FilesystemStorage, self).__init__(base_store)
