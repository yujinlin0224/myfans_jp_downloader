# myfans.jp Downloader

## Setup environment

- Use conda:

    ```sh
    conda create -p ./venv -c conda-forge --strict-channel-priority -y --file requirements.txt
    conda activate ./venv
    conda config --env --add channels conda-forge
    conda config --env --set channel_priority strict
    pip install -r requirements-pip.txt
    ```

- Use pip:

    ```sh
    python -m venv env
    source env/bin/activate
    pip install -r requirements.txt
    pip install -r requirements-pip.txt
    ```
