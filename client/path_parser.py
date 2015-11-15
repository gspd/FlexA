'''
Created on Nov 14, 2015

@author: vhcandido
'''

import os
from stat import S_ISREG

def is_file(pathname):
    return S_ISREG(os.stat(pathname).st_mode)

def set_file_info_to_send(file_info, filename, data_dir):
    """ If the given filename exists, is a regular file and is inside
        the mapped directory tracked by FlexA, this function:
         -Finds names relative to FlexA system and absolute pathnames
            for local file system

        Parameters:
            file_info - object to store some info about the path in
                different environments (FlexA dir or local one)
            filename - name of file that will be process
    """
    # local full filepath
    file_info.absolute_filepath = os.path.abspath(filename)

    # verify if path exists
    if not os.path.exists(file_info.absolute_filepath):
        print("Skipping '" + file_info.absolute_filepath + "'. "
              "File was not found.")
        return False
    # verify if it's a regular file
    elif not is_file(file_info.absolute_filepath):
        print("Skipping '" + file_info.absolute_filepath + "'. "
              "It's not a path to a regular file.")
        return False
    #verify if it's withing FlexA data directory
    elif not data_dir in file_info.absolute_filepath:
        print("Skipping '" + file_info.absolute_filepath + "'. "
                "File can't be located outside mapped directory")
        return False
    
    file_info.size = os.path.getsize(file_info.absolute_filepath)

    # full filepath relative to FlexA file system
    file_info.relative_filepath = file_info.absolute_filepath.split(data_dir)[1]

    file_info.filename = file_info.relative_filepath.split('/')[-1]

    # name of encrypted file
    file_info.enc_filename = file_info.filename + ".enc"

    # full local filepath for the encrypted file (temporary to send and receive)
    file_info.absolute_enc_filepath = file_info.absolute_filepath + ".enc"

    return True

def set_file_info_to_receive(file_info, current_local_dir, current_relative_dir, data_dir):
    file_info.absolute_filepath = os.path.join(current_local_dir, file_info.filename)
    file_info.absolute_filepath = os.path.normpath(file_info.absolute_filepath)
    file_info.relative_filepath = os.path.join(current_relative_dir, file_info.filename)
    file_info.relative_filepath = os.path.normpath(file_info.relative_filepath)

    #verify if it's withing FlexA data directory
    if not data_dir in file_info.absolute_filepath:
        print("Skipping '" + file_info.absolute_filepath + "'. "
                "File can't be located outside mapped directory")
        return False

    file_info.enc_filename = file_info.filename + '.enc'
    file_info.absolute_enc_filepath = file_info.absolute_filepath + '.enc'
    return True



def get_subdir_name(cur_dir, path):
    r = ''
    
    # if path is (somewhere) inside cur_dir
    if cur_dir == '/':
        r = path.split('/')[1]
    elif path.startswith(cur_dir):
        # then remove the prefix and keep the rest
        dir_rest = path[len(cur_dir):]
        # check if it's a subdirectory
        if dir_rest[0] == '/':
            r = dir_rest.split('/')[1]
    ''' this won't work, dunno why
    elif path.startswith(cur_dir+'/'):
        # then remove the prefix and keep the rest
        dir_rest = path[len(cur_dir)+1:]
        r = dir_rest.split('/')[1]
        print(dir_rest.split('/'))
    '''
    return r

def print_file_list(file_dictionaries, cur_dir):
    
    if(not file_dictionaries):
        print("No files found.")
        return
    
    # columns come in a different order each call
    columns = file_dictionaries[0].keys()
    header = dict.fromkeys(columns, '')
    header['create_date'] = "Created on"
    header['modify_date'] = "Last modified on"
    header['size'] = "Size"
    header['name'] = "Name"
    
    # create a list of lists
    # each list (row) has the lenghts of each column
    all_widths = []
    # first the header lenghts
    all_widths.append([len(v) for v in header.values()])
    # then the lenghts of the remaining rows
    for file_dict in file_dictionaries:
        all_widths.append([len(v) for v in file_dict.values()])

    # checks the max lenght for every column iterating between rows
    widths = [max(row_lenghts) for row_lenghts in zip(*all_widths)]
    #maps the lenghts in the dictionary to be accessed together with file info
    header_len = dict(zip(columns, widths))
    
    # ordered header labels (column names)
    # this is the order things will be shown
    ord_hl = ['create_date', 'modify_date', 'size', 'name']

    # prints header
    print("  ".join(header[label].ljust(header_len[label]) for label in ord_hl))

    # a list with subdirectories already shown so they won't be again
    shown_sd = []
    # print info for every file
    for file_dict in file_dictionaries:
        
        # check if it's NOT directly within current directory
        if cur_dir != os.path.dirname(file_dict['name']):
            # check if it's a direct subdirectory
            subdir = get_subdir_name(cur_dir, file_dict['name'])
            if subdir != "":
                sd = os.path.basename(subdir) + '/'
                if not sd in shown_sd: # it hasn't been shown
                    print("-"*header_len["create_date"], end="  ")
                    print("-"*header_len["modify_date"], end="  ")
                    print("-"*header_len["size"], end="  ")
                    print(sd.ljust(header_len["name"]))
                    shown_sd.append(sd) # add it to the shown list 
            continue
        
        file_dict['name'] = os.path.basename(file_dict['name'])
        print("  ".join(file_dict[label].ljust(header_len[label]) for label in ord_hl))
        
    #else: # check if current dir is substring at the beginning
    #    if not os.path.dirname(dic_file['name']).startswith(cur_dir):
    #        continue