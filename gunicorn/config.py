# Sample Gunicorn configuration file.

#
# Server socket
#
#   bind - The socket to bind.
#
#       A string of the form: 'HOST', 'HOST:PORT', 'unix:PATH'.
#       An IP is a valid HOST.
#
#   backlog - The number of pending connections. This refers
#       to the number of clients that can be waiting to be
#       served. Exceeding this number results in the client
#       getting an error when attempting to connect. It should
#       only affect servers under significant load.
#
#       Must be a positive integer. Generally set in the 64-2048
#       range.
#
import os
from dotenv import find_dotenv

from vyperlogix.env.environ import MyDotEnv

def __escape(v):
    from urllib import parse
    return parse.quote_plus(v)

def __unescape(v):
    from urllib import parse
    return parse.unquote_plus(v)

__env__ = {}
env_literals = []
def get_environ_keys(*args, **kwargs):
    from expandvars import expandvars
    
    k = kwargs.get('key')
    v = kwargs.get('value')
    assert (k is not None) and (v is not None), 'Problem with kwargs -> {}, k={}, v={}'.format(kwargs,k,v)
    __logger__ = kwargs.get('logger')
    if (k == '__LITERALS__'):
        for item in v:
            env_literals.append(item)
    if (isinstance(v, str)):
        v = expandvars(v) if (k not in env_literals) else v
        v = __escape(v) if (k in __env__.get('__ESCAPED__', [])) else v
    ignoring = __env__.get('IGNORING', [])
    environ = kwargs.get('environ', None)
    if (isinstance(environ, dict)):
        environ[k] = v
    if (k not in ignoring):
        __env__[k] = v
    if (__logger__):
        __logger__.info('\t{} -> {}'.format(k, environ.get(k)))
    return tuple([k,v])

dotenv = MyDotEnv(find_dotenv(), verbose=True, interpolate=True, override=True, callback=get_environ_keys)
dotenv.set_as_environment_variables()

normalize = lambda v,t:t(eval(str(v)))

bind = "{}:{}".format(os.environ.get('host', '0.0.0.0'), os.environ.get('port', '9999'))
backlog = normalize(os.environ.get('gunicorn_backlog', 128), int)

print('GUNICORN (1) :: bind -> {}'.format(bind))
print('GUNICORN (2) :: backlog -> {}'.format(backlog))

#
# Worker processes
#
#   workers - The number of worker processes that this server
#       should keep alive for handling requests.
#
#       A positive integer generally in the 2-4 x $(NUM_CORES)
#       range. You'll want to vary this a bit to find the best
#       for your particular application's work load.
#
#   worker_class - The type of workers to use. The default
#       sync class should handle most 'normal' types of work
#       loads. You'll want to read
#       http://docs.gunicorn.org/en/latest/design.html#choosing-a-worker-type
#       for information on when you might want to choose one
#       of the other worker classes.
#
#       A string referring to a Python path to a subclass of
#       gunicorn.workers.base.Worker. The default provided values
#       can be seen at
#       http://docs.gunicorn.org/en/latest/settings.html#worker-class
#
#   worker_connections - For the eventlet and gevent worker classes
#       this limits the maximum number of simultaneous clients that
#       a single process can handle.
#
#       A positive integer generally set to around 1000.
#
#   timeout - If a worker does not notify the master process in this
#       number of seconds it is killed and a new worker is spawned
#       to replace it.
#
#       Generally set to thirty seconds. Only set this noticeably
#       higher if you're sure of the repercussions for sync workers.
#       For the non sync workers it just means that the worker
#       process is still communicating and is not tied to the length
#       of time required to handle a single request.
#
#   keepalive - The number of seconds to wait for the next request
#       on a Keep-Alive HTTP connection.
#
#       A positive integer. Generally set in the 1-5 seconds range.
#
import multiprocessing
__workers__ = (multiprocessing.cpu_count() * 2) + 1
workers = normalize(os.environ.get('gunicorn_workers', 3), int)
print('GUNICORN (3) :: __workers__ -> {}, workers -> {}'.format(__workers__, workers))
assert workers <= __workers__, 'Cannot exceed the theoretical upper-limit for workers which is now {}.'.format(__workers__)

worker_class = os.environ.get('gunicorn_worker_class', 'gevent')  # 'sync' or 'eventlet'
print('GUNICORN (4) :: worker_class -> {}'.format(worker_class))
worker_connections = normalize(os.environ.get('gunicorn_worker_connections', 1000), int)
print('GUNICORN (5) :: worker_connections -> {}'.format(worker_connections))
timeout = normalize(os.environ.get('gunicorn_timeout', 180), int)
print('GUNICORN (6) :: timeout -> {}'.format(timeout))
keepalive = normalize(os.environ.get('gunicorn_keepalive', 10), int)
print('GUNICORN (7) :: keepalive -> {}'.format(keepalive))
graceful_timeout = normalize(os.environ.get('gunicorn_graceful_timeout', 30), int)
print('GUNICORN (8) :: graceful_timeout -> {}'.format(graceful_timeout))

