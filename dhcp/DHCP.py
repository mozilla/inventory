class DHCP:
    def __init__(self, scope_options, hosts):
        self.id = id
        self.scope_options = scope_options
        self.hosts = hosts
        self.header_text = '' 
        self.footer_text = ''
        self.notes_text = ''
        self.pool_text = ''
        self.options_text = ''
        self.host_text = ''

    def header(self):
        if 'network_block' not in self.scope_options:
            self.scope_options['network_block'] = ''
            
        self.header_text = 'subnet ' + self.scope_options['network_block'] + ' netmask ' + self.scope_options['subnet_mask'] + ' {\n'
        return '%s' % self.header_text

    def footer(self):
        self.footer = '\n\n\n}'
        return self.footer 

    def pool(self):
        self.pool_text = "\tpool {\n"
        if 'pool_deny_dynamic_bootp_agents' in self.scope_options:
            self.pool_text += "deny dynamic bootp clients;\n"

        if 'pool_range_start' in self.scope_options and 'pool_range_end' in self.scope_options:
	
            self.pool_text += "range " + self.scope_options['pool_range_start'] + " " + self.scope_options['pool_range_end'] + ";\n"
        self.pool_text += 'failover peer "dhcp-failover";\n'
        self.pool_text += "}\n"
        
        return self.pool_text

    def options(self):
        if 'option_ntp_servers' in self.scope_options:
            self.options_text = 'option ntp-servers ' + self.scope_options['option_ntp_servers'] + ";\n"
        if 'option_subnet_mask' in self.scope_options:
            self.options_text += 'option subnet-mask ' + self.scope_options['option_subnet_mask'] + ";\n"
        if 'option_domain_name' in self.scope_options:
            self.options_text += 'option domain-name "' + self.scope_options['option_domain_name'] + "\";\n"
        if 'option_domain_name_servers' in self.scope_options:
            self.options_text += 'option domain-name-servers ' + self.scope_options['option_domain_name_servers'] + ";\n"
        if 'option_routers' in self.scope_options:
            self.options_text += 'option routers ' + self.scope_options['option_routers'] + ";\n"
        if 'option_subnet_mask' in self.scope_options:
            self.options_text += 'option subnet-mask ' + self.scope_options['option_subnet_mask'] + ";\n"
        if 'filename' in self.scope_options:
            self.options_text += 'filename "' + self.scope_options['filename'] + "\";\n"
        if 'allow_booting' not in self.scope_options:
            self.scope_options['allow_booting'] = 0
        if 'allow_bootp' not in self.scope_options:
            self.scope_options['allow_bootp'] = 0
        if int(self.scope_options['allow_booting']) > 0:
            self.options_text += "allow booting;\n"
        if int(self.scope_options['allow_bootp']) > 0:
            self.options_text += "allow bootp;\n"

        return self.options_text

    def get_hosts(self):
        self.host_text = "\n"
        for arr in self.hosts:
            for host in arr:
                if 'system_hostname' in host and 'adapter_name' in host:
                    self.host_text += "\nhost " + host['system_hostname'].strip() + "-" + host['adapter_name'].strip() + "  {\n"
                if 'mac_address' in host:
                    self.host_text +=  "\thardware ethernet " + host['mac_address'] + ";\n" 
                if 'ipv4_address' in host:
                    self.host_text +=  "\tfixed-address " + host['ipv4_address'] + ";\n" 
                if 'dhcp_filename' in host and host['dhcp_filename'] > '':
                    self.host_text +=  "\tfilename \"" + host['dhcp_filename'] + "\";\n" 
                if 'dhcp_hostname' in host and host['dhcp_hostname'] > '':
                    self.host_text +=  "\toption host-name \"" + host['dhcp_hostname'] + "\";\n" 
                if 'dhcp_domain_name' in host and host['dhcp_domain_name'] > '':
                    self.host_text +=  '\toption domain-name "' + host['dhcp_domain_name'] + '";\n '
                if 'dhcp_domain_name_servers' in host and host['dhcp_domain_name_servers'] != '':
                    self.host_text += '\toption domain-name-servers ' + host['dhcp_domain_name_servers'] + ";\n"
                self.host_text += "}"
        try:
            self.host_text += self.scope_options['overrides']
        except:
            pass
        return self.host_text

    def notes(self):
        self.notes_text = "##\n"
        if self.scope_options['notes'] is not None:
            for line in self.scope_options['notes'].split("\n"):
                self.notes_text += "## " + line + "\n"
            self.notes_text += "##\n"
        else:
            self.notes_text = ''

        return self.notes_text
