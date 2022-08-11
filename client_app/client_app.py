import requests, argparse
from ruamel.yaml import YAML



def get_args():
    parser = ThrowingArgumentParser()
    parser.add_argument("mac_ticket_and_default_gateway", nargs="+",
                        help="MAC ticket number and default gateway interface comma-delimited (e.g. ...,...)")
    args = parser.parse_args()
    return args

# subclass ArgumentParser and override the error method to do something different when an error occurs
class ThrowingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        message = "MAC ticket number and default gateway interface comma-delimited (e.g. ...,...)"
        raise ArgumentParserError(message)

class ArgumentParserError(Exception): pass

def get_response_data(mac_ticket, default_gateway):
    response = requests.get('https://.../api/v1/{mac_ticket}/default-gateway/{default_gateway}'.format(mac_ticket = mac_ticket, default_gateway = default_gateway), allow_redirects=True)
    data = response.json()
    return data

def write_config_to_yml_file(hostname, netconfig):
    yaml = YAML()
    yaml.explicit_start = True  # ---
    with open(f'../host_vars/{hostname}.yml', 'w') as file:
        yaml.dump(netconfig, file)


if __name__ == "__main__":
    args = get_args()

    for mac_ticket_and_default_gateway in args.mac_ticket_and_default_gateway:
        try:
            mac = mac_ticket_and_default_gateway.split(',')[0]
            gw = mac_ticket_and_default_gateway.split(',')[1]
        except Exception as e:
            print(
                "make sure the mac-ticket and default-gateway are correct, also the format of input")
            raise e
    
        data = get_response_data(mac, gw)
        hostname = list(data.keys())[0]
        netconfig = list(data.values())[0]

        write_config_to_yml_file(hostname, netconfig)
