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