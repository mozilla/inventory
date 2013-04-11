.. _rage:

Problem
=======

http://python.6.n6.nabble.com/Signals-for-ManyToMany-relations-question-td460014.html

http://stackoverflow.com/questions/1925383/issue-with-manytomany-relationships-not-updating-inmediatly-after-save

This is what I want to do:

Example models
--------------
Models::

    class Foo(models.Model):
        items = fields.ManyToMany(Item)

    class Item(models.Model):
        name = fields.CharField()

Example:
--------
Let's assume I don't ever want to associate a Foo object with an item that has name == "Green"::

    >>> f = Foo()
    >>> item = Item("Green")
    >>> f.items.add(item)

    ^ I want an exception raised during "add(item)"

Why can't I do that sainly?!?!

.. autofunction:: mozdns.models.views_handler
