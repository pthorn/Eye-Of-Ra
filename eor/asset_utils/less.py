# coding: utf-8

import os
import stat
import subprocess

from .. import app_conf

import logging
log = logging.getLogger(__name__)


"""
    installing less
        ubuntu: sudo apt-get install git-core build-essential openssl libssl-dev
        download node-v*.tar.gz from http://nodejs.org/download/
        ./configure --prefix=~/local/    (requires recent python; npm installed automatically)
        make && make install
        ~/local/bin/npm set global true
        ~/local/bin/npm install less
"""

def _run_command(cmd, add_to_path=None):
    env = {
        'HOME': os.environ.get('HOME', ''),
        'LOGNAME': os.environ.get('LOGNAME', ''),
        'USER': os.environ.get('USER', ''),
        'LANG': os.environ.get('LANG', ''),
        'SHELL': os.environ.get('SHELL', ''),
        'SHLVL': os.environ.get('SHLVL', ''),
        'PWD': os.environ.get('PWD', ''),
        'PATH': os.environ.get('PATH', '')
    }
    if add_to_path:
        env['PATH'] = '%s:%s' % (add_to_path, env['PATH'])

    # try:
    popen = subprocess.Popen(cmd, shell=True, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
    #except:
    retcode = popen.wait()
    if retcode != 0:
        log.error(u'error running command (exit code %s): %s' % (retcode, cmd))
        log.error(u'..output: %s ' % (popen.stdout.read(),))
        return False

    return True

def compile_less(css_files):

    lessc_path = app_conf('lessc-path')
    try:
        mode = os.stat(lessc_path).st_mode
        # TODO test if file is executable?
    except OSError, e:
        log.error(u'lessc: %s' % (unicode(e,)))
        return False

    for group in css_files:

        # find latest modification time for source files in group
        source_mtime = 0.0
        source_error = False
        for src_file in group['source']:
            try:
                source_mtime = max(source_mtime, os.stat(src_file).st_mtime) # float
            except OSError, e:
                source_error = True
                log.error(u'cannot open source file %s: %s (cwd=%s)' % (src_file, unicode(e), os.getcwd()))
        if source_error:
            log.warn('not regenerating %s due to errors' % (group['dest'],))
            continue

        try:
            dest_mtime = os.stat(group['dest']).st_mtime
        except OSError:
            dest_mtime = None # file doesn't exist, this is normal

        if not dest_mtime or source_mtime >= dest_mtime:
            source_paths = ' '.join([p for p in group['source']])
            res = _run_command('cat %s | %s --no-color --yui-compress -O2 - > %s' % (source_paths, lessc_path, group['dest']),
                add_to_path=os.path.dirname(lessc_path))
            if res:
                log.info('compiled css: %s > %s' % (source_paths, group['dest']))
            else:
                try:
                    os.unlink(group['dest'])
                except OSError:
                    pass
