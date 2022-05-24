# Data Annotation Platform
This software is a data annotation platform aimed at datasets containing trajectories in urban traffic.

## Install locally
Currently, the platform is only available through a local installation. This section outlines how to install the data annotation platform locally.

### Prerequisites
It is assumed that the following prerequisites are satisfied on the machine:

1. Python 3.3+ with pip is installed.
2. The dataset is located inside the ```data_annotation_platform/data``` directory. Two files are required: ```broken_trajectorie.pkl``` and ```segments.pkl```.
3. The video recording is located inside the ```data_annotation_platform/video``` directory. The file should be named ```video``` and ```mp4``` format.

### Install using a bash script
The easiest way to set up the platform on a local environment is to use the  ```run``` bash script included in the source code. The script assumes that the dependencies from the previous section are satisfied.

The application can be accessed on ```localhost:5006```


### Install manually
Below is an outline of the steps performed by the script which can be recreated manually if needed:

1. Create a Python virtual environment using the ```venv``` module bundled with Python (version 3.3+):

    ```python3 -m venv env```

   The second parameter ```env``` is the name of the virtual environment. This could be any name but in this case we simply use ```env``` and the following steps assume that name.

2. Activate the environment:

    ```source env/bin/activate```

3. Install dependencies:

    ```python3 -m pip install -r requirements.txt```

4. Run bokeh server:

    ```bokeh serve data_annotation_platform --dev```

5. Access the application on:

    ```localhost:5006```

Steps 1 and 2 are optional but highly recommended. The virtual environment avoids version conflicts with packages that might be already installed globally on the machine. It also avoids cluttering the global Python installation with packages only relevant to this project.

## Prototypes

The initial prototypes developed for this project can be found in the folders ```dash_prototype``` and ```bokeh_prototype```.

They both contain a run script like the one described earlier. Since they're prototypes, they're not documented in more detail.