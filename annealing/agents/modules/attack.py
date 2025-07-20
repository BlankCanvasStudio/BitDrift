# attack.py
# The attack module defines how to handle attacks on the host proper
#
import logging
import os
import random
import glob

def _fillfile(fn, size):
    """
    fillfile (fn, size) -> None
    Fills a file with name fn of size size with garbage.
    """
    with open(fn, 'wb') as fh:
        fh.write(os.urandom(size))
    return

def prep_tgtfiles(tf_dir, sizerange, filerange):
    """
    prep_tgtfiles(tf_dir, sizerange, filerange)
    prep_tgfiles: creates targetfiles in the target directory

    tf_dir: targetfile_directory
    sizerange: the range in file sizes, specified as a tuple of (minsize, maxsize)
    filerange: the range of files to generate per call

    Target files are bogus files which in the game exercise contain potentially valuable
    information for transfer to the ground segment.  With each call of prep_tgtfiles, the
    target file directory is filled with files to transfer

    returns: nothing
    """
    maxfiles = random.randint(filerange[0], filerange[1])
    fcount = len(glob.glob(os.path.join(tf_dir, '*')))
    for i in range(0, maxfiles):
        findex = fcount + i + 1
        fn = os.path.join(tf_dir, 'dumpfile.%05d' % findex)
        _fillfile(fn, random.randint(sizerange[0],sizerange[1]))
    return


def purge_tgtfiles(tf_dir, purge_arg):
    """
    purge_tgtfiles(tf_dir, purge_type, purge_arg)
    purge_tgtfiles: cleares out the target directory in
    chronological order (earliest first) based on the purge argument

    tf_dir: targetfile_directory
    purge_arg: number of files to purge; if equal to 0, purge everything

    Empties the target file directory.
    """
    fns = glob.glob(os.path.join(tf_dir, 'dumpfile*'))
    # Process the purge_arg argument by truncating hte list if purge_arg > 0 
    if purge_arg > 0:
        fns = fns[0:purge_arg]
    for i in fns:
        os.unlink(i)        
    return

def move_tgtfile(tf_n, basestation_info, iscopy):
    """
    move_tgtfile(tf_n, basestation_info, iscopy)
    moves a targetfile to the base station via scp

    tf_n: name of the targetfile
    basestation_info: address of the basestation
    iscopy: boolean; if true, don't delete the file on transfer complete.
    """
    return

def encrypt_tgtfile(tf_n):
    """
    encrypt_tgtfile(tf_n)
    encrypts the targetfile for ransomware attacks
    
    tf_n: filename
    'encrypts' a targetfile by running a sha256sum and then renaming the file to
    x.enc
    """
    logging.info('Encrypting %s' % os.path.basefname(tf_n))
    os.system('sha256 %s' % tf_n)
    os.rename(tf_n, tf_n + '.enc')
    return

def subvert(status_dir, malware_path):
    """
    'subverts' a host for malware
    Subversion consist of running a 'malawre' process which announces that its malware
    """
    
    return

