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

The Labeling-Collaborator framework uses advanced prompting techniques with vision-language models to generate high-quality labels for nuanced classification tasks. The framework leverages powerful models to interpret visual content and generate structured annotations based on carefully designed prompts.

Key components of our prompting approach:
- Task-specific prompt engineering
- Multi-perspective prompt ensembling
- Confidence-based filtering

To use the prompting framework, see the example in `run_agile_datasets.py`.

## Weak Supervision

Our approach combines vision-language model outputs with weak supervision techniques to refine and improve label quality. The weak supervision module:

1. Aggregates labels from multiple sources (VLM prompts, rules, heuristics)
2. Resolves conflicts between labeling sources
3. Generates probabilistic labels for training downstream models

Examples of our weak supervision implementation can be found in the `weak-supervision` directory, with notebooks demonstrating the approach on various datasets.

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
