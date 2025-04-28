# DSS to CSV Tools

This repository contains Python scripts to convert CalSim3 output DSS files into CSV format and validate the conversion. It depends on the [`pydsstools` library](https://github.com/gyanz/pydsstools).

## Requirements

- **Compatibility**: The `pydsstools` library is compatible with 64-bit Python on Windows 10 and Ubuntu-like Linux distributions. For Linux, ensure that `zlib`, `math`, `quadmath`, and `gfortran` libraries are installed.
- **Dependencies**: This library depends on `heclib.a`, which must be installed correctly, which is why we are using Docker.

## Docker Setup

Included in the repository is a `Dockerfile` that runs a Linux container and installs the necessary libraries, fulfilling the compatibility and dependency requirements listed above. The instructions below are a guide to setting up a Docker container and running the Python scripts. If you are installing on Windows and don't want to use Docker, you can use the `Dockerfile` and the `pydsstools` README as a guide.

### Mac Users

If you are on a Mac, you may encounter issues installing Docker. I had these issues, so I've included the `docker-fix` files in this repo. See: [Docker for Mac Issue #7527](https://github.com/docker/for-mac/issues/7527).

## Python Scripts

The repository includes Python files for exporting DSS files to CSV and for validating them. Note that the `pydsstools` library prints every path as it processes it. I haven't been able to suppress this.

## Steps to Use

1. **Install Docker Desktop**: If necessary, download Docker from [Docker's website](https://www.docker.com/). If you are on a Mac and get malware warnings, see the notes above. Start up the Docker app. You can test your installation by running:
   ```bash
   > docker info
   ```

3. **Clone the Repository**: And `cd` into the directory.

4. **Edit `docker-compose.yml` if you want to change the data directory**: The `docker-compose.yml` is set up with relative directories. See the directory documenation below. For at least your first run, I recommend using this directory structure as a trial.

5. **Build the Docker Image**:
   ```bash
   > cd pydsstools-docker
   > docker-compose build
   ```
   Building takes a few minutes. Once the image is built, you don't have to build it again.

6. **Run Services**: See the `docker-compose` file for available services. Run them with the following command:
   ```bash
   > docker-compose run <service> --dss /data/scenario/<filename>.dss --csv /data/scenario/<filename>.csv
   ```
   Example:
   ```bash
   > docker-compose run convert --dss /data/scenario/DCR2023_DV_9.3.1_v2a_Danube_Adj_v1.8.dss --csv /data/scenario/DCR2023_DV_9.3.1_v2a_Danube_Adj_v1.8.csv
   ```
   You will see all the paths print on the console. This is a function of the `pydsstools` library. Once they have all printed, the console will hang for a bit. You have time for a cup of coffee. It takes about 5 minutes to run the process.

7. **Stop Services**: When done, stop running services using:
   ```bash
   > docker-compose down
   ```
Use Docker commands as normal. For example, to avoid voluminous print output, you can run Docker in the background with the `-d` flag. To automatically remove the container when it stops, use the `--rm` flag.

# Variable filtering pipeline

This respository also contains files and a suggested data directly structure to create a pipeline for different levels of csv processing:

- Level 0: csv format directly from DSS output
- Level 1: csv with system and validation variables removed through Part C filtering
- Level 2: final variable csv for the COEQWAL website

## Suggested directory tree

```text
COEQWAL-pydsstools/
├── README.md
│
├── data/                     
│   ├── 00_dss/               # raw DSS output files
│   │   └── scenarioA.dss
│   ├── 10_level0_raw_csv/    # Level-0 CSVs (1-to-1 export)
│   │   └── scenarioA_L0.csv
│   ├── 20_level1_filtered/   # Level-1 CSVs (after dropping whole Part C's)
│   │   └── scenarioA_L1.csv
│   ├── 30_variable_maps/     # helper text files for manual review
│   │   ├── PartC.txt         # unique Part-C list
│   │   └── PartsBC.txt       # Part-C ➜ Part-B map
│   ├── 40_configs/           # YAML keep-lists used to create Level-2
│   │   └── scenarioA_keep.yml
│   └── 50_level2_final/      # Level-2, database-ready CSVs
│       └── scenarioA_L2.csv
│
└── pydsstools-docker/        # all runnable code + container build
    ├── python-code/
    │   ├── dss_to_csv.py     # Level-0 exporter
    │   └── csv_levels.py     # multi-mode helper (0,1,2,listC,mapBC)
    ├── Dockerfile
    └── docker-compose.yml
```

## DSS → COEQWAL variables pipeline

### Quick-start (after building Docker image, see above)
----------------------------------------------------

> **Tip** Run these `docker compose` commands from inside the
> `pydsstools-docker/` folder.  Inside the container, the project's top-level
> `data/` directory is mounted at **`/data`**, so the paths you see below will
> resolve automatically.

### 1. Build Level-0 CSV
```bash
> docker compose run --rm convert \
  --dss  /data/00_dss/scenarioA.dss \
  --csv  /data/10_level0_raw_csv/scenarioA_L0.csv
```


### 2. List all unique Part-C values
```bash
> docker compose run --rm csv-levels listC \
  /data/10_level0_raw_csv/scenarioA_L0.csv \
  --outfile /data/30_variable_maps/PartC.txt
```

### 3. Produce Level-1 after deciding what to drop
```bash
> docker compose run --rm csv-levels 1 \
  /data/10_level0_raw_csv/scenarioA_L0.csv \
  /data/20_level1_filtered/scenarioA_L1.csv \
  --drop JUNKC1 JUNKC2
```

### 4. Map remaining Part-C → Part-B combinations (after Level-1)
```bash
> docker compose run --rm csv-levels mapBC \
  /data/20_level1_filtered/scenarioA_L1.csv \
  --mapfile /data/30_variable_maps/PartsBC.txt
```

### 5. Build Level-2 using an edited YAML keep-list
```bash
> docker compose run --rm csv-levels 2 \
  /data/20_level1_filtered/scenarioA_L1.csv \
  /data/50_level2_final/scenarioA_L2.csv \
  --config /data/40_configs/scenarioA_keep.yml
```
