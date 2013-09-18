def htmlify_dhcp_output(dhcp_input, preserve_tabs=False):
    lines = dhcp_input.split('\n')

    def tabs_to_spaces(line):
        if not preserve_tabs:
            if line.startswith('\t'):
                line = line[1:]

        return line.replace('\t', '    ')

    def wrap_tags(line):
        return "<span class='dhcp-output-line'><pre>" + line + "</pre></span>"

    return '\n'.join(map(wrap_tags, map(tabs_to_spaces, lines)))
