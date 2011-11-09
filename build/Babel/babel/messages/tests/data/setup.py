#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: setup.py 596 2011-03-17 14:05:55Z fschwarz $
# =============================================================================
# $URL: http://svn.edgewall.org/repos/babel/tags/0.9.6/babel/messages/tests/data/setup.py $
# $LastChangedDate: 2011-03-17 15:05:55 +0100 (Do, 17. Mär 2011) $
# $Rev: 596 $
# $LastChangedBy: fschwarz $
# =============================================================================
# Copyright (C) 2006 Ufsoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

# THIS IS A BOGUS PROJECT

from setuptools import setup, find_packages

setup(
    name = 'TestProject',
    version = '0.1',
    license = 'BSD',
    author = 'Foo Bar',
    author_email = 'foo@bar.tld',
    packages = find_packages(),
)
