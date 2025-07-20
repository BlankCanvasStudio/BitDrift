# BitDrift

DropBox, but worse in every way!

**BitDrift** is a Git-aware file synchronization manager that uses `unison` over SSH to sync files and folders between machines. It automatically detects Git repositories, excludes them from syncing, and records metadata in a `.hydrate` file for future rehydration. BitDrift supports per-user and global configs, daemon mode, and systemd integration.

---


## 🔧 Installation

Clone the repository and run:

```bash
sudo make install
```

This will:

    - Install required dependencies (unison, ssh, git) via dnf or apt

    - Copy the bitdrift binary to /usr/local/bin/bitdrift

    - Install the default config to /etc/bitdrift/bitdrift.conf

    - Copy the systemd unit to /etc/systemd/system/bitdrift.service



## ⚙️ Configuration

BitDrift supports both global and per-user configs:

    Global Config: /etc/bitdrift/bitdrift.conf

    User Config: ~/.config/bitdrift/bitdrift.conf

Create a user config if one doesn't exist:

```bash
mkdir -p ~/.config/bitdrift
cp /etc/bitdrift/bitdrift.conf ~/.config/bitdrift/bitdrift.conf
```

or enable bitdrift as a user with:

```bash
bitdrift enable
```

## Example configuration

```
[general]
frequency=5
remote_hostname=user@remotehost
remote_host_storage_folder=/opt/bitdrift/storage
unison_args=""

[files]
# Absolute paths to sync

[ignore]
# Absolute paths to exclude from sync
```

## 🚀 Usage

**bitdrift [options]**

Options

Flag	Description
-d	Run as a daemon, syncing all configured users continuously
-a <path>	Add a file or folder to the sync list
-i <path>	Add a file or folder to the ignore list
-h6 <repo>	Hydrate a Git repo using metadata from .hydrate
-r	Run a sync once for the current config
-e	Enable and start the systemd BitDrift service
-l <path>	Load (download) a remote path to the local machine


## 📦 Examples

Add a folder to sync:

```bash
bitdrift -a ~/Projects/myapp
```

Ignore a subdirectory:

```bash
bitdrift -i ~/Projects/myapp/node_modules
```

Run a one-time sync:

```bash
bitdrift -r
```

Run BitDrift in daemon mode:

```bash
sudo bitdrift -d
```

Enable and start systemd service:

```bash
bitdrift -e
```

Hydrate a Git repo found in .hydrate:

```bash
bitdrift -h6 frontend
```

Load a remote folder:

```bash
bitdrift -l frontend
```


## 🧠 Features

**Git-Aware Syncing**
Scans directories for Git repos, excludes them from unison, and writes their metadata to .hydrate.

**Rehydration Support**
Hydrate Git repos using stored URL/branch/commit data with -h6.

**Daemon Mode**
Continuously syncs files for all users with configs at ~/.config/bitdrift/bitdrift.conf. Also syncs root.

**Remote Prep**
Automatically creates and chmods storage folders on the remote host before syncing.

**Flexible Ignore Rules**
Ignore subdirectories or files using unison's -ignore Path pattern.



## 🖥️ Daemon Behavior

When run with -d, BitDrift:

    Iterates through /home/* users

    Runs bitdrift run as each user (via sudo -u)

    Also syncs root files

    Sleeps for frequency seconds between runs



## 🗃️ Remote Folder Layout

/opt/bitdrift/storage/
├── myfolder/
│   ├── .hydrate
│   └── synced-content/

**Note:** The path /opt/bitdrift/storage is configurable via the `remote_host_storage_folder` 
parameter in any of your config files



## 📂 Hydration File Format

.hydrate entries are generated for Git repos found during sync:

```
repo-path|git-url|branch-name|commit-hash
```

You can rehydrate using:

```bash
bitdrift -h6 repo-path
```


## Dependencies

- Unison
- ssh
- POSIX-compliant shell (tested with sh and bash)
- git


### Random dependencies you probably already have

- mkdir
- grep
- awk
- sed
- echo
- chmod
- sort
- awk
- printf
- cd
- pushd 
- popd
- touch
- ls
- systemd (optional)


### Build Dependencies

- Make
- sh / bash

