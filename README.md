# retrieve_hostname_netconfig

This app exists to eliminate the manual, error-prone copy/paste from the MAC network grid into a `netconfig` data structure in host_vars in ansible-infra. The app can be run several ways, but the most convenient way to consume it would be to hit the instance of the app currently running in Rancher.

## How it works
1. Given a `MAC ticket number`, retrieve the unique `ID of the ticket(ISSUEID)` through jira API
1. Using this id from Jira, query the related network grid info like `IP address` from the NSR database
1. Compute a valid `netconfig` data structure for the server
1. Write out the computed `netconfig` and `idrac_dhcp` vars as an ansible host_vars file

## Using the app

The app can be reached in Rancher at https://hostname-netconfig... This will give you a 404 for failing to provide a full, valid URL to request data. The URL structure is:

`https://hostname-netconfig.../netconfig/api/v1/<MAC-ticket>/default-gateway/<gateway-interface>`

For example:

`https://hostname-netconfig.../netconfig/api/v1/MACV3-16134/default-gateway/em2.2222`

You can hit this with `curl`, or you can use the included client app that will hit a properly formatted URL for you. For example:

```
cd client_app
virtualenv -p python3 client_app_venv
source client_app_venv/bin/activate
pip install -r requirements.txt

# NOTE: mac-ticket and default-gateway should be comma-delimited (with NO space)
./client_app.py MACV3-3713,em1

# or specify multiple MACs
./client_app.py MACV3-3713,em1 MACV3-12965,em1 MACV3-15469,p3p1.124

# A .yml file will be generated for each MAC/host in `client_app/host_vars`
```

## Alternate ways to run the app
(Pre-request: ask project related engineers or manager for the credentials like Oracle_Username and manually replace them in /src/mac_networking.py)
### Run the flask app locally

You'd run the app like this before deploying updated code to Rancher. Note that for this to work, you'll need a working local install of the Oracle Instant Client.

```bash
virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt
cd src
./app.py
```

Then, you can hit the locally-running version of the api with `curl` as follows to get JSON:

```
tcai@sample:~/git/retrieve_hostname_netconfig/src$ curl -s http://localhost:5000/netconfig/api/v1/MACV3-3713/default-gateway/em1 | jq .
{
  "abcd-machine04": {
    "idrac_dhcp": "yes",
    "netconfig": {
      "interfaces": {
        "em1": {
          "bootproto": "dhcp",
          "onboot": "yes",
          "type": "access"
        }
      }
    }
  }
}
tcai@sample:~/git/retrieve_hostname_netconfig/src$ 
```

### Run the app directly (not as a flask app)

```bash
virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt
cd src

# NOTE: mac-ticket and default-gateway should be comma-delimited (with NO space)
./create_host_vars.py MACV3-3713,em1
./create_host_vars.py MACV3-3713,em1 MACV3-12965,em1 MACV3-15469,p3p1.124

# The .yml file(s) will be created in the current directory
```

## How to update app running in Rancher
(Only necessary if you update code in the `requirement.txt` in the root or the code in `/src` or the Dockerfile)
1. Code and locally test python code updates
1. Build updated docker image: `docker image build -t harbor.../unix/hostname-netconfig .`
1. (optional) Run the image as a container: `docker run -dp 5000:5000 harbor.../unix/hostname-netconfig`
1. Push the image to harbor..., `docker push harbor.../unix/hostname-netconfig:v0.2`
1. Update manifests in `k8s` directory as needed (likely only the `deployment.yaml` with `kubectl`)
1. Apply any modified manifests (e.g. `kubectl apply k8s/deployment.yaml -n hostname-netconfig`)
1. NOTE: The `hostname-netconfig` namespace under `Unix Operations` project in Rancher has already been created for this app. Additionally, via the Rancher UI, we've created secrets for the robot account to use when pulling the container image from harbor (secret named `harbor`) and the private key and certificate files to use with the ingress (secret named `unix-...`).
