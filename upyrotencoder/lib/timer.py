from boot import MAIN_FILE_LOGGING, MAIN_FILE_MODE, MAIN_FILE_NAME, logfiles
import ulogging
import utime

logger_log_level= 10
logger_setup = 1  # 0 for basicConfig, 1 for custom logger with RotatingFileHandler (RFH)
FileMode = 2 # If logger_setup ==1 (RotatingFileHandler) then access to modes below
            #  FileMode == 1 # no log file
            #  FileMode == 2 # write to log file
logfile = __name__ + '.log'
if logger_setup == 0: # Use basicConfig logger
    ulogging.basicConfig(level=logger_log_level) # Change logger global settings
    logger_timer = ulogging.getLogger(__name__) 
elif logger_setup == 1 and FileMode == 1:         # Using custom logger
    logger_timer = ulogging.getLogger(__name__)
    logger_timer.setLevel(logger_log_level)
elif logger_setup == 1 and FileMode == 2 and not MAIN_FILE_LOGGING:  # Using custom logger with output to log file
    logger_timer = ulogging.getLogger(__name__, logfile, mode='w', autoclose=True, filetime=5000)  # w/wb to over-write, a/ab to append, autoclose (with method), file time in ms to keep file open
    logger_timer.setLevel(logger_log_level)
    logfiles.append(logfile)
elif logger_setup == 1 and FileMode == 2 and MAIN_FILE_LOGGING:            # Using custom logger with output to main log file
    logger_timer = ulogging.getLogger(__name__, MAIN_FILE_NAME, MAIN_FILE_MODE, 0)  # over ride with MAIN_FILE settings in boot.py
    logger_timer.setLevel(logger_log_level)

logger_timer.info(logger_timer)

def Timer(f, *args, **kwargs):
    name = str(f).split(' ')[1]
    def new_func(*args, **kwargs):
        t = utime.ticks_us()
        result = f(*args, **kwargs)
        delta = utime.ticks_diff(utime.ticks_us(), t)
        logger_timer.debug('Function,{},time,{:6.3f},ms'.format(name, delta/1000))
        return result
    return new_func