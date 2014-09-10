import datetime
import time

class FileMetadata:
    def __init__(self, name, date, file_id, is_folder,  size, mimetype):
        self.name = name
        DB_TIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f'
        date_aux = datetime.datetime.fromtimestamp(time.mktime(time.strptime(date, DB_TIME_FORMAT)))
        self.date = date_aux
        self.file_id = file_id
        self.is_folder = is_folder
        self.size = size
        self.mimetype = mimetype

    @staticmethod
    def compute_size(json_content):
        total_size = 0
        for item in json_content['contents']:
            total_size += item['size']

        return total_size
