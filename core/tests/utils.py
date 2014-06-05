class Refresher(object):
    # Mixin class. Make sure the mixer class is django ORM based class
    def refresh(self):
        return self.__class__.objects.get(pk=self.pk)
