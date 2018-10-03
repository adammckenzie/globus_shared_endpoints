import globus_sdk
import yaml

with open("config.yaml", 'r') as stream:
    try:
        config = yaml.safe_load(stream)
        print(config)
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit(1)

client_id = config[0]["auth"]["client_id"]
print(client_id)

client = globus_sdk.NativeAppAuthClient(client_id)
client.oauth2_start_flow(refresh_tokens=True)

print('Please go to this URL and login: {0}'
              .format(client.oauth2_get_authorize_url()))

get_input = getattr(__builtins__, 'raw_input', input)
auth_code = get_input('Please enter the code here: ').strip()
token_response = client.oauth2_exchange_code_for_tokens(auth_code)

# let's get stuff for the Globus Transfer service
globus_transfer_data = token_response.by_resource_server['transfer.api.globus.org']
# the refresh token and access token, often abbr. as RT and AT
transfer_rt = globus_transfer_data['refresh_token']
transfer_at = globus_transfer_data['access_token']
expires_at_s = globus_transfer_data['expires_at_seconds']

print("refresh_token: '" + str(transfer_rt) + "'")
print("active_token: '" + str(transfer_at) + "'")
print("token_expires '" + str(expires_at_s) + "'")
