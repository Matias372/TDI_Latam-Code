import logging

class LogFormatter(logging.Formatter):
    """Formateador personalizado para logs"""
    
    def __init__(self):
        super().__init__(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def format(self, record):
        # Personalizar formato si es necesario
        return super().format(record)