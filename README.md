# Country Region Normalization

A Python CLI tool that normalizes country names in CSV files and adds corresponding region information.

The tool uses fuzzy matching, alias mapping, and intelligent column detection to standardize country data across datasets.

## Usage


```bash
python normalize.py input.csv
python normalize.py data/survey_responses.csv
```

**Output**: Creates `input_out.csv` with:
- Normalized country names
- Added region columns (e.g., `Country_region`)
- Same structure as original file


## Configuration Files

`country_region.csv`: maps canonical country names to regions

```csv
country,region
United States,North America
Germany,Europe
South Korea,Asia
Brazil,South America
```


`alias_to_canonical.csv`: maps various country name formats to standardized names

```csv
alias,country_normalized
usa,United States
deutschland,Germany
대한민국,South Korea
brasil,Brazil
```


## How It Works

1. **Column Detection**: Identifies country columns by:
   - Keyword matching (`country`, `nation`, `location`, etc.)
   - Content analysis (checks if >30% of values look like countries)

2. **Normalization Process**:
   - Text cleaning (lowercasing, removing punctuation, etc.)
   - Alias lookup (exact and no-spaces matching)
   - First-word fallback for compound entries
   - Fuzzy matching (85% similarity threshold)

3. **Output Generation**:
   - Replaces country column with normalized values
   - Adds corresponding region column
   - Preserves all other data unchanged

## Adding New Mappings

To improve normalization, add entries to `alias_to_canonical.csv`:

```csv
# Add common typos
amrica,United States
germnay,Germany

# Add local language names
italien,Italy
japon,Japan

# Add abbreviations
uk,United Kingdom
uae,United Arab Emirates
```

## Customization

### Modify Column Detection
Edit the `detect_country_columns()` function to change detection logic:

```python
country_keywords = ['country', 'nation', 'pais', 'land', 'location', 'origin']
```

### Adjust Fuzzy Matching
Change the similarity threshold in `normalize_country()`:

```python
matches = difflib.get_close_matches(
    no_space,
    [...],
    n=1,
    cutoff=0.85,  # Adjust this value (0.0-1.0)
)
```

### Add Custom Cleaning Rules
Modify the `clean_text()` function:

```python
def clean_text(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).lower().strip()
    s = re.sub(r"^the\s+", "", s)  # Remove "the" prefix
    s = re.sub(r"\b(republic|rep|of)\b", " ", s)  # Remove common words
    # Add your own rules here
    return s
```


## Contributing

1. Add new aliases to `alias_to_canonical.csv`
2. Test with your datasets
3. Submit pull requests with improvements

