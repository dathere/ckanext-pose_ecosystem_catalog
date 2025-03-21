import os
import requests

from requests_toolbelt import MultipartEncoder
from config import Config

ckanConfig = Config.get('ckan')


def action(action, data_dict, file_dict=None):
    fields = data_dict

    if file_dict:
        data_dict['upload'] = (
            file_dict.get('file_name'),
            open(os.path.abspath(file_dict.get('path')), 'rb'),
            'application/octet-stream'
        )
        fields = dict(data_dict)
        m = MultipartEncoder(fields=fields)
        r = requests.post(
            ckanConfig.get('url') + '/api/action/' + action,
            data=m,
            headers={
                'content-type': m.content_type,
                'Authorization': ckanConfig.get('api_key')
            }
    )

    else:
        fields = {}
        for key, value in data_dict.items():
            if key == 'tags' or 'extras':
                fields[key] = value
            else:
                fields[key] = str(value)
        r = requests.post(
            ckanConfig.get('url') + '/api/action/' + action,
            json=fields,
            headers={
                'Content-Type': 'application/json',
                'Authorization': ckanConfig.get('api_key')
            }
        )

    print(r.json())
    print("\n")

    return r
