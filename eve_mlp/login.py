import requests
from urlparse import urljoin
import re
import logging
import common

log = logging.getLogger(__name__)


LAUNCHER_INFO = 'http://client.eveonline.com/patches/win_launcherinfoTQ_inc.txt'


class LoginFailed(Exception):
    pass


def do_login(username, password):
    log.debug("Using cached SSO login URL")
    #login_action_url = get_login_action_url(LAUNCHER_INFO)
    login_action_url = "https://login.eveonline.com/Account/LogOn?" + \
        "ReturnUrl=%2Foauth%2Fauthorize%2F%3Fclient_id%3DeveLauncherTQ%26lang%3Den%26response_type%3Dtoken%26" + \
        "redirect_uri%3Dhttps%3A%2F%2Flogin.eveonline.com%2Flauncher%3Fclient_id%3DeveLauncherTQ%26scope%3DeveClientToken"

    access_token = submit_login(login_action_url, username, password)
    launch_token = get_launch_token(access_token)

    return launch_token


def get_login_action_url(launcher_url):
    from bs4 import BeautifulSoup
    import yaml

    # get general info
    launcher_info = yaml.load(requests.get(launcher_url))
    landing_url = launcher_info["UISettings"]["LandingPage"]
    landing_url = urljoin(launcher_url, landing_url)

    # load main launcher page
    landing_page = BeautifulSoup(requests.get(landing_url))
    login_url = landing_page.find(id="sso-frame").get("src")
    login_url = urljoin(landing_url, login_url)

    # load login frame
    login_page = BeautifulSoup(requests.get(login_url))
    action_url = login_page.find(name="form").get("action")
    action_url = urljoin(login_url, action_url)

    return action_url

def query_user(args):
  return raw_input(args);

def submit_login(action_url, username, password):
    log.info("Submitting username / password")
    session = requests.Session()

    auth_result = session.post(
        action_url,
        data={"UserName": username, "Password": password},
        verify=False,
    )

    if "<title>License Agreement Update</title>" in auth_result.text:
      print auth_result.text
      print "\n\n"
      print "EULA changed. Read it above or at: %s" % common.EULA_URL
      eula_accept = query_user("Do you acceppt the EULA (y/n)?")
      if eula_accept in ['y','Y']:
          matches3 = re.search("action=\"([^\"]+)\".*\"eulaHash\".*?value=\"([^\"]+)\".*\"returnUrl\".*?value=\"([^\"]+)\"", auth_result.text);
          if not matches3:
              raise LoginFailed("You have to accept the EULA.");
          log.debug("EULA-ACCEPT: hash: %s, return: %s" %(matches3.group(2),matches3.group(3)))
          auth_result = session.post(
            "https://login.eveonline.com"+matches3.group(1),
            data={"eulaHash": matches3.group(2), "returnUrl": matches3.group(3)},
            verify=False,
          )
      
    matches = re.search("#access_token=([^&]+)", auth_result.url)
    if not matches:
        #maybe char-challange
        matches2 = re.search("/Account/Challenge\?([^\"]*)", auth_result.text)
        if not matches2:
            print auth_result.text+"\n\n"
            raise LoginFailed("Invalid username / password?")
        else:
            char = query_user("Character Challenge for User %s. Name one Character on this Account: " % username)
            challenge_result = session.post(
                 "https://login.eveonline.com/Account/Challenge?"+matches2.group(1),
                 data={"Challenge": char},
                 verify=False,
            )
            if "<title>License Agreement Update</title>" in challenge_result.text:
                print challenge_result.text
                print "\n\n"
                print "EULA changed. Read it above or at: %s" % common.EULA_URL
                eula_accept = query_user("Do you acceppt the EULA (y/n)?")
                if eula_accept in ['y','Y']:
                    matches3 = re.search("action=\"([^\"]+)\".*\"eulaHash\".*?value=\"([^\"]+)\".*\"returnUrl\".*?value=\"([^\"]+)\"", challenge_result.text);
                    if not matches3:
                        raise LoginFailed("You have to accept the EULA.");
                    #TODO: returnUrl seems to cause problems. Maybe HTML-Encode the string (as it seems not to be the case..)
                    challenge_result = session.post(
                      "https://login.eveonline.com/"+matches3.group(1),
                      data={"eulaHash": matches3.group(2), "returnUrl": matches3.group(3)},
                      verify=False,
                    )
            matches = re.search("#access_token=([^&]+)", challenge_result.url)
            if not matches:
              raise LoginFailed("Character-Challenge not successful. Aborting.")
    return matches.group(1)


def get_launch_token(access_token):
    log.info("Fetching launch token")

    response = requests.get(
        "https://login.eveonline.com/launcher/token?accesstoken="+access_token,
        verify=False,
    )
    matches = re.search("#access_token=([^&]+)", response.url)
    if not matches:
        raise LoginFailed("No launch token?")
    return matches.group(1)
