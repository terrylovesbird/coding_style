from requests.models import ConnectionError
from mac_networking import MacToNetconfig
from flask import Flask, jsonify, abort
import os


app = Flask(__name__)

@app.route('/netconfig/api/v1/<mac_ticket>/default-gateway/<default_gateway>')
def get_hostname_netconfig(mac_ticket, default_gateway):
    try:
        my_mac_netconfig = MacToNetconfig(mac_ticket, default_gateway)
        hostname = my_mac_netconfig.get_hostname()
        netconfig = my_mac_netconfig.get_netconfig()
        return jsonify({hostname: netconfig})
    except (LookupError, ValueError):
        abort(404)
    except (ConnectionError):
        abort(502)
    except Exception:
        abort(500)


@app.errorhandler(404)
def page_not_found(error):
    return 'Error 404, check the URL format and info correctness', 404

@app.errorhandler(500)
def internal_server_error(error):
    return 'Error 500, something going wrong on server side or jira API or querying DB', 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
