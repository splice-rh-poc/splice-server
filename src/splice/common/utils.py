# -*- coding: utf-8 -*-
#
# Copyright © 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


def sanitize_dict_for_mongo(input_dict):
    """
    @param input_dict   dictionary to be processed and convert all "." and "$" to safe characters
                        "." are translated to "_dot_"
                        "$" are translated to "_dollarsign_"
    @type input_dict: dict

    @return safe dictionary able to store in mongo
    @rtype: dict
    """
    ret_val = {}
    for key in input_dict:
        cleaned_key = key.replace(".", "_dot_").replace("$", "_dollarsign_")
        ret_val[cleaned_key] = input_dict[key]
    return ret_val