# LLM-Based Topic Naming

The Topical Guide now supports using Large Language Models (LLMs) to generate human-readable topic names automatically. This feature uses OpenAI's GPT models to analyze topic word distributions and generate intuitive topic labels.

## Setup

### 1. Install OpenAI Package

```bash
pip install openai
```

Or install all optional dependencies:

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Set your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY='your-api-key-here'
```

Or in your shell configuration file (~/.bashrc, ~/.zshrc, etc.):

```bash
echo "export OPENAI_API_KEY='your-api-key-here'" >> ~/.bashrc
source ~/.bashrc
```

## Usage

### Option 1: Command Line with Custom Script

Create a Python script to run LLM-based topic naming on an existing analysis:

```python
#!/usr/bin/env python
import os
import django

# Setup Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'topicalguide.settings'
django.setup()

from import_tool.analysis.name_schemes.llm_namer import LLMTopicNamer
from import_tool.analysis.utilities import create_topic_names
from visualize.models import Analysis

# Get your analysis
dataset_name = 'state_of_the_union'
analysis_name = 'lda20topics'
analysis_db = Analysis.objects.get(dataset__name=dataset_name, name=analysis_name)

# Create LLM topic namer
llm_namer = LLMTopicNamer(
    n_words=10,          # Number of top words to consider
    n_docs=3,            # Number of sample documents to include
    model="gpt-4o-mini", # OpenAI model (gpt-4o-mini is fast and cheap)
    max_label_length=50, # Maximum characters in generated label
    fallback_to_topn=True # Fall back to simple naming on errors
)

# Generate topic names
create_topic_names('default', analysis_db, [llm_namer], verbose=True)

print(f"LLM-based topic names generated for {analysis_name}!")
```

Save as `generate_llm_names.py` and run:

```bash
python generate_llm_names.py
```

### Option 2: Programmatic Usage

You can also integrate LLM naming into your analysis workflow:

```python
from import_tool.analysis.name_schemes.llm_namer import LLMTopicNamer
from import_tool.analysis.name_schemes.top_n import TopNTopicNamer
from import_tool.analysis.name_schemes.tf_itf import TfitfTopicNamer

# When running analysis, include LLM namer
topic_namers = [
    TopNTopicNamer(3),      # Traditional top-3 words
    TfitfTopicNamer(3),     # TF-ITF based naming
    LLMTopicNamer(          # LLM-based naming
        n_words=10,
        n_docs=3,
        model="gpt-4o-mini"
    )
]

# Pass to run_analysis or create_topic_names
create_topic_names(database_id, analysis_db, topic_namers, verbose=True)
```

## Configuration Options

### LLMTopicNamer Parameters

- **n_words** (int, default=10): Number of top words from the topic to include in the prompt
- **n_docs** (int, default=3): Number of sample document excerpts to include (set to 0 to disable)
- **model** (str, default="gpt-4o-mini"): OpenAI model to use
  - `gpt-4o-mini`: Fast, cheap, good quality
  - `gpt-4o`: Higher quality, more expensive
  - `gpt-3.5-turbo`: Cheaper, faster, lower quality
- **api_key** (str, optional): OpenAI API key (defaults to OPENAI_API_KEY env var)
- **max_label_length** (int, default=50): Maximum characters in generated labels
- **fallback_to_topn** (bool, default=True): Use simple Top-3 naming if API call fails

## Cost Considerations

### Pricing (as of 2024)

- **gpt-4o-mini**: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- **gpt-4o**: ~$2.50 per 1M input tokens, ~$10 per 1M output tokens

### Cost Example

For a 20-topic analysis:
- Input: ~200-400 tokens per topic (words + context)
- Output: ~20-50 tokens per topic (topic name)
- Total: ~8,000 input tokens + ~400 output tokens for 20 topics
- **Cost with gpt-4o-mini**: ~$0.001 (less than a cent)

For a 100-topic analysis:
- **Cost with gpt-4o-mini**: ~$0.005 (half a cent)

LLM-based naming is very affordable, especially with gpt-4o-mini.

## Viewing Generated Names

After generating LLM-based topic names, you can view them in the web interface:

1. Start the server:
   ```bash
   python manage.py runserver
   ```

2. Navigate to http://localhost:8000/

3. Select your dataset and analysis

4. Topic names will be displayed with the "LLM-10words" naming scheme

You can switch between different naming schemes (Top3, TF-ITF Top 3, LLM-10words) in the interface.

## Troubleshooting

### "OpenAI API key not found"

Make sure you've set the environment variable:
```bash
export OPENAI_API_KEY='your-key-here'
```

Verify it's set:
```bash
echo $OPENAI_API_KEY
```

### "openai package not found"

Install the OpenAI package:
```bash
pip install openai
```

### API Rate Limits

If you hit rate limits with many topics:
- Add delays between API calls
- Use gpt-4o-mini (higher rate limits)
- Batch process topics in smaller groups

### Fallback Behavior

If `fallback_to_topn=True` (default), the system will automatically use simple Top-3 naming for any topics that fail LLM generation. This ensures robustness even with API issues.

## Examples

### State of the Union Dataset

```python
# Generate LLM names for a 20-topic State of the Union analysis
llm_namer = LLMTopicNamer(n_words=12, n_docs=5, model="gpt-4o-mini")
create_topic_names('default', analysis_db, [llm_namer], verbose=True)
```

Example output:
- Instead of: "war military troops"
- LLM generates: "Military Operations and National Defense"

- Instead of: "economy jobs workers"
- LLM generates: "Economic Growth and Employment"

## Advanced: Custom Models

You can specify different OpenAI models:

```python
# Use GPT-4o for higher quality (more expensive)
llm_namer = LLMTopicNamer(model="gpt-4o")

# Use GPT-3.5 for faster, cheaper naming
llm_namer = LLMTopicNamer(model="gpt-3.5-turbo")
```

## Integration with Analysis Pipeline

To automatically generate LLM names during analysis, modify your analysis script:

```bash
# After running analysis
python tg.py analyze state_of_the_union --number-of-topics 20 --stopwords stopwords/english_all.txt

# Then run LLM naming
python generate_llm_names.py
```

Or create a combined script that does both.
