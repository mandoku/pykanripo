#   -*- coding: utf-8 -*-
import requests
import json
import re

from github import Github
from github import UnknownObjectException

apiappend = ""
krp_base = ""
krp_api  = "%s/api/v1.0/" % (krp_base)
kanripo   = "kanripo"
ghkrp    = "https://raw.githubusercontent.com/%s/%s/%s/%s.txt"
titles = {}
apisession = requests.Session()
ghuser = None
# 
TITLES_URL = "https://raw.githubusercontent.com/%s/KR-Workspace/master/Settings/krp-titles.txt"
BYDATE_URL = "https://raw.githubusercontent.com/%s/KR-Workspace/master/Settings/krp-by-date.txt"


def _loadtitles(ghuser=kanripo):
    global titles
    url=TITLES_URL%(ghuser)
    r=apisession.get(url)
    if r.status_code == 200:
        for line in r.text.split("\n"):
            if " " in line:
                l = line.split(" ")
                titles[l[0]] = l[-1]
        return 0
    else:
        return -1    

def _krpapicall(querystring):
    global apiappend
    url = krp_base+"/"+querystring+apiappend
    response = apisession.get(krp_base+"/"+querystring+apiappend).text
    return response


def searchtexts(key):
    return _krpapicall("search?query="+key)

# interact with the github user workspace

def get_workspace(gh, source="kanripo"):
    """Get the repo of the workspace for the user.  ghuser is an
    authenticated Github user object. If not existing, clone the
    workspace from @kanripo or from another account given in
    'source'."""
    ghuser = gh.get_user()
    try:
        ws = ghuser.get_repo("KR-Workspace")
    except (UnknownObjectException):
        ws = ghuser.create_fork(gh.get_repo("%s/KR-Workspace" % (source)))
    return ws

def get_user_settings(gh, cfg="global.cfg"):
    """Get the contents of a file from the Settings folder in the user's
workspace on Github."""
    ws = get_workspace(gh)
    try:
        c = ws.get_contents("Settings/%s" % (cfg))
    except (UnknownObjectException):
        return None
    return c.decoded_content

def set_user_settings(gh, cfg=None, new_content=None, message=None, create=True):
    if cfg and new_content:
        ws = get_workspace(gh)
        path = "/Settings/%s" % (cfg)
        try:
            sha = ws.get_contents(path).sha
        except (UnknownObjectException):
            # the file does not exist.  Create if instructed so
            if not message:
                message="Created %s." % (cfg)
            ret=ws.create_file(path=path, content=new_content, message=message)
        if not message:
            message="Updated %s." % (cfg)
        ret = ws.update_file(path=path, content=new_content, message=message, sha=sha)
    else:
        ret = "File and/or content not given."
    return ret

def fork_text(gh, text, source="kanripo"):
    """Fork a text to the users account. If no source is given, use
@kanripo. 'gh' is an authenticated Github object."""
    ghuser = gh.get_user()
    try:
        repo = ghuser.get_repo(text)
    except (UnknownObjectException):
        try:
            repo = ghuser.create_fork(gh.get_repo("%s/%s" % (source, text)))
        except (UnknownObjectException):
            repo = None
    return repo

def create_branch(gh, text=None, new_branch=None, source_branch='master'):
    if text and newbranch:
        ghuser = gh.get_user()
        repo = ghuser.get_repo(text)
        sb = repo.get_branch(source_branch)
        ret=repo.create_git_ref(ref='refs/heads/' + new_branch, sha=sb.commit.sha)
    else:
        ret = None
    return ret

def save_text(gh, text_file, new_content, branch='master', message=None):
    """Save (commit) a new version of a text. The file that is to be
updated is given as 'text_file', the new content of the file a
'new_content'. If no branch is given, update 'master'."""
    text = text_file.split("_")[0]
    path = "%s/%s" % (text, text_file)
    ghuser = gh.get_user()
    repo = ghuser.get_repo(text)
    sb = repo.get_branch(branch)
    sha = repo.get_contents(path, ref=branch).sha
    if not message:
        message = "Updating %s." % (text_file)
    ret=repo.update_file(path=path, content=new_content, message=message, sha=sha, branch=branch)
    return ret

# or maybe use this?
def krp_login(token):
    global gh
    if not gh:
        gh = Github(token)
    return gh
