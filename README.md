# Xolphin CLI

This is a CLI tool to request certificates from [Xolphin.com](https://www.xolphin.com/). You can use this tool any machine that reaches [Xolphin API](https://api.xolphin.com/) endpoints.

Before proceeding, you'll have to:
* Place a file credentials.secret with your Xolphin customer credentials, in the format username:password
* Edit approverdetails.yml with your personal data.
* Install python modules: sudo pip install setuptools prettytable xolphin-api pyaml

Normal flow for this script:
```bash
# list available products, to obtain product ids
./xolphin-cli -p

# perform the request
./xolphin-cli --request -y <years> -p <product id> -d <domain> --csr <csrfile> -a <e.g. www.domain>

# check the request is pending, if it's a simple certificate you should get an e-mail to validate it,
# otherwise if it's an EV, the process is a bit more complicated.
./xolphin-cli -r

# when certificate disappears from the "requests list", it should be available in the
# "available certificates list". Get its id from the list
./xolphin-cli -l

# Now you can just download it.
./xolphin-cli --download <certificate id>
```

References
==========
* https://api.xolphin.com/support/REST/Xolphin_API_wrapper_for_Python
* https://api.xolphin.com/docs/v1
