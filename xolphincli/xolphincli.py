# Xolphin API wrapper
#
# (c) 2016, Nuno Tavares <nuno.tavares@synrix.com>

import xolphin
import signal
import datetime
from prettytable import PrettyTable
from operator import itemgetter
import sys

class XolphinCLI(object):
    _client = None
    _username = None
    _password = None
    DEBUG = 0

    _approver_first_name = None
    _approver_last_name = None
    _approver_phone = None
    _approver_email = None

    def __init__(self, debug, username, password, usetest=False):
        self.DEBUG = debug
        self._username = username
        self._password = password
        self._client = xolphin.Client(username, password)
        if usetest:
            self._client.BASE_URL = 'https://test-api.xolphin.com/v1/';
        self.debug(2, '# Using the following API: ' + self._client.BASE_URL)
        if self.DEBUG == 0:
            signal.signal(signal.SIGINT, self.catch_ctrl_C)

    def loadApproverDetails(self, details):
        self._approver_first_name = details['firstName']
        self._approver_last_name = details['lastName']
        self._approver_phone = details['phone']
        self._approver_email = details['email']
        self._approver_address = details['address']
        self._approver_zipcode = details['zipcode']

    def debug(self, level, args):
        if self.DEBUG>=level:
            print args

    # Handle unwanted CTRL+C presses
    def catch_ctrl_C(self, sig, frame):
        print "Warning: do not interupt! If you really want to quit, use kill -9."

    def getCertificateById(self, certid):
        certificates = self._client.certificate().all()
        for certificate in certificates:
            if str(certificate.id) == str(certid):
                return certificate
        return None

    def listCertificates(self, format='sections'):
        certificates = self._client.certificate().all()

        sections = {}
        for certificate in certificates:
            if ( not certificate.isExpired() ):
                #print "%d %s [%s %s (%d)] - %s" % (certificate.id, certificate.domain_name, certificate.product.brand, certificate.product.name, certificate.product.id, datetime.datetime.strftime(certificate.date_expired, '%Y-%m-%d'))
                revstr = certificate.domain_name[::-1].split('.')
                if format == 'sections':
                    section = (revstr[0] + '.' + revstr[1])[::-1]
                else:
                    section = ''
                #print " + section = %s" % section
                if section not in sections:
                    sections[section] = []
                sections[section] = sections[section] + [ certificate ]

        for section, certs in sections.iteritems():
            print "\n" + section
            sectiontbl = PrettyTable(["#", "Domain", "Product (#)", "ExpireDate"])
            for cert in certs:
                #print "\t%d %s [%s %s (%d)] - %s" % (cert.id, cert.domain_name, cert.product.brand, cert.product.name, cert.product.id, datetime.datetime.strftime(cert.date_expired, '%Y-%m-%d'))
                sectiontbl.add_row([ str(cert.id), cert.domain_name, cert.product.brand + ' ' + cert.product.name + ' (' + str(cert.product.id) + ')', datetime.datetime.strftime(cert.date_expired, '%Y-%m-%d')])
            print sectiontbl

    def listRequests(self):
        requests = self._client.request().all()
        results = PrettyTable(["ID", "Company + Product (pId)", "Domain"])
        for request in requests:
            results.add_row([ str(request.id), request.product.brand + ' ' + request.product.name + ' (' + str(request.product.id) + ')', request.domain_name ])
        print results



    def decodeCSR(self, csrText):
        self.debug(2, 'CSR: ' + csrText)
        data = self._client.support().decode_csr(csrText)

        results = PrettyTable(["Key Type", "Company", "CN", "State", "City", "Country", "altName(s)"])
        altnames = []
        data.altNamesList = []
        if data.altNames:
            if isinstance(data.altNames, dict):
               for an in data.altNames.values():
                   altnames = altnames + [ an['dNSName'] ]
                   data.altNamesList = data.altNamesList + [ an['dNSName'] ]
        results.add_row([ data.type + ' ' + str(data.size), data.company, data.cn, data.state, data.city, data.country, ','.join(altnames) ])
        print results
        return data


    def listProducts(self, sort=True):
        products = self._client.support().products()
        results = PrettyTable(["ID", "Company + Product"])

        for product in products:
            results.add_row([ str(product.id), product.brand + ' ' + product.name + ' (' + product.type + ', ' + product.validation + ') ' ])

        if sort:
            print results.get_string(sort_key=lambda x: int(x[0]), sortby="ID")
        else:
            print results

    def downloadCertificate(self, certId, compatMode = False):
        cert = self.getCertificateById(certId)
        if not cert:
            print "ERROR: Could not find certificate with id=" + certId
            sys.exit(4)

        self.debug(2, ' + Downloading cert...')
        certtext = self._client.certificate().download(certId, 'CRT')
        self.debug(2, ' + Downloading ca-bundle...')
        catext = self._client.certificate().download(certId, 'CA_Bundle')
        if compatMode:
            filename = cert.domain_name.replace('.', '_')
        else:
            filename = cert.domain_name

        with open(filename + '.crt', 'wb') as f:
            f.write(certtext)
        with open(filename + '.ca-bundle', 'wb') as f:
            f.write(catext)
        self.debug(2, ' + Also generating nginx .PEM...')
        with open(filename + '.pem', 'wb') as f:
            f.write(certtext)
            f.write(catext)


    def requestCertificate(self, csrText, productId, years, domain, subjAltNames):
        ccr = self._client.request().create(productId, years, csrText, 'EMAIL')

        csr = self.decodeCSR(csrText)

        ccr.approver_first_name = self._approver_first_name
        ccr.approver_last_name = self._approver_last_name
        ccr.approver_phone = self._approver_phone
        ccr.approver_email = self._approver_email
        ccr.address = self._approver_address
        ccr.zipcode = self._approver_zipcode
        ccr.city = csr.city
        ccr.company = csr.company
        ccr.state = csr.state
        ccr.country = csr.country
        if productId in [ 24 ]:
            # These products require Domain Control Validation
            ccr.dcv.append({
                'domain': domain,
                'dcvType': 'DNS',
                'approverEmail': self._approver_email
            })
        else:
            ccr.dcv.append({
                'domain': domain,
                'dcvType': 'EMAIL',
                'approverEmail': self._approver_email
            })
        if subjAltNames:
            for san in subjAltNames.split(','):
                ccr.subject_alternative_names.append(san)

        request = self._client.request().send(ccr)
        print "New request placed with ID = " + str(request.id)
