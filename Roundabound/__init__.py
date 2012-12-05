import glob
import os
import os.path
import time
import logging
from zipfile import ZipFile

class LogRotationError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

def parse_age(arg):
        return int(arg) * 24 * 60 * 60;

class RotationSet:
    def __init__(self, config):
        self.file_pattern = config['pattern']
        self.archive_age = None
        self.delete_age = None
        self.archive_path = None

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
            stat = os.stat(filename)
            age = now - stat.st_mtime

            logging.debug('Examining file %s; age %d' % (filename, age))

            if self.archive_age != None and age > self.archive_age:
                self._archive(filename)
            elif self.delete_age != None and age > self.delete_age:
                os.remove(filename)
                logging.info('Deleted %s' % filename)

        for filename in glob.glob(self.archive_file_pattern):
            stat = os.stat(filename)
            age = now - stat.st_mtime

            logging.debug('Examining file %s; age %d' % (filename, age))

            if self.delete_age != None and age > self.delete_age:
                os.remove(filename)
                logging.info('Deleted %s' % filename)

    def _archive(self, filename):
        if self.archive_path != None:
            (path, name) = os.path.split(filename)
            archived_name = os.path.join(self.archive_path, name + '.zip')
        else:
            archived_name = filename + '.zip'

        with ZipFile(archived_name, 'w') as zip_file:
            zip_file.write(filename)

        os.remove(filename)
        logging.info('Archived %s to %s' % (filename, archived_name))

class LogRotate:
    def __init__(self, config):
        if not config.has_key('sets'):
            raise LogRotationError('Configuration is missing key "sets".')

        self.sets = {}
        for (set_name, set_config) in config["sets"].items():
            self.sets[set_name] = RotationSet(set_config)

    def rotate(self):
        logging.info('Starting log rotation')
        for (set_name, rotation_set) in self.sets.items():
            logging.info('Rotating %s' % set_name)
            try:
                rotation_set.rotate()
            except Exception, e:
                logging.error('Encountered error while rotating set "%s".'
                    % set_name, exc_info=True)

        logging.debug('Log rotation done')

def main(argv):
    import json
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='roundabound.cfg', help='the configuration file to use')
    parser.add_argument('--verbosity', default='ERROR', help='indicates the verbosity of the output', choices=['DEBUG', 'INFO', 'WARN', 'ERROR'])

    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.verbosity))

    with open(args.config, 'r') as config_file:
        config = json.loads(config_file.read())

    logrotate = LogRotate(config)
    logrotate.rotate()

if __name__ == '__main__':
    import sys
    main(sys.argv)
