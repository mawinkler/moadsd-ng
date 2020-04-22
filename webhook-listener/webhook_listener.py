import hmac
import logging
from json import dumps
from os import X_OK, access, getenv, listdir
from os.path import join
from pathlib import Path
from subprocess import PIPE, Popen
from sys import stderr, exit
from traceback import print_exc

from flask import Flask, abort, request


def get_secret(name):
    """Tries to read Docker secret or corresponding environment variable.

    Returns:
        secret (str): Secret value.

    """
    secret_path = Path('/run/secrets/') / name

    try:
        with open(secret_path, 'r') as file_descriptor:
            return file_descriptor.read() \
                    .strip()
    except OSError as err:
        variable_name = name.upper()
        logging.debug(
            'Can\'t obtain secret %s via %s path. Will use %s environment variable.',
            name,
            secret_path,
            variable_name
        )
        return getenv(variable_name)


logging.basicConfig(stream=stderr, level=logging.INFO)

# Collect all scripts now; we don't need to search every time
# Allow the user to override where the hooks are stored
HOOKS_DIR = getenv("WEBHOOK_HOOKS_DIR", "/app/hooks")
scripts = [join(HOOKS_DIR, f) for f in listdir(HOOKS_DIR)]
scripts = [f for f in scripts if access(f, X_OK)]
if not scripts:
    logging.error("No executable hook scripts found; did you forget to"
                  " mount something into %s or chmod +x them?", HOOKS_DIR)
    exit(1)

# Get application secret
webhook_secret = get_secret('webhook_secret')
if webhook_secret is None:
    logging.error("Must define WEBHOOK_SECRET")
    exit(1)

# Our Flask application
application = Flask(__name__)

# Keep the logs of the last execution around
responses = {}

@application.route('/', methods=['POST'])
def index():
    global webhook_secret, branch_whitelist, scripts, responses

    # # Get signature from the webhook request
    # header_signature = request.headers.get('X-Scan-Event-Signature')
    # if header_signature is None:
    #     logging.info("X-Scan-Event-Signature was missing, aborting")
    #     abort(403)
    #
    # # Construct an hmac, abort if it doesn't match
    # try:
    #     sha_name, signature = header_signature.split('=')
    # except:
    #     logging.info("X-Scan-Event-Signature format is incorrect (%s), aborting", header_signature)
    #     abort(400)
    # data = request.get_data()
    # try:
    #     mac = hmac.new(webhook_secret.encode('utf8'), msg=data, digestmod=sha_name)
    # except:
    #     logging.info("Unsupported X-Scan-Event-Signature type (%s), aborting", header_signature)
    #     abort(400)
    # if not hmac.compare_digest(str(mac.hexdigest()), str(signature)):
    #     logging.info("Signature did not match (%s and %s), aborting", str(mac.hexdigest()), str(signature))
    #     abort(403)

    # # Respond to ping properly
    # event = request.headers.get("X-Scan-Event", "ping")
    # if event == "ping":
    #     return dumps({"msg": "pong"})

    logging.info(request.get_json(force=True))
    useragent = request.headers.get("User-Agent")
    logging.info("User-Agent: " + useragent)
    if useragent != "DeepSecuritySmartCheck":
        return dumps({"msg": "pong"})

    # We're only interested in scan-completed events
    event = request.get_json(force=True)["event"]
    logging.info("Event: " + event)
    if event != "scan-completed":
        logging.info("Ignoring Event")
        return dumps({"msg": "pong"})

    # We only want clean images
    status = request.get_json(force=True)["scan"]["status"]
    logging.info("Status: " + status)
    #if status != "completed-no-findings":
    #    logging.info("Ignoring Image because of Findings")
    #    return dumps({"msg": "pong"})

    # Run scripts, saving into responses (which we clear out)
    responses = {}
    image_name = request.get_json(force=True)["scan"]["name"]
    scan_id = request.get_json(force=True)["scan"]["href"]
    logging.info("running scripts")
    for script in scripts:
        logging.info("running: " + str(script))
        proc = Popen([script, image_name, scan_id], stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        stdout = stdout.decode('utf-8')
        stderr = stderr.decode('utf-8')

        # Log errors if a hook failed
        if proc.returncode != 0:
            logging.error('[%s]: %d\n%s', script, proc.returncode, stderr)

        responses[script] = {
            'stdout': stdout,
            'stderr': stderr
        }
    logging.info("responses: " + responses)

    return dumps(responses)

@application.route('/logs', methods=['GET'])
def logs():
    return dumps(responses)


# Run the application if we're run as a script
if __name__ == '__main__':
    logging.info("All systems operational, beginning application loop")
    application.run(debug=True, host='0.0.0.0', port=8000)
