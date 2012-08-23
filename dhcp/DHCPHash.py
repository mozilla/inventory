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
                tmp['host'] = m.group(1)
                for the_key in m.group(2).split(';'):
                    for known in self.known_options:
                        if known in the_key:
                            tmp[known] = the_key.replace(known, '').strip().strip('"').strip("'")
            hash_list.append(tmp)
        return hash_list


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
            missingFromList2.append(row)
    for row in list2:
        if row not in list1:
            missingFromList1.append(row)
    if missingFromList1 == missingFromList2:
        return None
    else:
        return missingFromList1, missingFromList2