threads = normalize(os.environ.get('gunicorn_threads', workers), int)
print('GUNICORN (9) :: threads -> {}'.format(threads))

pidfile = os.environ.get('gunicorn_pidfile')
if (pidfile is not None):
    pidfile = os.path.abspath(pidfile)
print('GUNICORN (10) :: pidfile -> {}'.format(pidfile))
#
#   spew - Install a trace function that spews every line of Python
#       that is executed when running the server. This is the
#       nuclear option.
#
#       True or False
#

spew = False

#
# Server mechanics
#
#   daemon - Detach the main Gunicorn process from the controlling
#       terminal with a standard fork/fork sequence.
#
#       True or False
#
#   raw_env - Pass environment variables to the execution environment.
#
#   pidfile - The path to a pid file to write
#
#       A path string or None to not write a pid file.
#
#   user - Switch worker processes to run as this user.
#
#       A valid user id (as an integer) or the name of a user that
#       can be retrieved with a call to pwd.getpwnam(value) or None
#       to not change the worker process user.
#
#   group - Switch worker process to run as this group.
#
#       A valid group id (as an integer) or the name of a user that
#       can be retrieved with a call to pwd.getgrnam(value) or None
#       to change the worker processes group.
#
#   umask - A mask for file permissions written by Gunicorn. Note that
#       this affects unix socket permissions.
#
#       A valid value for the os.umask(mode) call or a string
#       compatible with int(value, 0) (0 means Python guesses
#       the base, so values like "0", "0xFF", "0022" are valid
#       for decimal, hex, and octal representations)
#
#   tmp_upload_dir - A directory to store temporary request data when
#       requests are read. This will most likely be disappearing soon.
#
#       A path to a directory where the process owner can write. Or
#       None to signal that Python should choose one on its own.
#

daemon = normalize(os.environ.get('gunicorn_daemon', False), bool)
print('GUNICORN (11) :: daemon -> {}'.format(daemon))
raw_env = []
tmp_upload_dir = None

#
#   Logging
#
#   logfile - The path to a log file to write to.
#
#       A path string. "-" means log to stdout.
#
#   loglevel - The granularity of log output
#
#       A string of "debug", "info", "warning", "error", "critical"
#

errorlog = os.environ.get('gunicorn_errorlog')
print('GUNICORN (12.1) :: errorlog -> {}'.format(errorlog))
if (errorlog is not None):
    errorlog = os.path.abspath(errorlog)
print('GUNICORN (12.2) :: errorlog -> {}'.format(errorlog))
if (os.path.exists(errorlog)):
    os.remove(errorlog)
loglevel = os.environ.get('gunicorn_loglevel', 'info')
accesslog = os.environ.get('gunicorn_accesslog')
print('GUNICORN (13.1) :: accesslog -> {}'.format(accesslog))
if (accesslog is not None):
    accesslog = os.path.abspath(accesslog)
print('GUNICORN (13.2) :: accesslog -> {}'.format(accesslog))
if (os.path.exists(accesslog)):
    os.remove(accesslog)
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

#
# Process naming
#
#   proc_name - A base to use with setproctitle to change the way
#       that Gunicorn processes are reported in the system process
#       table. This affects things like 'ps' and 'top'. If you're
#       going to be running more than one instance of Gunicorn you'll
#       probably want to set a name to tell them apart. This requires
#       that you install the setproctitle module.
#
#       A string or None to choose a default of something like 'gunicorn'.
#

proc_name = os.environ.get('gunicorn_proc_name', 'vyperapi')
print('GUNICORN (14) :: proc_name -> {}'.format(proc_name))

#
# Server hooks
#
#   post_fork - Called just after a worker has been forked.
#
#       A callable that takes a server and worker instance
#       as arguments.
#
#   pre_fork - Called just prior to forking the worker subprocess.
#
#       A callable that accepts the same arguments as after_fork
#
#   pre_exec - Called just prior to forking off a secondary
#       master process during things like config reloading.
#
#       A callable that takes a server instance as the sole argument.
#

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_fork(server, worker):
    pass

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

    ## get traceback info
    import threading, sys, traceback
    id2name = {th.ident: th.name for th in threading.enumerate()}
    code = []
    for threadId, stack in sys._current_frames().items():
        code.append("\n# Thread: %s(%d)" % (id2name.get(threadId,""),
            threadId))
        for filename, lineno, name, line in traceback.extract_stack(stack):
            code.append('File: "%s", line %d, in %s' % (filename,
                lineno, name))
            if line:
                code.append("  %s" % (line.strip()))
    worker.log.debug("\n".join(code))

def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")
