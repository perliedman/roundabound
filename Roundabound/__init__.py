# Needed to get with statement working in Python 2.5
from __future__ import with_statement
import glob
import os
import os.path
import time
import logging
import zipfile

class LogRotationError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

def parse_age(arg):
        return int(arg) * 24 * 60 * 60;

class RotationSet:
    def __init__(self, config, dry_run=False):
        self.file_pattern = config['pattern']
        self.archive_age = None
        self.delete_age = None
        self.archive_path = None
        self.dry_run = dry_run

        if config.has_key('archive_age'):
            self.archive_age = parse_age(config['archive_age'])

        if config.has_key('archive_path'):
            self.archive_path = config['archive_path']
            (file_path, file_pattern) = os.path.split(self.file_pattern)
            self.archive_file_pattern = \
                os.path.join(self.archive_path, file_pattern + ".zip")
        else:
            self.archive_file_pattern = self.file_pattern + ".zip"

        if config.has_key('delete_age'):
            self.delete_age = parse_age(config['delete_age'])

    def rotate(self):
        now = time.time()
        for filename in glob.glob(self.file_pattern):
            try:
                stat = os.stat(filename)
                age = now - stat.st_mtime

                logging.debug('Examining file %s; age %d' % (filename, age))

                if self.archive_age != None and age > self.archive_age:
                    self._archive(filename)
                elif self.delete_age != None and age > self.delete_age:
                    self._do_action(lambda x: os.remove(filename))
                    logging.info('Deleted %s' % filename)
            except WindowsError, e:
                if e.winerror == 5:
                    logging.warning('Access denied for "%s".' % filename)

        for filename in glob.glob(self.archive_file_pattern):
            stat = os.stat(filename)
            age = now - stat.st_mtime

            logging.debug('Examining file %s; age %d' % (filename, age))

            if self.delete_age != None and age > self.delete_age:
                self._do_action(lambda x: os.remove(filename))
                logging.info('Deleted %s' % filename)

    def _archive(self, filename):
        if self.archive_path != None:
            (path, name) = os.path.split(filename)
            archived_name = os.path.join(self.archive_path, name + '.zip')
        else:
            archived_name = filename + '.zip'

        self._do_action(lambda x: self._do_archive(filename, archived_name, name))
        logging.info('Archived %s to %s' % (filename, archived_name))

    def _do_archive(self, filename, archived_name, name):
        with zipfile.ZipFile(archived_name, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(filename, name)

        os.remove(filename)

    def _do_action(self, action):
        if not self.dry_run:
            action(None)

class LogRotate:
    def __init__(self, config, dry_run=False):
        if not config.has_key('sets'):
            raise LogRotationError('Configuration is missing key "sets".')

        self.dry_run = dry_run

        self.sets = {}
        for (set_name, set_config) in config["sets"].items():
            self.sets[set_name] = RotationSet(set_config, dry_run)

    def rotate(self):
        logging.info('Starting log rotation')

        if self.dry_run:
            logging.warning('Running in dry run mode. No files will be altered.')

        for (set_name, rotation_set) in self.sets.items():
            logging.info('Rotating %s' % set_name)
            try:
                rotation_set.rotate()
            except Exception, e:
                logging.error('Encountered error while rotating set "%s".'
                    % set_name, exc_info=True)

        logging.debug('Log rotation done')

def main(argv):
    try:
        import json
    except ImportError:
        import simplejson

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='roundabound.cfg', help='the configuration file to use')
    parser.add_argument('--verbosity', default='WARN', help='indicates the verbosity of the output', choices=['DEBUG', 'INFO', 'WARN', 'ERROR'])
    parser.add_argument('--dry-run', action='store_true', help='If set, will not actually do anything, just log actions.')

    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.verbosity))

    with open(args.config, 'r') as config_file:
        config = json.loads(config_file.read())

    logrotate = LogRotate(config, args.dry_run)
    logrotate.rotate()

if __name__ == '__main__':
    import sys
    main(sys.argv)
