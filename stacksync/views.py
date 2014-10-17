from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import render

from stacksync.forms import contact_form, file_form
from django.contrib.auth import get_user_model
from django.http import HttpResponse, HttpResponseRedirect, StreamingHttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.mail import EmailMessage

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control

from stacksync.connection_api import Api
from stacksync.bread_crumbs import BreadCrumbs
from django.core.mail import send_mail
from django.conf import settings

import os
from django.core.servers.basehttp import FileWrapper
from django.utils.timezone import utc
from datetime import timedelta
import datetime
import time

import json
import requests
import datetime
import urllib
from requests_oauthlib import OAuth1
from urlparse import parse_qs



connect = Api()
breadcrumbs = BreadCrumbs()

def log_in(request):
    try:
        if request.session['email']:
            return HttpResponseRedirect('/')
    except:
        None

    if request.method == 'POST':
        form = AuthenticationForm(request.POST)

        if form.is_valid:
            username = request.POST['username']
            password = request.POST['password']
            oauth = OAuth1(client_key="b3af4e669daf880fb16563e6f36051b105188d413", client_secret="c168e65c18d75b35d8999b534a3776cf", callback_uri='oob')
            headers = {"STACKSYNC_API":"v2"}
     
            r = requests.post(url=settings.STACKSYNC_REQUEST_TOKEN_ENDPOINT, auth=oauth, headers=headers, verify=False)
            var = r.content
     
            credentials = parse_qs(r.content)
            resource_owner_key = credentials.get('oauth_token')[0]
            resource_owner_secret = credentials.get('oauth_token_secret')[0]
     
            authorize_url = settings.STACKSYNC_AUTHORIZE_ENDPOINT + '?oauth_token='
            authorize_url = authorize_url + resource_owner_key
            params = urllib.urlencode({'email': username, 'password': password, 'permission':'allow'})
            headers = {"Content-Type":"application/x-www-form-urlencoded", "STACKSYNC_API":"v2"}
            response = requests.post(authorize_url, data=params, headers=headers, verify=False)
     
            if "application/x-www-form-urlencoded" == response.headers['Content-Type']:
                parameters = parse_qs(response.content)
                verifier = parameters.get('verifier')[0]
     
                oauth2 = OAuth1("b3af4e669daf880fb16563e6f36051b105188d413",
                       client_secret="c168e65c18d75b35d8999b534a3776cf",
                       resource_owner_key=resource_owner_key,
                       resource_owner_secret=resource_owner_secret,
                       verifier=verifier,
                       callback_uri='oob')
                r = requests.post(url=settings.STACKSYNC_ACCESS_TOKEN_ENDPOINT, auth=oauth2, headers=headers, verify=False)
                credentials = parse_qs(r.content)
                resource_owner_key = credentials.get('oauth_token')[0]
                resource_owner_secret = credentials.get('oauth_token_secret')[0]

                request.session['access_token_key'] = resource_owner_key
                request.session['access_token_secret'] = resource_owner_secret
                request.session['email'] = username
                request.session.set_expiry(0)
                return HttpResponseRedirect('/')


            notvalid = True
            return render_to_response('login.html', {'form': form, 'notvalid': notvalid},
                                  context_instance=RequestContext(request))
        
        notvalid = True
        return render_to_response('login.html', {'form': form, 'notvalid': notvalid},
                                  context_instance=RequestContext(request))

    else:
        form = AuthenticationForm()
        return render_to_response('login.html', {'form': form}, context_instance=RequestContext(request))


