from django import template
from settings.local import MEDIA_URL as STATIC_URL 
register = template.Library()


class StaticLinkNode(template.Node):
    def __init__(self, file_type, file_path):
        self.file_type = file_type
        if not file_path.endswith(file_type) and file_type != "img":
            file_path = "%s.%s" % (file_path, file_type)
        self.file_path = file_path

    def render(self, context):
        if self.file_type == 'js':
            tag = "<script type='text/javascript' src='%sjs/%s'></script>"
            tag %= (STATIC_URL, self.file_path)
        if self.file_type == 'css':
            tag = "<link rel='stylesheet' type='text/css' href='%scss/%s'>"
            tag %= (STATIC_URL, self.file_path)
        if self.file_type == 'img':
            tag = "<img src='%simg/%s'/>"
            tag %= (STATIC_URL, self.file_path)

        return tag


def staticlink_tag(parser, token):
    (staticlink_type, staticlink_file) = tuple(token.split_contents()[1].split(":"))
    return StaticLinkNode(staticlink_type, staticlink_file)


register.tag('staticlink', staticlink_tag)
