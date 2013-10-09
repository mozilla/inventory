Bulk Action API
===============

Action Supported:
-----------------
    * create
    * udpate

Right now, this API is not a good tool for deleting entire system objects.

Goal
----
This API can be used to create/update to many objects at the same time. It will allow a large change
to happen in one transaction.

General Usage
-------------
Using this API is usually a three part process:

    1. Export data
    2. Edit exported data
    3. Upload data to Inventory for saving

Skipping step 1, even if you are creating new objects, is highly discouraged.

Data Structure
--------------
Communication between client and server is done via a JSON protocol.  The Bulk
Action API relies on a strictly structured JSON blob that is exported by
Inventory, modified by a user, and then sent back to Inventory for processing.

The API uses a JSON blob (referenced as the 'main' blob) that always consists
of a list of system JSON blobs. Contained in each system blob is a system's
attributes and possibly other JSON blobs representing Static Registrations
(StaticRegs) and Hardware Adapters (HWAdapters).

For example::

    [  #### A list of system JSON blobs. This is the 'main' blob.
        ...
        ...
        ...
        {  #### A system JSON blob
            "asset_tag": "7349",
            "hostname": "puppet1.private.phx1.mozilla.com",
            "rack_order": "1.16",
            "pk": 5046,
                ...
                ...
                ...
            "static_reg_set": [  #### A list of Static Registration JSON blobs
                {  #### A StaticReg JSON blob
                    "fqdn": "puppet1.private.phx1.mozilla.com",
                    "ip_type": "4",
                    "pk": 11,
                    "ip_str": "10.8.75.10"
                    ...
                    ...
                    ...
                    "hwadapter_set": [  #### A list of HWAdapter JSON blobs
                        {  #### A HWAdapter JSON blob
                            "mac": "44:1E:A1:5C:01:B4",
                            "pk": 27,
                            "name": "nic1"
                            ...
                            ...
                            ...
                        },
                    ],
                },
            ]
        }
    ]

Here is the same example from above but with the non-relational attributes
removed. This is meant to show you the consistent JSON structure that the
API expects::

    [  #### A list of system JSON blobs. This is the 'main' blob.
        ...
        ...
        ...
        {  #### A systems JSON blob
                ...
                ...
                ...
            "static_reg_set": [  #### A list of Static Registration JSON blobs
                {  #### A Static Registration JSON blob
                    ...
                    ...
                    ...
                    "hwadapter_set": [  #### A list of HWAdapter JSON blobs
                        {  #### A HWAdapter JSON blob },
                    ],
                },
            ]
        }
    ]

As a general rule, attributes that end in ``_set`` are a list of related JSON
blobs that may or may not have attributes that end in ``_set``.

Sending JSON blobs to Inventory
===============================
Upon receiving a JSON blob, Inventory looks at the list of system objects and
determines for each system whether you are (a) creating a new system with new
StaticReg and HWAdatper or (b) updating an existing system.

In the case of (a) you are creating a new system and new related objects. At
this time you cannot create an new system and assign it existing
StaticReg/HWAdapter objects -- practically this means JSON blobs embedded in a
'new' system blob cannot have a 'pk' attribute.

Inventory will try to process the main JSON in a _single_ database transaction.
Only after every object is processed without error will the transaction be
committed. If there are errors when processing a JSON blob Inventory will not
commit the transaction and will return which blob it had an issue processing
(an error message will also be returned).

Creating/Updating Objects
=========================
Inventory is keyed into whether you are updating or creating by detecting the
presence of a ``pk`` attribute in a JSON blob.

For example here is a JSON blob that would *create* a new system with the
hostname ``foo.mozilla.com``::

    [
        {
            "hostname": "foo.mozilla.com",
        }
    ]

For contrast, here is a JSON blob that would *update* a system with the ``pk``
(primary key) ``5046`` to have the hostname ``foo.mozilla.com``::

    [
        {
            "hostname": "foo.mozilla.com",
            "pk": 5046,
        }
    ]

Creating/Updating Static Registrations and Hardware Adapters
------------------------------------------------------------

