#!/usr/bin/python
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

from setuptools import setup, find_packages

setup(
    name='Splice',
    version='0.1'
    license='GPLv2+',
    author='Splice Team - Red Hat',
    author_email='splice-devel@redhat.com',
    description='Framework for tracking entitlement consumption',
    url='https://github.com/splice/splice-server.git',
    packages=find_packages(),
)