def contact(request):
    if request.method == 'POST':
        form = contact_form(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            send_mail(cd['subject'], cd['message'], cd.get('email', 'noreply@example.com'),
                      ['juanjoolinares@gmail.com'], )
        return render_to_response('thanks.html', {'form': form}, context_instance=RequestContext(request))
    else:
        form = contact_form()
        user = request.session['email']
        return render_to_response('contactform.html', {'user': user, 'form': form},
                                  context_instance=RequestContext(request))
 
def thanks(request):
    user = request.session['email']
    form = contact_form()
    return render_to_response('thanks.html', {'user': user, 'form': form}, context_instance=RequestContext(request))

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def index(request):
    try:
        if request.session['email']:
            if request.method == 'POST':
                files = request.FILES['file']
                filename = files.name
                connect.upload_file(filename, files, request.session['last_folder'],request.session['access_token_key'], request.session['access_token_secret'])
        
                if request.session['last_folder'] == "":
                    return HttpResponseRedirect('/')
                else:
                    return HttpResponseRedirect('/focus/' + request.session['last_folder'])
            else:
        
                request.session['last_folder'] = ""
        
                files = connect.metadata(request.session['access_token_key'], request.session['access_token_secret'])
        
                pathlist = breadcrumbs.del_crumb()
                return render(request,'index.html', {'user': request.session['email'], 
                               'files': files, 'file_id': request.session['last_folder'],
                               'pathlist': pathlist})

        else:
            return HttpResponseRedirect('/log_in')

    except:
        return HttpResponseRedirect('/log_in')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def index_focus(request, file_id):
    user = request.session['email']
    request.session['last_folder'] = file_id
 
    files = connect.metadata_focus(file_id, request.session['access_token_key'], request.session['access_token_secret'])
    pathlist = breadcrumbs.add_crumb(files[0])
    files.pop(0)
 
    if request.method == 'POST':
        files = request.FILES['files']
        filename = files.name
        connect.upload_file(filename, files, request.session['last_folder'], 
                            request.session['access_token_key'], request.session['access_token_secret'])
 
        if request.session['last_folder'] == "":
            return HttpResponseRedirect('/')
        else:
            return HttpResponseRedirect('/focus/' + request.session['last_folder'])
    else:
 
        return render_to_response('index.html',
                                  {'user': request.session['email'], 'files': files, 'file_id': request.session['last_folder'],
                                   'pathlist': pathlist}, context_instance=RequestContext(request))
 
def delete_file(request, file_id):
    files = connect.delete_file(file_id, request.session['access_token_key'], request.session['access_token_secret'])
    if request.session['last_folder'] == "":
        return HttpResponseRedirect('/')
    else:
        return HttpResponseRedirect('/focus/' + request.session['last_folder'])
 
def download_file(request, file_id):
    listData = connect.metadata_file(file_id, request.session['access_token_key'], request.session['access_token_secret'])
    mimetype = listData[0]
    file_name = listData[1]
    files = connect.download_file(file_id, request.session['access_token_key'], request.session['access_token_secret'])
 
#     wrapper = FileWrapper(file(files))
    response = HttpResponse(files, content_type=mimetype)
    response['Content-Disposition'] = 'attachment; filename=%s' % file_name
    response['Content-Length'] = len(files)
    return response
 
def new_folder(request, folder_name):
    listData = connect.create_folder(folder_name, request.session['last_folder'], request.session['access_token_key'], request.session['access_token_secret'])
    if request.session['last_folder'] == "":
        return HttpResponseRedirect('/')
    else:
        return HttpResponseRedirect('/focus/' + request.session['last_folder'])


def delete_folder(request, folder_id):
    files = connect.delete_folder(folder_id, request.session['access_token_key'], request.session['access_token_secret'])
    if request.session['last_folder'] == "":
        return HttpResponseRedirect('/')
    else:
        return HttpResponseRedirect('/focus/' + request.session['last_folder'])
    
def rename_folder(request, folder_id, folder_name):
    response = connect.rename_folder(folder_id, folder_name, request.session['access_token_key'], request.session['access_token_secret'])
    response = json.loads(response)
    if 'error' in response:
        #TODO: Show some message to advert that folder_name is None
        None
        
    if request.session['last_folder'] == "":
        return HttpResponseRedirect('/')
    else:
        return HttpResponseRedirect('/focus/' + request.session['last_folder'])
    
    
def rename_file(request, file_id, file_name):
    response = connect.rename_folder(file_id, file_name, request.session['access_token_key'], request.session['access_token_secret'])
    response = json.loads(response)
    if 'error' in response:
        #TODO: Show some message to advert that folder_name is None
        None
        
    if request.session['last_folder'] == "":
        return HttpResponseRedirect('/')
    else:
        return HttpResponseRedirect('/focus/' + request.session['last_folder'])

# 
def popup_move(request, file_id):
    base = True
 
    if file_id == "root":
        files = connect.metadata(request.session['access_token_key'], request.session['access_token_secret'])
        base = False
        request.session['popup_folder'] = []
        request.session['popup_folder'].append("root")
        request.session.modified = True
 
    elif file_id == "back":
        request.session['popup_folder'].pop()
        file_back = request.session['popup_folder'][-1]
        if file_back == "root":
            files = connect.metadata(request.session['access_token_key'], request.session['access_token_secret'])
            base = False
        else:
            files = connect.metadata_focus(file_back, request.session['access_token_key'], request.session['access_token_secret'])
        request.session.modified = True
 
    else:
        files = connect.metadata_focus(file_id, request.session['access_token_key'], request.session['access_token_secret'])
        request.session['popup_folder'].append(file_id)
        request.session.modified = True
 
    return render_to_response('popupmove.html', {'files': files, 'base': base},
                              context_instance=RequestContext(request))
 
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def pdf(request, file_id):
    pdf_metadata = connect.metadata_file(file_id, request.session['access_token_key'], request.session['access_token_secret'])
    pdf_content = connect.download_pdf(file_id, request.session['access_token_key'], request.session['access_token_secret'])
    browser = request.META['HTTP_USER_AGENT'].split("/")[-2]
    browser = browser.split(" ")[-1]
   
    return render_to_response('pdf.html', {'file_id': file_id, 'pdf_content':pdf_content, 'file_name':pdf_metadata[1]}, context_instance=RequestContext(request))

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def img(request, file_id):
    user = request.session['email']
    image = connect.download_img(file_id, request.session['access_token_key'], request.session['access_token_secret'])
    return render(request,'img.html', {'user': user, 'file_id': file_id, 'img':image})

def log_out(request):
    del request.session['access_token_key']
    del request.session['access_token_secret']
    del request.session['email']
    return HttpResponseRedirect('/log_in')


def share_folder(request, folder_id):
    unformatted_users = request.POST.getlist('email_list[]', [])

    try:
        addresees = [user.strip() for user in unformatted_users]
        [validate_email(user) for user in addresees]
        response = connect.share_folder(folder_id, addresees, request.session['access_token_key'], request.session['access_token_secret'])

        message = {'status_code': response.status_code, 'content': response.content}

    except ValidationError as e:
        message = {'content': e.message + " " + user}
    except Exception as ex:
        message = str(ex)

    json_response = json.dumps(message)
    return HttpResponse(json_response)

def get_members_of_folder(request, folder_id):
    json_response = connect.get_members_of_folder(folder_id, request.session['access_token_key'], request.session['access_token_secret'])
    return HttpResponse(json.dumps(json_response))
