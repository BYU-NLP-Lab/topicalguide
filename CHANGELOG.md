# Changelog

All notable changes to the Topical Guide project are documented in this file.

## [Unreleased] - 2024-11

### Major Updates

#### Django and Python Modernization
- **Upgraded from Django 1.7 to Django 4.2 LTS**
  - Updated all Django imports and API calls for compatibility
  - Migrated database models to Django 4.2 standards
  - Updated middleware configuration
  - Fixed deprecated features and removed obsolete code

- **Migrated from Python 2.7 to Python 3.10+**
  - Fixed all Python 2 to Python 3 compatibility issues
  - Updated import statements (absolute → relative imports)
  - Fixed iterator protocol (`next()` → `__next__()`)
  - Fixed `StopIteration` handling in generators (PEP 479)
  - Fixed `sorted()` function calls (removed deprecated `cmp` parameter)
  - Updated string handling and Unicode support
  - Fixed HTMLParser compatibility issues

#### State of the Union Dataset Enhancements
- **Expanded dataset from 1790-2010 to 1790-2025**
  - Added 15 new State of the Union addresses (2011-2025)
  - Includes speeches from Obama, Trump (both terms), and Biden administrations

- **Created `download_sotu.py` script**
  - Automated downloading of recent State of the Union addresses
  - Fetches speeches from American Presidency Project website
  - Properly formats metadata and content for Topical Guide
  - Handles all modern presidents (Obama through Trump 2025)

- **Updated dataset metadata**
  - Updated date range to reflect 1790-2025 coverage
  - Added source attribution for American Presidency Project (2011-2025)

#### Topic Modeling Improvements
- **Added stopwords support**
  - Integrated stopwords filtering into import workflow using existing stopwords files
  - Project includes multiple stopword lists: `stopwords/english_all.txt` (747 words), `stopwords/english_mallet.txt` (523 words), `stopwords/en.txt` (722 words)
  - Significantly improved topic quality and naming
  - Reduced token count from ~1.7M to ~892K with better semantic coherence

- **Support for multiple analyses**
  - Can run multiple topic modeling analyses on same dataset
  - Example: 20-topic and 100-topic analyses can coexist
  - Each analysis maintains independent topic names and metrics

#### Bug Fixes and Enhancements

- **Fixed document text display**
  - Changed default value of `public_documents` from `False` to `True`
  - Updated `import_tool/dataset/utilities.py` to make document text visible by default
  - Fixed database schema to properly display document content in web interface

- **Fixed all unit tests**
  - Updated `test_basic_tools.py` for Python 3 compatibility
  - Fixed HTMLParser initialization issues
  - Fixed HTML entity handling (`html.unescape()`)
  - Fixed subdocument creation whitespace handling
  - All 6 tests now passing

- **Fixed import script**
  - Updated `default_datasets/import_state_of_the_union.sh`
  - Fixed stopwords file path reference
  - Removed redundant `--public-documents` flag (now default)

- **Virtual environment naming**
  - Updated documentation to use `venv` instead of `ENV`
  - Consistent with modern Python best practices

#### Documentation Updates

- **Updated README.md**
  - Added Python 3.10+ requirement
  - Clarified Django 4.2 LTS usage
  - Updated installation instructions for modern Python
  - Added instructions for downloading recent SOTU addresses
  - Improved clarity and formatting
  - Added database migration step

- **Updated requirements.txt**
  - Django 4.2.17 (LTS)
  - Python 3.10+ compatible dependencies
  - Updated all packages to current versions
  - Added testing dependencies (pytest, pytest-django)

- **Enhanced code documentation**
  - Added comprehensive docstring to `download_sotu.py`
  - Updated docstrings in import utilities to reflect new defaults
  - Improved inline comments throughout codebase

### Technical Details

#### Import System Changes
- Relative imports throughout `import_tool/` package
- Fixed `GenericDataset` iterator protocol for Python 3
- Updated metric modules for Python 3 compatibility
- Fixed generator functions to comply with PEP 479

#### Database Changes
- SQLite database located at `working/tg.sqlite3`
- Migrations updated for Django 4.2
- `public_documents` field now defaults to `True`
- Support for multiple concurrent analyses per dataset

#### Testing
- 6/6 tests passing in `tests/import_tool/test_basic_tools.py`
- Fixed HTMLParser compatibility
- Fixed HTML entity replacement
- Fixed subdocument creation logic

### Dependencies
- Python: 3.10+
- Django: 4.2.17 (LTS)
- NLTK: 3.9.2
- NumPy: ≥2.0.0
- SciPy: ≥1.15.0
- Requests: (for download_sotu.py)
- BeautifulSoup4: (for download_sotu.py)
- See `requirements.txt` for complete list

### Breaking Changes
- **Python 2 is no longer supported** - Python 3.10+ required
- **Django 1.x is no longer supported** - Django 4.2 required
- Old database files may need migration to Django 4.2 format
- Import paths in custom code may need updating to relative imports

### Migration Guide

For users upgrading from the old Python 2/Django 1.7 version:

1. **Update Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Migrate database**
   ```bash
   python manage.py migrate
   ```

3. **Re-import datasets** (recommended)
   ```bash
   python tg.py import default_datasets/state_of_the_union/ --identifier state_of_the_union --public --verbose
   python tg.py analyze state_of_the_union --number-of-topics 20 --stopwords english_stopwords.txt --verbose
   ```

4. **Update custom code**
   - Convert any Python 2 syntax to Python 3
   - Update Django imports and API calls
   - Use relative imports in custom modules

### Known Issues
- None at this time

### Future Work
- Consider upgrading to Django 5.x when ready
- Add more comprehensive testing coverage
- Add automated CI/CD pipeline
- Consider containerization (Docker)
- Add more example datasets

---

## Previous Versions

This project was previously maintained with:
- Python 2.7
- Django 1.7
- State of the Union dataset (1790-2010 only)

For historical information, see the git commit history.
