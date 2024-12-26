import logging

def setup_logger(log_file, logger_name="IperfApp"):
    """
    Sets up a logger with file and console handlers.
    
    :param log_file: Path to the log file
    :param logger_name: Name of the logger
    :return: Configured logger
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    if not logger.hasHandlers():
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

# 
#from logger import setup_logger

#logger = setup_logger('client.log', logger_name='IperfClient')
#logger.info("Client initialized.")

#from logger import setup_logger

#logger = setup_logger('server.log', logger_name='IperfServer')
#logger.info("Server started successfully.")

