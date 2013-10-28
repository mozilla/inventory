Bulk Action API
===============

Action Supported:
-----------------
    * create
    * udpate

Right now, this API is not a tool that can delete objects.

Goal
----
This API can be used to create/update to many objects at the same time. It will allow a
large change to happen in one transaction.

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

The API uses a JSON blob ('main' blob) that stores a key 'systems' that is mapped to
another dictionary that maps hostnames to json blobs that represent systems blobs.
Contained in each system blob is a system's attributes and possibly other JSON blobs
representing Static Registrations (StaticRegs) and Hardware Adapters (HWAdapters) and
somtimes CNAME DNS records.

For example::

    {
        "systems": { #### A list of system JSON blobs. This is the 'main' blob.
            "hostname.mozilla.com": {  #### A system JSON blob
                "hostname": "hostname",
                "pk": 9550,
                "rack_order": "7.02",
                ...
                ...
                ...
                "staticreg_set": {  #### A dict of Static Regs JSON blobs indexed by SREG name
                    "nic0": { #### A StaticReg JSON blob
                        "fqdn": "hostname.mozilla.com",
                        "ip_str": "10.26.56.133",
                        "pk": 3216,
                        ...
                        ...
                        ...
                        "hwadapter_set": {  #### A list of HWAdapter JSON blobs
                            "hw0": {
                                "mac": "00:25:90:C2:30:D8",
                                "name": "hw0",
                                "pk": 3202
                                ...
                                ...
                                ...
                            }
                        },
                    }
                },
            }
        }
    }


Here is the same example from above but with the non-relational attributes
removed. This is meant to show you the consistent JSON structure that the
API expects::

    {
        "systems": { #### A list of system JSON blobs. This is the 'main' blob.
            "hostname.mozilla.com": {  #### A system JSON blob
                ...
                ...
                ...
                "staticreg_set": {  #### A dict of Static Regs JSON blobs indexed by SREG name
                    "nic0": { #### A StaticReg JSON blob
                        ...
                        ...
                        ...
                        "hwadapter_set": {  #### A list of HWAdapter JSON blobs
                            "hw0": {
                                ...
                                ...
                                ...
                            }
                        },
                    }
                },
            }
        }
    }

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

    {
        'systems': {
            "foo.mozilla.com": {
                "hostname": "foo.mozilla.com",
            }
        },
        'commit': true
    }

For contrast, here is a JSON blob that would *update* a system with the ``pk``
(primary key) ``5046`` to have the hostname ``foo.mozilla.com``::

    {
        'systems': {
            "foo.mozilla.com": {
                "hostname": "foo.mozilla.com",
                "pk": 5046,
            }
        },
        'commit': true
    }

Rollback by default
-------------------
When you send a JSON blob to Inventory it will, by default, will not save the changes the
JSON blob would cause. You need to put the key 'commit' with the value 'true' in the top
level of the JSON blob for Inventory to save your changes.
