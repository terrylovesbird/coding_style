import pandas as pd
import sys
import cx_Oracle
import requests
import os
from sqlalchemy import create_engine
import ipaddress
from IPy import IP

class MacToNetconfig():
    def __init__(self, mac_ticket, default_gateway):
        self.mac_ticket = mac_ticket
        self.default_gateway = default_gateway
        self.netconfig_data = {'idrac_dhcp': '', 'netconfig': {'interfaces': {}}}
        self.jira_id = ''
        self.hostname = ''
        self.query_result = None
        self.nic_or_trunk_rows = []

    def get_hostname(self):
        if self.hostname == '':
            self._get_Jira_data()
        return self.hostname

    def get_netconfig(self):
        if len(self.netconfig_data['netconfig']['interfaces']) == 0:
            self.set_netconfig()
        return self.netconfig_data

    def _get_Jira_data(self):
        url = 'https://jira....?jql=issue={id}'.format(
            id=self.mac_ticket)
        headers = {"Content-Type": "application/json"}
        response = requests.get(url, headers=headers, auth=(
            '...', '...'))   
        self._check_response_status_code(response)
        data = response.json()
        issues = data['issues']
        self.jira_id = issues[0]['id']
        self.hostname = issues[0]['fields']['...']
        
     def _check_response_status_code(self, response):
        if(response.status_code) == 400:
            raise ValueError('Error 400, Bad request, check URL correctness')
        if(response.status_code) == 401:
            raise Exception('Error 401, Unauthorized, check request info')
        else:
            response.raise_for_status()
            
     def _query_db(self):
        dialect = 'oracle'
        sql_driver = 'cx_oracle'
        username = os.environ.get("ORACLE_USERNAME")
        password = os.environ.get("ORACLE_PASSWORD")
        host = os.environ.get("ORACLE_HOST")
        port = os.environ.get("ORACLE_PORT")
        service = os.environ.get("ORACLE_SERVICE")
        engine_path_with_auth = dialect + '+' + sql_driver + '://' + username + ':' + \
            password + '@' + host + ':' + \
            str(port) + '/?service_name=' + service
        engine = create_engine(engine_path_with_auth)

        pd.set_option('display.max_columns', 30)
        pd.set_option('display.min_rows', 20)
        pd.set_option('display.max_rows', 20)

        self._get_Jira_data()  
        self.query_result = pd.read_sql_query(
            "SELECT * FROM ... WHERE issueid={id}".format(id=self.jira_id), engine)
            
     def _ILO_ip_is_dhcp(self):
        if self.query_result.query('connection_type.str.lower() == "ilo"').get('ip_address').tail(1).item().lower() == 'dhcp':
            return True
     
     def _update_interface_netconfig_with_ip_netmask(self, interface_netconfig, interface_db_row):
        interface_netconfig[interface_db_row['connection_name']].update({'bootproto': 'static',
                                                                   'addr': interface_db_row['ip_address'],
                                                                   'netmask': interface_db_row['netmask']
                                                                  })
        return interface_netconfig
        
     def _get_config_NIC(self):
        self._get_nic_or_trunk_rows('nic')
        for nic in self.nic_or_trunk_rows:
            interface_netconfig = {nic['connection_name']:
                                   {
                                    'type': 'access',
                                    'bootproto': 'dhcp',
                                    'onboot': 'yes'
                                   }
                                  }
            if nic['ip_address'] == 'dhcp':
                self.netconfig_data['netconfig']['interfaces'].update(
                    interface_netconfig
                )

            elif nic['ip_address'] != 'none':
                self._update_interface_netconfig_with_ip_netmask(
                    interface_netconfig, nic)

                if self.default_gateway == nic['connection_name']:
                    interface_netconfig[nic['connection_name']].update(
                        {'gateway': nic['gateway']})
                self.netconfig_data['netconfig']['interfaces'].update(
                    interface_netconfig)
            else: 
                raise Exception("NIC interface {} with 'none' as the IP address".format(nic['connection_name']))
            
            
            
