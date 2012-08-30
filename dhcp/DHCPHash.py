import re
class DHCPHash(object):
    dhcp_object_list = []
    hashed_list = []
    list_string = ""
    unformatted_string = ""
    known_options = [
            'hardware ethernet',
            'fixed-address',
            'option host-name',
            'option domain-name',
            'option domain-name-servers',
            'filename',
            ]
    def __init__(self, list_string):
        self.list_string = list_string
        unformatted_string = self.remove_formatting(self.list_string)
        dhcp_object_list = self.split_lines(unformatted_string)
        self.hashed_list = self.hash_list(dhcp_object_list)

    def get_hash(self):
        return self.hashed_list


    def remove_formatting(self, input_string):
        output_string = input_string
        output_string = output_string.replace('\n','')
        output_string = output_string.replace('\t','')
        output_string = output_string.replace('    ','')
        output_string = output_string.replace('}','}\n')
        return output_string

    def split_lines(self, input_string):
        input_string = input_string.strip()
        return input_string.split('\n')

    def hash_list(self, input_list):
        hash_list = []
        for line in input_list:
            m = re.search('^host\s+(.*)\s+{(.*)}$', line)
            if m:
                tmp = {}
                host = m.group(1)
                if '-' in host:
                    split_hostname = m.group(1).split('-')[:-1]
                    tmp['host'] = "-".join(split_hostname)
                else:
                    tmp['host'] = host


                for the_key in m.group(2).split(';'):
                    for known in self.known_options:
                        if known in the_key:
                            tmp[known] = the_key.replace(known, '').strip().strip('"').strip("'")
            hash_list.append(tmp)
        return hash_list


class DHCPHashCompare(object):

    hash1_count = 0    
    hash2_count = 0    
    hash1_hosts = []
    hash2_hosts = []
    hash1_diff = []
    hash2_diff = []
    identical = True

    def __init__(self, hash1, hash1_name, hash2, hash2_name):
        """
            taskes 2 DHCPHash objects and descriptive names and compares
            what is missing/different between the 2
        """
        self.hash1 = hash1
        self.hash2 = hash2
        self.hash1_name = hash1_name
        self.hash2_name = hash2_name
        self.hash1_count = self._get_hash_len(hash1)
        self.hash2_count = self._get_hash_len(hash2)
        self.hash1_hosts = self._get_hosts(hash1)
        self.hash2_hosts = self._get_hosts(hash2)
        identical, lists = self.compare_lists(hash1, hash2)
        if not identical:
            self.hash1_diff = lists[0]
            self.hash2_diff = lists[1]


    def _get_hosts(self, hash):
        tmp = []
        for h in hash:
            tmp.append(h['host'])
        return tmp

    def _get_hash_len(self, hash):
        return len(hash)

    def compare_lists(self, list1, list2):
        """
        Compares two lists.
        First list returned is items that are missing
        Second list returned is items that are missin
        """
        identical = True
        for row in list1:
            row['host'] = row['host'].replace('.mozilla.com', '')
        for row in list2:
            row['host'] = row['host'].replace('.mozilla.com', '')

        for row in list1:
            if row not in list2:
                identical = False
                if row['host'] not in [r['host'] for r in list2]:
                    self.hash1_diff.append({'host': row['host'].replace('.mozilla.com',''), 'data': row})
        for row in list2:
            if row not in list1:
                identical = False
                if row['host'] not in [r['host'] for r in self.hash2_diff]:
                    self.hash2_diff.append({'host': row['host'].replace('.mozilla.com',''), 'data': row})
        if identical:
            return identical, [[], []]
        else:
            return identical, [self.hash1_diff, self.hash2_diff]
    def analyze(self):
        msg = "Hosts in %s but not in %s\n" % (self.hash1_name, self.hash2_name)
        for h in self.hash1_diff:
            if h['host'] not in [h2['host'] for h2 in self.hash2_diff]:
                msg += "%s\n" % h['host']

        msg += "Hosts in %s but not in %s\n" % (self.hash2_name, self.hash1_name)
        for h in self.hash2_diff:
            if h['host'] not in [h2['host'] for h2 in self.hash1_diff]:
                msg += "%s\n" % h['host']

        ## Remove this if a way can be found to compare the output hashes
        return msg
        msg += "Differences of dictionary pairs across both lists\n"

        for row in self.hash1_diff:
            try:
                second_hashes = [h2['data'] for h2 in self.hash2_diff if h2['data']['host'] == row['host']]
                ret = self.dict_diff(row['data'], second_hash)
                for key in ret.iterkeys():
                    msg += '%s key "%s" is %s from %s' % (row['host'], key, ret[key][0], self.hash1_name)
                    msg += ' --- %s from %s\n' % (ret[key][1], self.hash2_name)
            except IndexError:
                ## Host isn't present in both lists
                pass
        ## I've not found a way to report against potentially changed data on a key by key bases
        ## If by some miracle i do figure this out
        ## Uncomment the following return msg and uncomment the previous
    ## {{{ http://code.activestate.com/recipes/576644/ (r1)
    def dict_diff(self, first, second):
        KEYNOTFOUND = '<KEYNOTFOUND>'       # KeyNotFound for dictDiff
        """ Return a dict of keys that differ with another config object.  If a value is
            not found in one fo the configs, it will be represented by KEYNOTFOUND.
            @param first:   Fist dictionary to diff.
            @param second:  Second dicationary to diff.
            @return diff:   Dict of Key => (first.val, second.val)
        """
        diff = {}
        # Check all keys in first dict
        for key in first.keys():
            if (not second.has_key(key)):
                diff[key] = (first[key], KEYNOTFOUND)
            elif (first[key] != second[key]):
                diff[key] = (first[key], second[key])
        # Check all keys in second dict to find missing
        for key in second.keys():
            if (not first.has_key(key)):
                diff[key] = (KEYNOTFOUND, second[key])
        return diff
    ## end of http://code.activestate.com/recipes/576644/ }}}




def compare_lists(list1, list2):
    """
    Compares two lists.
    First list returned is items that are missing
    Second list returned is items that are missin
    """
    missingFromList2 = [] 
    missingFromList1 = [] 
    for row in list1:
        if row not in list2:
            print "%s not found" % row
            missingFromList2.append(row)
    for row in list2:
        if row not in list1:
            missingFromList1.append(row)
    if missingFromList1 == missingFromList2:
        return None
    else:
        return missingFromList1, missingFromList2
