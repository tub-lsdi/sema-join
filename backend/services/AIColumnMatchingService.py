import requests
import json
from backend.config import settings


class AIColumnMatchingService:
    """
    This service analyzes two table schemas and uses an LLM to
    recommend which columns from each table should be joined together based on
    their names, sample values, and semantic meaning.
    """

    def __init__(self):
        """
        Initialize the AI Column Matching Service.

        Configuration is loaded from .env file via settings.
        If not set in .env, uses defaults from config.py:
        - OLLAMA_BASE_URL: http://localhost:11434
        - OLLAMA_MODEL: mistral
        - OLLAMA_TIMEOUT: 60
        """
        self.base_url = settings.OLLAMA_BASE_URL.rstrip('/')
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT

    def _build_prompt(
        self,
        table_r_schema: dict,
        table_s_schema: dict
    ) -> str:
        """
        Build a prompt for the LLM to analyze column relationships.

        Args:
            table_r_schema: Schema of first table with columns and sample values
            table_s_schema: Schema of second table with columns and sample values

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a data analyst expert specializing in database joins. 
Analyze the following two table schemas and recommend which columns should be joined together.

I'm providing you with extensive data from both tables (up to 100 rows per table) so you can make accurate recommendations.

TABLE R SCHEMA:
{json.dumps(table_r_schema, indent=2)}

TABLE S SCHEMA:
{json.dumps(table_s_schema, indent=2)}

Your task is to find SEMANTIC RELATIONSHIPS between columns by analyzing the actual DATA VALUES, not just column names.

CRITICAL INSTRUCTIONS:
1. **Focus on VALUE-BASED relationships**: Look at the actual sample values and find where:
   - Codes/abbreviations in one column match full names/descriptions in another column
   - Example: "DE" in Table R → "Germany" in Table S (country code → country name)
   - Example: "AAPL" → "Apple Inc." (ticker → company name)
   - Example: "NYC" → "New York City" (abbreviation → full name)

2. **Cross-column analysis is KEY**: The most useful joins are often between DIFFERENT column names:
   - "code" column → "entity" column (code values match entity names)
   - "id" column → "name" column (IDs reference names)
   - "sku" column → "product_name" column (SKUs reference products)

3. **De-prioritize obvious matches**: Columns with the SAME NAME are often obvious and less interesting:
   - If both tables have "code", "id", "name" - these are obvious matches
   - Focus on SEMANTIC relationships that aren't immediately obvious from column names

4. **Look for these patterns in the VALUES**:
   - Country/region codes (US, DE, FR) → Country/region names (United States, Germany, France)
   - Short codes/abbreviations → Full descriptions
   - IDs/SKUs → Entity names
   - Acronyms → Full names

5. **Analyze the actual data**:
   - Read through ALL sample values carefully
   - Check if short values in one column are abbreviations of longer values in another
   - Look for semantic matches: "DE" could match "Germany" or "Delaware" - context matters!

6. **Prioritize enriching joins**: Recommend joins that would ADD NEW INFORMATION:
   - Joining a code column to an entity name column adds context
   - Joining identical columns adds less value

Provide your answer in the following JSON format (respond ONLY with valid JSON, no additional text):
{{
  "recommended_joins": [
    {{
      "r_column": "column_name_from_R",
      "s_column": "column_name_from_S",
      "confidence": 0.95,
      "reason": "Specific explanation citing actual data values (e.g., 'DE' in r_column matches 'Germany' in s_column)"
    }}
  ],
  "analysis": "Analysis explaining the semantic relationships found between the actual data values"
}}

IMPORTANT:
- Confidence should be based on how well the VALUES match, not just column names
- List multiple recommendations if appropriate, ranked by confidence
- ALWAYS cite specific data values in your reasons (e.g., "DE matches Germany")
- Focus on semantic meaning, not just syntactic similarity
"""
        return prompt

    def _call_ollama(self, prompt: str) -> dict:
        """
        Call the Ollama API to get LLM response.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            Parsed JSON response from the LLM

        Raises:
            Exception: If API call fails or response cannot be parsed
        """
        try:
            # Call Ollama API
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"  # Request JSON format
                },
                timeout=self.timeout
            )
            response.raise_for_status()

            # Parse response
            ollama_response = response.json()
            llm_output = ollama_response.get("response", "")

            # Parse the JSON from LLM
            try:
                result = json.loads(llm_output)
                return result
            except json.JSONDecodeError as e:
                # If JSON parsing fails, try to extract JSON from the text
                # Sometimes LLMs add extra text around the JSON
                import re
                json_match = re.search(r'\{.*\}', llm_output, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return result
                else:
                    raise ValueError(
                        f"Could not parse JSON from LLM response: {llm_output}") from e

        except requests.exceptions.RequestException as e:
            raise Exception(
                f"Failed to call Ollama API at {self.base_url}: {str(e)}")
        except Exception as e:
            raise Exception(f"Error processing LLM response: {str(e)}")

    def recommend_column_joins(
        self,
        table_r: list[dict],
        table_s: list[dict],
        max_samples: int = 100
    ) -> dict:
        """
        Analyze two tables and recommend which columns to join.

        Args:
            table_r: First table as list of dictionaries
            table_s: Second table as list of dictionaries
            max_samples: Maximum number of sample values to include per column (default: 100)

        Returns:
            Dictionary containing recommended joins and analysis

        Raises:
            ValueError: If tables are empty or invalid
            Exception: If LLM call fails
        """
        # Validation
        if not table_r or not table_s:
            raise ValueError("Both tables must contain at least one row")

        # Extract schema with sample values (using first N rows)
        table_r_schema = self._extract_schema(table_r, max_samples)
        table_s_schema = self._extract_schema(table_s, max_samples)

        # Build prompt
        prompt = self._build_prompt(table_r_schema, table_s_schema)

        # Call LLM
        result = self._call_ollama(prompt)

        # Add metadata
        result["model_used"] = self.model
        result["table_r_columns"] = list(table_r_schema.keys())
        result["table_s_columns"] = list(table_s_schema.keys())
        result["rows_analyzed_r"] = min(len(table_r), max_samples)
        result["rows_analyzed_s"] = min(len(table_s), max_samples)

        return result

    def _extract_schema(self, table: list[dict], max_samples: int) -> dict:
        """
        Extract schema information from a table with sample values.

        Args:
            table: Table as list of dictionaries
            max_samples: Maximum number of rows to analyze

        Returns:
            Dictionary mapping column names to their metadata and sample values
        """
        if not table:
            return {}

        schema = {}
        first_row = table[0]
        rows_to_analyze = min(len(table), max_samples)

        for column in first_row.keys():
            # Get sample values from first N rows
            samples = []
            unique_values = set()

            for row in table[:rows_to_analyze]:
                if column in row and row[column] is not None:
                    value_str = str(row[column])
                    samples.append(value_str)
                    unique_values.add(value_str)

            # Infer data type from first non-null value
            dtype = "unknown"
            for row in table[:rows_to_analyze]:
                if column in row and row[column] is not None:
                    dtype = type(row[column]).__name__
                    break

            # Include all samples for better AI analysis
            schema[column] = {
                "type": dtype,
                "sample_values": samples,  # All values from analyzed rows
                "unique_count": len(unique_values),
                "total_samples": len(samples),
                "null_count": rows_to_analyze - len(samples)
            }

        return schema

    def check_ollama_status(self) -> dict:
        """
        Check if Ollama is running and the model is available.

        Returns:
            Dictionary with status information
        """
        try:
            # Check if Ollama is running
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            response.raise_for_status()

            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]

            model_available = any(self.model in name for name in model_names)

            return {
                "ollama_running": True,
                "model_requested": self.model,
                "model_available": model_available,
                "available_models": model_names
            }
        except Exception as e:
            return {
                "ollama_running": False,
                "error": str(e),
                "suggestion": "Make sure Ollama is running. Try: 'ollama serve'"
            }

    def suggest_best_bridge_entries(self, bridge_entries: list[dict]) -> dict:
        """
        Use LLM to select the best match for each R value from RS-JP top-k results.

        Args:
            bridge_entries: List of dicts with r_val, s_val, npmi fields

        Returns:
            Dictionary with selections, analysis, selected_indices, and model_used
        """
        # Group entries by r_val
        grouped = {}
        for idx, entry in enumerate(bridge_entries):
            r_val = entry["r_val"]
            if r_val not in grouped:
                grouped[r_val] = []
            grouped[r_val].append({
                "index": idx,
                "s_val": entry["s_val"],
                "npmi": entry["npmi"]
            })

        # Build prompt
        prompt = f"""You are a data expert analyzing bridge table matches from a semantic join algorithm.

For each value from Table R, the algorithm found multiple candidate matches in Table S based on co-occurrence statistics (NPMI scores).

Your task: Select the BEST match for each R value.

BRIDGE TABLE CANDIDATES:
{json.dumps(grouped, indent=2)}

INSTRUCTIONS:
1. For each R value, analyze ALL candidate S values
2. Consider both the NPMI score AND the semantic meaning
3. Higher NPMI = stronger statistical co-occurrence in corpus
4. But also use common sense about which match makes most semantic sense
5. Select the ONE best S value for each R value

CRITICAL RULES:
- The highest NPMI is usually correct, but not always
- Look for standard codes vs non-standard codes (e.g., "DE" is better than "GE" for Germany - ISO standard)
- Prefer well-known standards (ISO, FIPS, etc.)
- Explain WHY you picked each one
- **IMPORTANT**: You MUST provide a selection for EVERY r_val in the input
- **IMPORTANT**: The "selected_s_val" MUST be EXACTLY one of the s_val options shown above (copy it exactly, including case and spacing)

OUTPUT FORMAT (JSON):
{{
  "selections": [
    {{
      "r_val": "<EXACTLY as shown above>",
      "selected_s_val": "<EXACTLY one of the s_val options, copied verbatim>",
      "reason": "<why this one>",
      "confidence": 0.95
    }}
  ],
  "analysis": "<overall reasoning>"
}}

Example: If you see {{"s_val": "united kingdom", "npmi": 0.21}}, you MUST write "selected_s_val": "united kingdom" (not "United Kingdom" or "UK")

Respond with ONLY valid JSON, no markdown, no explanation outside the JSON."""

        try:
            # Call Ollama
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=self.timeout
            )
            response.raise_for_status()

            # Parse response
            response_text = response.json().get("response", "{}")
            ai_result = json.loads(response_text)

            # Map selections back to indices
            selections = ai_result.get("selections", [])
            selected_indices = []
            missing_selections = []

            for selection in selections:
                r_val = selection["r_val"]
                selected_s_val = selection["selected_s_val"]

                # Find the index of this (r_val, s_val) pair
                # Use case-insensitive comparison with whitespace stripping
                found = False
                for entry_data in grouped.get(r_val, []):
                    # Normalize both values for comparison
                    entry_s_normalized = entry_data["s_val"].strip().lower()
                    selected_s_normalized = selected_s_val.strip().lower()

                    if entry_s_normalized == selected_s_normalized:
                        selected_indices.append(entry_data["index"])
                        found = True
                        break

                # If AI suggested a value not in the list, log it and fall back to best NPMI
                if not found:
                    missing_selections.append({
                        "r_val": r_val,
                        "suggested_s_val": selected_s_val,
                        "available_s_vals": [e["s_val"] for e in grouped.get(r_val, [])]
                    })

                    # Fallback: Pick the one with highest NPMI for this r_val
                    entries_for_r = grouped.get(r_val, [])
                    if entries_for_r:
                        best_entry = max(
                            entries_for_r, key=lambda e: e.get("npmi", 0))
                        selected_indices.append(best_entry["index"])
                        print(f"Warning: AI suggested '{selected_s_val}' for '{r_val}' but it's not in the list. "
                              f"Falling back to best NPMI match: '{best_entry['s_val']}'")

            # Check if AI missed any r_vals - add them with highest NPMI
            all_r_vals = set(grouped.keys())
            suggested_r_vals = {s["r_val"] for s in selections}
            missed_r_vals = all_r_vals - suggested_r_vals

            if missed_r_vals:
                print(
                    f"Warning: AI didn't suggest matches for: {missed_r_vals}. Adding best NPMI matches.")
                for r_val in missed_r_vals:
                    entries_for_r = grouped.get(r_val, [])
                    if entries_for_r:
                        best_entry = max(
                            entries_for_r, key=lambda e: e.get("npmi", 0))
                        selected_indices.append(best_entry["index"])
                        selections.append({
                            "r_val": r_val,
                            "selected_s_val": best_entry["s_val"],
                            "reason": "AI didn't provide suggestion, using highest NPMI",
                            "confidence": 0.5
                        })

            return {
                "selections": selections,
                "analysis": ai_result.get("analysis", "AI analysis complete"),
                "selected_indices": selected_indices,
                "model_used": self.model
            }

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response as JSON: {e}")
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to communicate with Ollama: {e}")
