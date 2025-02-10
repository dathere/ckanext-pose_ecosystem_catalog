
# ckanext-pose_ecosystem_catalog

**CKAN Extension for the Pose Ecosystem Catalog Theme**

This repository contains the `ckanext-pose_theme` package – a CKAN extension that provides a suite of plugins to customize and enhance your CKAN instance for the Pose Ecosystem Catalog.

## Features

This extension includes the following CKAN plugins:

- **pose_custom_css**: Provides custom CSS styles.
- **pose_custom_homepage**: Customizes the homepage layout and content.
- **pose_custom_header**: Modifies the header with additional branding and functionality.
- **pose_custom_footer**: Enhances the footer area.
- **pose_custom_showcase**: Adds functionality to showcase datasets.
- **pose_custom_extension**: Adds functionality to add/display CKAN extensions.
- **pose_custom_site**: Adds functionality to add/display CKAN sites.

## Requirements

- **CKAN Versions**: 2.7, 2.9, and 2.10 are supported.
- **Python Versions**: Compatible with Python 2.7 and Python 3.6.


## Configuration Settings

To enable the plugins provided by this extension, add the following lines to your CKAN configuration file (e.g., `production.ini`):

```ini
ckan.plugins = pose_theme pose_custom_css pose_custom_homepage pose_custom_header pose_custom_footer pose_custom_showcase pose_custom_extension pose_custom_site

scheming.dataset_schemas = ckanext.pose_theme.pose_custom_showcase:showcase.yaml ckanext.pose_theme.pose_custom_extension:extension.yaml ckanext.pose_theme.pose_custom_site:site.yaml
scheming.presets = ckanext.scheming:presets.json
```

## Development Installation

To install `ckanext-pose_ecosystem_catalog` for development, follow these steps:

1. **Activate your CKAN virtual environment.**

2. **Clone the repository:**

   ```bash
   git clone https://github.com/dathere/ckanext-pose_ecosystem_catalog.git
   cd ckanext-pose_ecosystem_catalog
   ```

3. **Install the extension in development mode:**

   ```bash
   python setup.py develop
   ```

4. **Install the development requirements:**

   ```bash
   pip install -r dev-requirements.txt
   ```

## Running the Tests

You can run the tests using `pytest`. To run tests without warnings, execute:

```bash
pytest --disable-warnings ckanext.pose_theme
```

For a full test run that also generates coverage, pylint, and bandit reports, first install `tox` if it is not already available:

```bash
pip install tox
```

Then run:

```bash
tox --parallel 4
```

Reports will be generated in the `reports` folder.


