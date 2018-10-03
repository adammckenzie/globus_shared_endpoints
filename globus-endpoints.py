import argparse
import csv
import globus_sdk
import yaml
from tabulate import tabulate

# The Globus SDK needs to be installed first: https://globus-sdk-python.readthedocs.io/en/stable/installation/
# short answer: pip install globus-sdk

# Also needs tabulate
# pip install tabulate

class Endpoint:
    display_name = "Unset"
    id = "Unset"
    owner_string = "Unset"
    shared_endpoint = "Unset"
    share_path = "Unset"
    host_endpoint = "Unset"

def get_shared_endpoints_from_endpoint(tc, endpoint_id):
    return tc.endpoint_manager_hosted_endpoint_list(endpoint_id)

def get_endpoints(tc):
    return tc.endpoint_manager_monitored_endpoints()

def get_shared_endpoints(endpoints, tc):
    shared_endpoints = []
    for endpoint in endpoints:
        shared_endpoints.extend(get_shared_endpoints_from_endpoint(tc, endpoint["id"]))
    return shared_endpoints

def get_transfer_client(client_id, transfer_rt, transfer_at, expires_at_s):
    client = globus_sdk.NativeAppAuthClient(client_id)
    client.oauth2_start_flow(refresh_tokens=True)
    authorizer = globus_sdk.RefreshTokenAuthorizer(
        transfer_rt, client, access_token=transfer_at, expires_at=int(expires_at_s))
    tc = globus_sdk.TransferClient(authorizer=authorizer)
    return tc

def endpoint_as_array(endpoint):
    return [endpoint.display_name, endpoint.id, endpoint.owner_string, endpoint.shared_endpoint, endpoint.host_endpoint, endpoint.share_path]

def get_endpoint_headings():
    return ['Endpoint Name', 'Endpoint Id', 'Owner String', 'Shared Endpoint', 'Host Endpoint', 'Share Path']

def safe_encode(input_string):
    if input_string == None:
        return ''
    return input_string.encode('ascii', 'ignore')

def get_endpoint(input_json, is_shared_endpoint):
    new_endpoint = Endpoint()
    new_endpoint.display_name = safe_encode(input_json["display_name"])
    if (not new_endpoint.display_name):
        new_endpoint.display_name = safe_encode(input_json["host_endpoint_display_name"])
    if (not new_endpoint.display_name):
        new_endpoint.display_name = safe_encode(input_json["canonical_name"])
    new_endpoint.id = safe_encode(input_json["id"])
    new_endpoint.owner_string = safe_encode(input_json["owner_string"])
    if not is_shared_endpoint:
        new_endpoint.shared_endpoint = False
        new_endpoint.host_endpoint = 'n/a'
        new_endpoint.share_path = 'n/a'
    else:
        new_endpoint.shared_endpoint = True
        new_endpoint.host_endpoint = safe_encode(input_json["host_endpoint"])
        new_endpoint.share_path = safe_encode(input_json["sharing_target_root_path"])
    return new_endpoint

def main():
    parser = argparse.ArgumentParser(description='A script for gathering information about the hosted endpoints and shared endpoints')
    parser.add_argument('-c', '--config', default="config.yaml", help='Specify a configuration file. config.yaml is the default.')
    parser.add_argument('-e', '--endpoints', default=True, type=bool, help="Include normal endpoints in results.")
    parser.add_argument('-s', '--shared-endpoints', default=True, type=bool, help="Include shared endpoints in results.")
    parser.add_argument('-t', '--table', default=True, type=bool, help="Show endpoints and shared endpoints as a table")
    parser.add_argument('--csv', default="globus_endpoints.csv", help="Create a CSV file at the given location with the endpoints and/or shared endpoints")
    args = parser.parse_args()

    with open(args.config, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit(1)

    client_id = config[0]["auth"]["client_id"]
    refresh_token = config[0]["auth"]["refresh_token"]
    active_token = config[0]["auth"]["active_token"]
    token_expires = config[0]["auth"]["token_expires"]
    tc = get_transfer_client(client_id, refresh_token, active_token, token_expires)
    if (args.endpoints):
        endpoints = get_endpoints(tc)["DATA"]
    else:
        endpoints = config[1]["endpoints"]

    if (args.shared_endpoints):
        shared_endpoints = get_shared_endpoints(endpoints, tc)

    all_endpoints = []
    for endpoint in endpoints:
        all_endpoints.append(get_endpoint(endpoint, False))

    if (args.shared_endpoints):
        for shared_endpoint in shared_endpoints:
            all_endpoints.append(get_endpoint(shared_endpoint, True))

    if (args.csv):
        with open(args.csv, 'w') as csvfile:
            cvswriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            cvswriter.writerow(get_endpoint_headings())
            for endpoint in all_endpoints:
                cvswriter.writerow(endpoint_as_array(endpoint))

    if (args.table):
        endpoints_array = []
        for endpoint in all_endpoints:
            endpoints_array.append(endpoint_as_array(endpoint))
        print str(tabulate(endpoints_array, headers=get_endpoint_headings()))

if __name__ == "__main__":
        main()


