# DSS to CSV Tools

This repository contains Python scripts to convert CalSim3 output DSS files into CSV format and validate the conversion. It depends on the [`pydsstools` library](https://github.com/gyanz/pydsstools).

## Requirements

- **Compatibility**: The `pydsstools` library is compatible with 64-bit Python on Windows 10 and Ubuntu-like Linux distributions. For Linux, ensure that `zlib`, `math`, `quadmath`, and `gfortran` libraries are installed.
- **Dependencies**: This library depends on `heclib.a`, which must be installed correctly.

## Docker Setup

Included in the repository is a `Dockerfile` that runs a Linux container and installs the necessary libraries, fulfilling the compatibility and dependency requirements listed above. The instructions below are a guide to setting up a Docker container and running the Python scripts. If you are installing on Windows and don't want to use Docker, you can use the `Dockerfile` and the `pydsstools` README as a guide.

### Mac Users

If you are on a Mac, you may encounter issues installing Docker. I had these issues, so I've included the `docker-fix` files in this repo. See: [Docker for Mac Issue #7527](https://github.com/docker/for-mac/issues/7527).

## Python Scripts

The repository includes Python files for exporting DSS files to CSV and for validating them. Note that the `pydsstools` library prints every path as it processes it. I haven't been able to suppress this.

## Steps to Use

1. **Install Docker Desktop**: If necessary, download Docker from [Docker's website](https://www.docker.com/). If you are on a Mac and get malware warnings, see the notes above. Start up Docker. You can test your installation by running:
   `> docker info`

2. **Clone the Repository**: And `cd` into the directory.

3. **Edit `docker-compose.yml` if you want to change the data directory**: The `docker-compose.yml` is set up with relative directories. You can place your CalSim3 `DSS` output files in the `data/scenario` directory. For your first run, I recommend using this directory structure as a trial.

4. **Build the Docker Image**:
   ```bash
   > cd pydsstools-docker
   > docker-compose build
   ```
   Building takes a few minutes. Once the image is built, you don't have to build it again.

5. **Run Services**: See the `docker-compose` file for available services. Run them with the following command:
   ```bash
   > docker-compose run <service> --dss /data/scenario/<filename>.dss --csv /data/scenario/<filename>.csv
   ```
   Example:
   ```bash
   > docker-compose run convert --dss /data/scenario/DCR2023_DV_9.3.1_v2a_Danube_Adj_v1.8.dss --csv /data/scenario/DCR2023_DV_9.3.1_v2a_Danube_Adj_v1.8.csv
   ```
   You will see all the paths print on the console. This is a function of the `pydsstools` library. Once they have all printed, the console will hang for a bit. You have time for a cup of coffee. It takes about 5 minutes to run the process.

6. **Stop Services**: When done, stop running services using:
   ```bash
   > docker-compose down
   ```
Use Docker commands as normal. For example, to avoid voluminous print output, you can run Docker in the background with the `-d` flag. To automatically remove the container when it stops, use the `--rm` flag.
