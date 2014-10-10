import json
import requests
from requests_oauthlib import OAuth1
from stacksync.file_metadata import FileMetadataHelper
from django.conf import settings
from base64 import *


class Api:
    ROOT_FOLDER = u'0'
    DEFAULT_FILE_URL = settings.URL_STACKSYNC + '/file/'
    DEFAULT_FOLDER_URL = settings.URL_STACKSYNC + '/folder/'

    def metadata(self, access_token_key, access_token_secret):
        return self.metadata_focus(self.ROOT_FOLDER, access_token_key, access_token_secret)

    def metadata_focus(self, folder_id, access_token_key, access_token_secret):
        url = self.DEFAULT_FOLDER_URL + folder_id +'/contents'
        headeroauth, headers = self.get_oauth_headers(access_token_key, access_token_secret)
        r = requests.get(url, auth=headeroauth, headers=headers, verify=False)
 
        response = r.status_code
 
        folder_list = []
        file_list = []
        if response == 200:
            json_data = r.json()
            file_metadata_helper = FileMetadataHelper(json_data)

            if folder_id != self.ROOT_FOLDER:
                file_metadata_helper.add_initial_subfolder_metadata(folder_list)

            file_metadata_helper.filter_metadata_by_type(file_list, folder_list)

        folder_list = folder_list + file_list
        return folder_list
 
    def upload_file(self, name, files, parent, access_token_key, access_token_secret ):
        headeroauth, headers = self.get_oauth_headers(access_token_key, access_token_secret)
     
        if parent:
            url = settings.URL_STACKSYNC + '/file?name='+name+'&parent='+parent
        else:
            url = settings.URL_STACKSYNC + '/file?name='+name

        r = requests.post(url,data=files, auth=headeroauth, headers=headers, verify=False)

    def get_oauth_headers(self, access_token_key, access_token_secret):
        headers = {'Stacksync-api': 'v2', 'Content-Type': 'application/json'}
        headeroauth = OAuth1(settings.STACKSYNC_CONSUMER_KEY, settings.STACKSYNC_CONSUMER_SECRET,
                             access_token_key, access_token_secret,
                             signature_type='auth_header', signature_method='PLAINTEXT')
        return headeroauth, headers

    def delete_file(self, file_id, access_token_key, access_token_secret):
        headeroauth, headers = self.get_oauth_headers(access_token_key, access_token_secret)
         
        url = self.DEFAULT_FILE_URL+file_id
        r = requests.delete(url, auth=headeroauth, headers=headers, verify=False)

        flist = self.metadata(access_token_key, access_token_secret)
        return flist

    def delete_folder(self, folder_id, access_token_key, access_token_secret):
        headeroauth, headers = self.get_oauth_headers(access_token_key, access_token_secret)
        url = self.DEFAULT_FOLDER_URL+folder_id
        r = requests.delete(url, auth=headeroauth, headers=headers, verify=False)
 
        return r.json
        
    def rename_folder(self, folder_id, folder_name, access_token_key, access_token_secret):
        headeroauth, headers = self.get_oauth_headers(access_token_key, access_token_secret)
        url = self.DEFAULT_FOLDER_URL+folder_id
        if not folder_name or folder_name == "":
            return json.dumps({'error':'nothing to update'})
        
        data = json.dumps({'name':folder_name})
        r = requests.put(url, data=data, auth=headeroauth, headers=headers, verify=False)
        return r.content
    
    def rename_file(self, file_id, file_name, access_token_key, access_token_secret):
        headeroauth, headers = self.get_oauth_headers(access_token_key, access_token_secret)
        url = self.DEFAULT_FILE_URL+file_id
        if not file_name or file_name == "":
            return json.dumps({'error':'nothing to update'})
        
        data = json.dumps({'name':file_name})
        r = requests.put(url, data=data, auth=headeroauth, headers=headers, verify=False)
        return r.content
    
    def download_file(self, file_id, access_token_key, access_token_secret):
         
        headeroauth, headers = self.get_oauth_headers(access_token_key, access_token_secret)
         
        url = self.DEFAULT_FILE_URL+file_id+'/data'
 
        r = requests.get(url, auth=headeroauth, headers=headers, stream=False, verify=False)
    
        return r.content

    def download_pdf(self, file_id, access_token_key, access_token_secret):

        headeroauth, headers = self.get_oauth_headers(access_token_key, access_token_secret)

        url = self.DEFAULT_FILE_URL+file_id+'/data'

        r = requests.get(url, auth=headeroauth, headers=headers, stream=False, verify=False)

        content_type = r.headers.get('content-type')
        pdf64 = b64encode(r.content)
        pdf = "data:"+content_type+";base64,"+pdf64
        return pdf

    def download_img(self, file_id, access_token_key, access_token_secret):
 
        headeroauth, headers = self.get_oauth_headers(access_token_key, access_token_secret)
         
        url = self.DEFAULT_FILE_URL+file_id+'/data'
         
        r = requests.get(url, auth=headeroauth, headers=headers, stream=False, verify=False)
        content_type = r.headers.get('content-type')
        image64 = b64encode(r.content)
        image = "data:"+content_type+";base64,"+image64
        return image
 
 
    def metadata_file(self, file_id, access_token_key, access_token_secret):
        headeroauth, headers = self.get_oauth_headers(access_token_key, access_token_secret)
         
        url = self.DEFAULT_FILE_URL+file_id
        r = requests.get(url, auth=headeroauth, headers=headers, verify=False)
        response = r.status_code
 
        flist = []
        if response == 200:
            json_data = r.json()

            flist.append(json_data['mimetype'])
            flist.append(json_data['filename'])
 
        return flist
 
 
    def create_folder(self, folder_name, parent, access_token_key, access_token_secret):
        headeroauth, headers = self.get_oauth_headers(access_token_key, access_token_secret)

        if parent:
            data = {'name':folder_name, 'parent':parent}
        else:
            data = {'name':folder_name}
         
        data = json.dumps(data)
        url = settings.URL_STACKSYNC + '/folder'
        r = requests.post(url,data=data, auth=headeroauth, headers=headers, verify=False)
 
        response = r.status_code
        if response == 200:
            json_data = json.loads(r.content)
 
        return response

    def share_folder(self, folder_id, allowed_user_emails=[], access_token_key=None, access_token_secret=None):
        headeroauth, headers = self.get_oauth_headers(access_token_key, access_token_secret)
        url = self.DEFAULT_FOLDER_URL + str(folder_id) + '/share'

        json_payload = json.dumps(allowed_user_emails)

        r = requests.post(url, data=json_payload, auth=headeroauth, headers=headers, verify=False)
        return r

    def get_members_of_folder(self, folder_id, access_token_key=None, access_token_secret=None):

        headeroauth, headers = self.get_oauth_headers(access_token_key, access_token_secret)
        url = self.DEFAULT_FOLDER_URL + str(folder_id) + '/members'

        response = requests.get(url, auth=headeroauth, headers=headers, verify=False)

        if response.status_code == 200:
            return response.json()
        else:
            response.reason = response.reason + ". "+response.content
            response.raise_for_status()

    #
    def get_folder_size(folder_list):
        pass
    #     total = 0
    #     for item in folder_list:
    #         if item['is_folder']:
    #             total +=





