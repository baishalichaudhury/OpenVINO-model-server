# Landing OpenVINO&trade; Model Server on Bare Metal Hosts and Virtual Machines

## Requirements

OpenVINO&trade; model server installation is fully tested on Ubuntu16.04, however there are no anticipated issues on other 
Linux distributions like CentoOS*, RedHat*, ClearLinux* or SUSE Linux*.

Download the installer from: [OpenVINO&trade; toolkit](https://software.intel.com/en-us/openvino-toolkit/choose-download)


## Installation of Dependencies

Generally, you need to repeat the steps listed in the [Dockerfile](../Dockerfile)

The steps include installation of Linux packages of cpio, make, wget, python3, python setup tools and virtualenv.

Later, OpenVINO&trade; toolkit need to be installed - at least the inference engine is required.

It is important to set correct environment variables PYTHONPATH and LD_LIBRARY_PATH pointing to Python modules of OpenVINO&trade; and compiled libraries.


## Model Server Installation
It is recommended to run OpenVINO&trade; model server from Python virtual environment. This will avoid all conflicts 
between Python dependencies from other applications running on the same host.

**Note** All python dependencies are included in `requirements.txt` file.
 
OpenVINO&trade; Model server can be installed using commands:

```
make install
```
or if you don't want to create a virtual environment:
```
pip install .

```
or if you want to modify the source code and easily test changes:
```
pip install -e . 
```

## Starting the Serving Service

Process of starting the model server and preparation of the models is similar to docker containers.

When working inside the activated virtual environment or with all Python dependencies installed, the server can be
started using `ie_serving` command:
```bash
ie_serving --help
usage: ie_serving [-h] {config,model} ...

positional arguments:
  {config,model}  sub-command help
    config        Allows you to share multiple models using a configuration file
    model         Allows you to share one type of model

optional arguments:
  -h, --help      show this help message and exit
```

The server can be started in interactive mode, as a background process or a daemon initiated by `systemctl/initd` depending
on the Linux distribution and specific hosting requirements.

Refer to [docker_container.md](docker_container.md) to get more details.
