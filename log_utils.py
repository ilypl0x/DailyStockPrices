import sys
import os
import re
from datetime import datetime
from queue import Queue
from threading import Thread

def create_logger(filename,clsname,level,stdout=False):
    formatter = _log.Formatter(fmt='%(asctime)s %(levelname)-4s %(message)s',
                                datefmt='%Y-%m-%d %H:%M:%S')

    logger = _log.getLogger(clsname)
    logger.setLevel(level)

    filehandler = _handlers.TimedRotatingFileHandler(filename, when = 'midnight', backupCount=5)
    filehandler.setFormatter(formatter)
    logger.addHandler(filehandler)

    if stdout:
        stdouthandler = _log.StreamHandler(stream=sys.stdout)
        stdouthandler.setFormatter(formatter)
        logger.addHandler(stdouthandler)

    return logger


class Logger(object):
    ''' console_print (Boolean): Determines if log statements should be printed to stdout
    log_filename (String): Filename of log
    log_dir (string): Filepath to log directory
    queue_enabled (Boolean): Determines if log statements should be added to queue or to be run later
    thread_count (Integer): Determines number of threads to use for processing queue
    '''

    def __init__(self):
        self.DEBUG_LEVELS = {'ERROR': 40, 'INFO': 20, 'DEBUG':10}
        self.debug_level = 'INFO'
        self.console_print = False
        self.log_filename = 'main.log'
        self.log_dir = 'LOGS'
        self.queue_enabled = False
        self.log_filepath = os.path.join(self.log_dir,self.log_filename)

    def setup_log_dir(self):
        if self.queue_enabled:
            thread_count = params.get('thread_count',8)
            self.setup_queue(thread_count)

        self.create_log_directory()
        self.log_filepath = os.path.join(self.log_dir, self.log_filename)
        self.back_up_prior_day_log()

    def is_valid(self,key,value):
        if key == 'debug_level':
            if value not in self.DEBUG_LEVELS.keys():
                raise Exception('Unknown config value {%s} for {%s}' %(value,key))
        return True
    
    def queue_writer(self):
        while True:
            level, message = self.q.get()
            self._write(level, message)
            self.q.task_done()

    def setup_queue(self,thread_count):
        '''should call wait() before exiting program or lags may be truncated'''
        self.q = Queue(maxsize=0)
        for i in range(thread_count):
            worker = Thread(target=self.queue_writer,args=())
            worker.setDaemon(True)
            worker.start()

    def config(self,params):
        for key,value in params.items():
            class_variables = [attr for attr in dir(self) if not callable(getattr(self,attr)) and not attr.startswith("__")]
            if key in class_variables and self.is_valid(key,value):
                setattr(self, key,value)
        self.setup_log_dir()
        return self
    
    def create_log_directory(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def _get_last_log_date(self):
        with open(self.log_filepath, 'r') as f:
            m = re.search('(\d{4}-\d{2}-\d{2}).*', f.readline())
            if m:
                return m.group(1)

    def back_up_prior_day_log(self):
        try:
            fsize = os.stat(self.log_filepath).st_size
            if fsize > 0:
                last_log_date = self._get_last_log_date()
                if last_log_date and last_log_date != datetime.now().strftime('%Y-%m-%d'):
                    try:
                        os.rename(self.log_filepath,self.log_filepath + '.' + last_log_date)
                    except PermissionError as e:
                        self._write('ERROR','Log file is already open. Cannot move prior day log at this time.')
        except FileNotFoundError as e:
            pass
    
    def _write(self,level,message):
        if self.DEBUG_LEVELS[self.debug_level] > self.DEBUG_LEVELS[level.upper()]:
            return
        
        msg = '%s - %s - %s' %(datetime.now(),level,message)
        if self.console_print:
            print(msg)

        try:
            f = open(self.log_filepath, "a")
        except FileNotFoundError:
            self.setup_log_dir()
            f = open(self.log_filepath, "a")
        f.write(msg + "\n")

    def queue_or_write(self, level, message):
        if self.queue_enabled:
            self.q.put((level, message))
        else:
            self._write(level, message)

    def error(self, message):
        self.queue_or_write('ERROR', message)

    def info(self, message):
        self.queue_or_write('INFO', message)

    def debug(self, message):
        self.queue_or_write('DEBUG', message) 

    def wait(self):
        if not hasattr(self, 'q'):
            print('Queue is Disabled. Ignoring Logger.wait() function.')
            return
        self.q.join()

def get_logger(params={}):
    global logger
    if not logger:
        logger = Logger()
    if params:
        logger.config(params)
    return logger

logger = None               
