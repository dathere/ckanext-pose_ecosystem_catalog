# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

`ckanext-pose_ecosystem_catalog` is a CKAN extension that provides a comprehensive theming and customization suite for the Pose Ecosystem Catalog. It extends CKAN to support showcasing datasets, extensions, and CKAN sites through custom dataset types and enhanced UI components.

## Development Commands

### Installation
```bash
# Activate CKAN virtual environment first
python setup.py develop
pip install -r requirements.txt
pip install -r dev-requirements.txt
```

### Testing
```bash
# Run tests without warnings
pytest --disable-warnings ckanext.pose_theme

# Run tests with coverage
pytest --disable-warnings --cov ckanext.pose_theme

# Run full test suite with coverage, pylint, and bandit reports
tox --parallel 4

# Reports are generated in the `reports/` folder
```

### Configuration
Add these plugins to your CKAN configuration file (e.g., `production.ini`):
```ini
ckan.plugins = pose_theme pose_custom_css pose_custom_homepage pose_custom_header pose_custom_footer pose_custom_showcase
scheming.dataset_schemas = ckanext.pose_theme.pose_custom_showcase:showcase.yaml ckanext.pose_theme.custom_themes.pose_theme:extension.yaml ckanext.pose_theme.custom_themes.pose_theme:site.yaml
scheming.presets = ckanext.scheming:presets.json
```

## Architecture

### Plugin Structure
The extension is organized as a collection of specialized CKAN plugins:

1. **pose_theme** (`ckanext/pose_theme/custom_themes/pose_theme/`): Core theme plugin providing base theming, blueprints, CLI commands, and template helpers. Implements custom facets for different dataset types.

2. **pose_custom_css**: Allows administrators to inject custom CSS styles through the admin interface.

3. **pose_custom_homepage**: Provides customizable homepage layouts with support for multiple layout templates.

4. **pose_custom_header**: Customizes the header with additional branding and navigation.

5. **pose_custom_footer**: Enhances footer with CKEditor integration for rich content editing.

6. **pose_custom_showcase**: Implements a custom "showcase" dataset type using ckanext-scheming for displaying applications/use cases.

### Custom Dataset Types
The extension uses ckanext-scheming to define three custom dataset types with YAML schemas:

- **showcase** (`pose_custom_showcase/showcase.yaml`): For showcasing applications/use cases of datasets
- **extension** (`custom_themes/pose_theme/extension.yaml`): For cataloging CKAN extensions with GitHub metadata
- **site** (`custom_themes/pose_theme/site.yaml`): For registering CKAN instances with location, technical details, and statistics

Each schema defines custom fields, validators, and form snippets specific to that dataset type.

### Key Components

**Base Helpers** (`ckanext/pose_theme/base/helpers.py`):
- Central location for template helper functions
- Provides data fetching functions: `dataset_count()`, `showcases()`, `extensions()`, `sites()`, `groups()`, `organization()`, etc.
- Featured and recent item helpers: `featured_extensions()`, `featured_sites()`, `recent_extensions()`, etc.
- Utility functions for data dictionary, tracking, and custom naming

**Blueprints** (`custom_themes/pose_theme/blueprint.py`):
- Flask blueprints for custom routes
- `datastore_dictionary` blueprint for dictionary downloads
- Contact form routes via `ckanext.pose_theme.routes.contact`

**Plugin Implementations**:
- Each plugin follows the pattern: `plugin.py` contains the main plugin class implementing CKAN interfaces
- Separate Flask and Pylons plugin implementations for compatibility (`flask_plugin.py`, `pylons_plugin.py`)
- Plugin classes implement interfaces like `IConfigurer`, `ITemplateHelpers`, `IBlueprint`, `IFacets`, `IPackageController`, `IActions`

### Asset Management
- Each plugin has its own `assets/` directory with CSS, JS, and vendor libraries
- Uses `webassets.yml` and `resource.config` for asset bundling
- SCSS compilation for custom themes (see `custom_themes/pose_theme/assets/scss/`)
- Vendor libraries include CKEditor (for rich text editing), Slick carousel, and Spectrum color picker

### Template Structure
- Templates follow CKAN's template inheritance pattern
- Custom templates in each plugin's `templates/` directory override base CKAN templates
- Jinja2 template snippets in `templates/snippets/` for reusable components
- Scheming-specific templates in `templates/scheming/package/` for custom dataset type rendering

### Search and Filtering
The `pose_custom_showcase` plugin modifies dataset search behavior:
- `before_dataset_search()` filters dataset listings to exclude non-dataset types
- Custom facet configuration per dataset type via `dataset_facets()`
- Search queries preserve all dataset types while listings show only "dataset" type

## Python Version Compatibility
Supports Python 2.7 and Python 3.6 (legacy CKAN versions). Uses `six` library for Python 2/3 compatibility.

## Dependencies
- **bleach**: HTML sanitization
- **tinycss2**: CSS parsing
- **wcag_contrast_ratio**: Accessibility color contrast checking
- **webcolors**: Color manipulation
- **pytest-ckan**: CKAN-specific testing utilities

## Code Quality
- Test coverage requirement: 85% (configured in tox.ini)
- Bandit for security analysis
- Pylint for code quality with HTML reports
- Tests located in `ckanext/pose_theme/tests/`
