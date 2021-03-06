import os
import json
import hashlib
import logging
import subprocess
import platform
import eve_mlp.aes as aes


__version__ = "0.1.1"


config_path = os.path.expanduser("~/.config/eve-mlp.conf")
log = logging.getLogger(__name__)
EULA_URL = "http://community.eveonline.com/support/policies/eve-eula/"


def load_config():
    config = {
        "usernames": [],
        "passwords": {},
        "extra": {},
    }
    try:
        config.update(json.loads(file(config_path).read()))
    except:
        log.debug("Couldn't load config file:", exc_info=True)
    return config


def save_config(config):
    try:
        config_dir = os.path.dirname(config_path)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        file(config_path, "w").write(json.dumps(config, indent=4))
    except:
        log.debug("Couldn't save config file:", exc_info=True)


def encrypt(cleartext, key):
    moo = aes.AESModeOfOperation()

    cypherkey = [ord(x) for x in hashlib.md5(key).digest()]
    iv = [ord(x) for x in os.urandom(16)]

    mode, orig_len, ciph = moo.encrypt(cleartext, moo.modeOfOperation["CBC"], cypherkey, moo.aes.keySize["SIZE_128"], iv)
    return json.dumps([mode, orig_len, ciph, iv]).replace(" ", "")


def decrypt(data, key):
    try:
        moo = aes.AESModeOfOperation()

        cypherkey = [ord(x) for x in hashlib.md5(key).digest()]
        mode, orig_len, ciph, iv = json.loads(data)

        cleartext = moo.decrypt(ciph, orig_len, mode, cypherkey, moo.aes.keySize["SIZE_128"], iv)
        return cleartext
    except Exception as e:
        log.error("Error decrypting password: %s", e)
        return None


def launch(launch_token, args, extra=[]):
    log.info("Launching eve")
    cmd = []

    # platform specific pre-binary bits
    if args.dry:
        cmd.append("echo")

    for i in extra[:-1]:
      cmd.append(i)
    if platform.system() == "Linux" and len(extra) == 0:
        cmd.append("wine")

    # run the app
    # wrap it with "" to account for spaces in path
    if (len(extra) == 0):
      cmd.append("\"" + os.path.join("bin", "ExeFile.exe"))
    else:
      cmd.append("\"" + os.path.join(extra[-1],"bin","ExeFile.exe") + "\"")
    cmd.append("/ssoToken=" + launch_token)
    cmd.append("/noconsole")

    # app flags
    if args.singularity:
        cmd.append("/server:Singularity")

    # go!
    print " ".join(cmd)
    return subprocess.Popen(" ".join(cmd), shell=True)
