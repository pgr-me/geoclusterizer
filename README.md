# Geoclusterizer

The Geoclusterizer is a clustering routine that uses publicly-available data to group like geographical areas. We reduce the dimensionality of the dataset using the [LinearCorex](https://github.com/gregversteeg/LinearCorex) method and then fitting a [Gaussian Mixture Model](https://scikit-learn.org/stable/modules/mixture.html#) on that data to generate clusters of Census tracts.

## Motivation

Marketing professionals often use customer segmentation to serve more differentiated products and services to their customers. Traditionally, marketing analysts have used a set of heuristics and Excel-based analytical methods to segment customers. More recently, unsupervised learning techniques have been employed to segment / cluster customers at scale.

## Getting Started

Software dependencies: Install Anaconda and create a virtual environment using the environment.yml file.

Reproduce the results:
* Geoclusterizer uses the pydoit dependency management framework to run tasks; however, the user can also run each task as a standalone py file
* The software is organized into the following tasks, which are listed in the ```dodo.py``` file
  * makedirs: Make directories if they don't exist 
  * download_acs: [Download American Community Survey (ACS) data](https://www.census.gov/programs-surveys/acs/data.html); script based on [this gist](https://gist.githubusercontent.com/erikbern/89c5f44bd1354854a8954fa2df04453d/raw/efd7b7c31d781a5cae9849be60ab86967bf7d2ed/american_community_survey_example.py)
  * parse_acs: Parse downloaded ACS data into standalone tables
  * scale_and_impute_data: Scale dataset and impute missing data
  * select_n_components: Select number of components to use
  * train_model: Train Gaussian Mixture model on scaled, imputed data using selected number of components
* To run all the tasks at once, simply cd into the repository and, if all packages have been installed correctly, type ```doit```
* Outputs are saved in the data/processed directory