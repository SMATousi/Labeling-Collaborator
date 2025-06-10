# Labeling-Collaborator

This is the official implementation of "Labeling Collaborator: Combining Vision-Language Models and Weak Supervision for Nuanced Vision Classification Tasks".

## Installation

To set up the environment for this project, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/SMATousi/Labeling-Collaborator.git
   cd Labeling-Collaborator
   ```

2. Install the dependencies using pip:
   ```bash
   pip install -r requirements.txt
   ```

## Prompting Framework

The Labeling-Collaborator framework uses advanced prompting techniques with vision-language models to generate high-quality labels for nuanced classification tasks. To use the prompting framework, the user should have Ollama installed and running.

Run `run_agile_datasets.py` to see an example of how to use the prompting framework. To properly run the script, the user should provide the base directory of the datasets as a global variable in the script.

```
python run_agile_datasets.py --model_name ${MODEL_NAME} --dataset_name ${DATASET_NAME} --subset ${SPLIT}
```

The script will save a JSON file containing the results in the `results` directory.

## Weak Supervision

After saving the results, the user can use the weak supervision notebooks in the `weak_supervision` directory to perform weak supervision on the results.

## Citations

If you find this work useful in your research, please consider citing:

```bibtex
@article{labeling-collaborator,
  title={Labeling Collaborator: Combining Vision-Language Models and Weak Supervision for Nuanced Vision Classification Tasks},
  author={Tousi et al.},
  journal={},
  year={2025}
}
```

## License

This project is licensed under the terms of the license included in the repository.
