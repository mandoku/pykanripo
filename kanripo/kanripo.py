#   -*- coding: utf-8 -*-
from __future__ import print_function
import requests
import json
import re

from github import Github
from github import UnknownObjectException

from collections import defaultdict

apiappend = ""
krp_base = "https://www.kanripo.org/"
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
    url = krp_api+"/"+querystring+apiappend
    response = apisession.get(url).text
    return response

def _get_title(textid):
    if len(titles) == 0:
        _loadtitles()
    if titles.has_key(textid):
        return titles[textid]
    else:
        return "No title"

def searchtexts(key, with_titles=False):
    res=_krpapicall("search?query="+key)
    out = []
    for line in res.split("\n"):
        l = line.split("\t", 1)
        if "_" in line:
            l0 = l[0].split(",")
            l[0] = "%s%s%s" % (l0[1], key[0], l0[0])
            if with_titles:
                title = _get_title(l[1].split("_")[0])
                out.append("\t".join((l[0], title, l[1])))
            else:
                out.append("\t".join((l[0], l[1])))
    return out

def search_multiple(keys, max_distance=100):
    res={}
    txs = defaultdict(lambda: defaultdict(list))
    found = []
    ret = []
    # search
    for key in keys:
        res[key] = searchtexts(key)
    # invert the data by text
    for k in res.keys():
        for i in range(0, len(res[k])):
            try:
                t1=res[k][i].split("\t")[1]
            except:
                print ("problem:", res[k][i])
                continue
            tx = t1.split(":")[0]
            no = int(t1.split("$")[-1])
            txs[tx][k].append((no, i))
    # find those that have the match within the required distance
    for tx in txs:
#        if len(txs[tx].keys()) >= len(keys):
        # this assumes len(keys) == 2
        if len(txs[tx].keys()) > 1:
            ks = txs[tx].items()
            # we use the key with the smallest number of hits for a loop 
            a = min(ks, key=lambda x: len(x[1]))
            for ano in a[1]:
                for b in txs[tx].keys():
                    if b != a[0]:
                        #print b, a
                        for bno in txs[tx][b]:
                            if abs(ano[0] - bno[0]) < max_distance:
                                if ano[0] < bno[0]:
                                    found.append((tx, a[0], ano, b, bno))
                                else:
                                    found.append((tx, b, bno, a[0], ano))
                                break
    for f in found:
        # now we call the lines from the results and return
        ret.append((res[f[1]][f[2][1]], res[f[3]][f[4][1]]))
    return ret

def get_result_file(location, gh=None):
    """This retrieves the textfile that matches the location. Location is a location returned from the search results or a textfile name from a KR text."""
    textfile=location.split(":")[0]
    text = textfile[0:8]
    if gh:
        ghuser = gh.get_user()
        try:
            repo = ghuser.get_repo(text)
        except (UnknownObjectException):
            repo = gh.get_repo("%s/%s" % (kanripo, text))
        try:
            c = repo.get_contents("/%s.txt" % (textfile))
        except:
            return None
        return c.decoded_content
    else:
        #TODO: get branch from variants at the end of location if available
        branch = "master"
        url=ghkrp % (kanripo, text, branch, textfile)
        #print url
        response = apisession.get(url).text
        return response
    
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

def get_or_fork_text(gh, text, source="kanripo"):
    """Get a text from the users' account. If the text does not exist,
fork the text to the users account. If no source is given, use
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
    if text and new_branch:
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
    path = "/%s" % (text_file)
    ghuser = gh.get_user()
    try:
        repo = ghuser.get_repo(text)
    except (UnknownObjectException):
        return "Text %s not found in %s account." % (text, ghuser.login)
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
