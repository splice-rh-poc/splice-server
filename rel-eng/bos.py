#!/usr/bin/env python
import ConfigParser
import os
import shutil
import sys
import tempfile
from optparse import OptionParser

CFG=None
def parse_config(filename):
    global CFG
    if not os.path.exists(filename):
        print "%s does not exist" % (filename)
        return False
    config = ConfigParser.ConfigParser()
    config.read(filename)
    cfg = {}
    for section in config.sections():
        cfg[section]={}
        for item,value in config.items(section):
            cfg[section][item] = value
    for section in ["builder", "projects", "third_party_deps"]:
        if not cfg.has_key(section):
            print "Config is missing section '%s'" % (section)
            return False
    for entry in ["git_dir", "repo_dir"]:
        if not cfg["builder"].has_key(entry):
            print "Config [builder] is missing entry for '%s'" % (entry)
            return False
    for name, third_party_dir in cfg["third_party_deps"].items():
        if not os.path.exists(third_party_dir):
            print "Config [third_party_deps] entry for %s: '%s' does not exist" % (name, third_party_dir)
            return False
    CFG=cfg
    return True

def run_command(cmd):
    print "Running: %s" % (cmd)
    ret_val = os.system(cmd)
    if ret_val:
        print "Error running command: %s" % (cmd)
        sys.exit(1)

def prep(git_dir, temp_dir, repo_dir):
    clean_temp_dir(temp_dir)
    for entry in [git_dir, temp_dir, repo_dir]:
        if not os.path.exists(entry):
            os.makedirs(entry)

def build(git_dir, temp_dir, proj_name, proj_url):
    expected_source_dir = os.path.join(git_dir, proj_name)
    if not os.path.exists(expected_source_dir):
        print "Will checkout source for '%s' with git url '%s'" % (proj_name, proj_url)
        cmd = "cd %s && git clone %s" % (git_dir, proj_url)
        run_command(cmd)
    print "\nBuilding: %s from %s" % (proj_name, proj_url)
    cmd = "cd %s && git pull --rebase" % (expected_source_dir)
    run_command(cmd)
    cmd = "cd %s && tito build --rpm -o %s" % (expected_source_dir, temp_dir)
    if CFG["scls"].has_key(proj_name):
        cmd += " --scl %s" % (CFG["scls"][proj_name])
    run_command(cmd)

def copy_deps(dest_dir):
    for name, location in CFG["third_party_deps"].items():
        run_command("cp %s/*.rpm %s" % (location, dest_dir))

def createrepo(temp_repo_dir, repo_dir):
    # Nervous deleting a full dir tree, so will move current to a backup
    # and only rmtree on a backup
    backup = "%s.backup" % (repo_dir)
    if os.path.exists(backup):
        shutil.rmtree(backup)
    cmd = "mv %s %s" % (repo_dir, backup)
    run_command(cmd)
    cmd = "mv %s %s" % (temp_repo_dir, repo_dir)
    run_command(cmd)
    cmd = "cd %s && createrepo ." % (repo_dir)
    run_command(cmd)
    cmd = "chmod -R go+rX %s" % (repo_dir)
    run_command(cmd)
    cmd = "restorecon -R %s" % (repo_dir)
    run_command(cmd)

def clean_temp_dir(temp_dir):
    if os.path.exists(temp_dir):
        # Ensure that we could only delete a directory under "/tmp"
        if temp_dir[:5] == "/tmp/":
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    parser = OptionParser(description="Build Our Stuff - Builds RPMs for multiple subprojects")
    parser.add_option('--config', action='store', default="bos.cfg", help="Config file for builder options")
    (opts, args) = parser.parse_args()

    if not parse_config(opts.config):
        print "Error with config file: %s" % (opts.config)
        sys.exit(1)

    git_dir=CFG["builder"]["git_dir"]
    repo_dir=CFG["builder"]["repo_dir"]
    temp_dir = tempfile.mkdtemp(prefix="splice_builder", dir="/tmp") # Used for tito output
    temp_repo_dir = tempfile.mkdtemp(prefix="splice_repo", dir="/tmp") # Used to stage built rpms & 3rd party 
    try:
        prep(git_dir, temp_dir, repo_dir)
        for proj_name, proj_url in CFG["projects"].items():
            build(git_dir, temp_dir, proj_name, proj_url)
        copy_deps(temp_repo_dir)
        cmd = "find %s -name \"*.rpm\" -exec cp {} %s \;" % (temp_dir, temp_repo_dir)
        run_command(cmd)
        createrepo(temp_repo_dir, repo_dir)
    finally:
        clean_temp_dir(temp_dir)
        clean_temp_dir(temp_repo_dir)

    print "Successful build.  Repo directory is: %s" % (repo_dir)


