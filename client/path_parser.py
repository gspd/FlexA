'''
Created on Nov 14, 2015

@author: vhcandido
'''

import os
from stat import S_ISREG

def is_file(self, pathname):
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
    
    file.size = os.path.getsize(file_info.absolute_filepath)

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
    elif path.startswith(cur_dir+'/'):
        # then remove the prefix and keep the rest
        dir_rest = path[len(cur_dir)+1:]
        r = dir_rest.split('/')[1]
    ''' old version was also working
    elif path.startswith(cur_dir):
        # then remove the prefix and keep the rest
        dir_rest = path[len(cur_dir):]
        # check if it's a subdirectory
        if dir_rest[0] == '/':
            r = dir_rest.split('/')[1]
    '''
    return r

def print_file_list(file_dictionaries, cur_dir):
    
    if(not file_dictionaries):
        print("No files found.")
        return
    
    columns = file_dictionaries[0].keys()
    header = dict.fromkeys(columns, ' ')
    header['create_date'] = "Created on"
    header['modify_date'] = "Last modified on"
    header['size'] = "Size"
    header['name'] = "Name"
    
    # creates list of lists with every lenght
    all_widths = []
    all_widths.append([len(v) for v in header.values()])
    for file_dict in file_dictionaries:
        all_widths.append([len(v) for v in file_dict.values()])
    
    # checks the max lenght for every column
    widths = [max(row_lenghts) for row_lenghts in zip(*all_widths)]
    #maps the lenghts in the dictionary
    header_len = dict(zip(columns, widths))
    
    print(header['create_date'].ljust(header_len["create_date"]), end="  ")
    print(header['modify_date'].ljust(header_len["modify_date"]), end="  ")
    print(header['size'].ljust(header_len["size"]), end="  ")
    print(header['name'].ljust(header_len["name"]))

    sd_list = []
    # print info for every file
    for file_dict in file_dictionaries:
        # check if it's within current directory
        if cur_dir != os.path.dirname(file_dict['name']):
            subdir = get_subdir_name(cur_dir, file_dict['name'])
            
            # check if it's a subdirectory
            if subdir != "":
                sd = os.path.basename(subdir) + '/'
                if sd in sd_list:
                    continue
                print("-".ljust(header_len["create_date"]), end="  ")
                print("-".ljust(header_len["modify_date"]), end="  ")
                print("-".ljust(header_len["size"]), end="  ")
                print(sd.ljust(header_len["name"]))
                sd_list.append(sd)
            continue

        print(file_dict["create_date"].ljust(header_len["create_date"]), end="  ")
        print(file_dict["modify_date"].ljust(header_len["modify_date"]), end="  ")
        print(file_dict["size"].ljust(header_len["size"]), end="  ")
        print(os.path.basename(file_dict["name"]).ljust(header_len["name"]))
        
    #else: # check if current dir is substring at the beginning
    #    if not os.path.dirname(dic_file['name']).startswith(cur_dir):
    #        continue