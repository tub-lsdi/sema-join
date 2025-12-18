import requests
import json
from pathlib import Path
from backend.config import settings


class AIRecommendationService:
    """AI-powered recommendation service for semantic joins using LLMs."""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        self.prompts_dir = Path(__file__).parent / "prompts"

    def _load_prompt_template(self, template_name: str) -> str:
        """Load a prompt template from file."""
        template_path = self.prompts_dir / template_name
        return template_path.read_text()

    def _build_prompt(self, table_r_schema: dict, table_s_schema: dict) -> str:
        """
        Build a prompt for the LLM to analyze column relationships.
        """
        template = self._load_prompt_template("column_recommendation.txt")
        return template.format(
            table_r_schema=json.dumps(table_r_schema, indent=2),
            table_s_schema=json.dumps(table_s_schema, indent=2),
        )

    def _call_ollama(self, prompt: str) -> dict:
        """
        Call the Ollama API to get LLM response.
        """
        try:
            # Call Ollama API
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",  # Request JSON format
                    "options": {
                        "num_ctx": 8192  # Increase context window to 8192 tokens
                    },
                },
                timeout=self.timeout,
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

                json_match = re.search(r"\{.*\}", llm_output, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return result
                else:
                    raise ValueError(
                        f"Could not parse JSON from LLM response: {llm_output}"
                    ) from e

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to call Ollama API at {self.base_url}: {str(e)}")
        except Exception as e:
            raise Exception(f"Error processing LLM response: {str(e)}")

    def recommend_column_joins(
        self, table_r: list[dict], table_s: list[dict], max_samples: int = 100
    ) -> dict:
        """
        Analyze two tables and recommend which columns to join.

        Args:
            table_r: First table as list of dictionaries
            table_s: Second table as list of dictionaries
            max_samples: Maximum number of sample values to include per column (default: 100)

        Returns:
            Dictionary containing recommended joins and analysis
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
                "null_count": rows_to_analyze - len(samples),
            }

        return schema

    def check_ollama_status(self) -> dict:
        """Check if Ollama is running and the model is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()

            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            model_available = any(self.model in name for name in model_names)

            return {
                "ollama_running": True,
                "model_requested": self.model,
                "model_available": model_available,
                "available_models": model_names,
            }
        except Exception as e:
            return {
                "ollama_running": False,
                "error": str(e),
                "recommendation": "Make sure Ollama is running. Try: 'ollama serve'",
            }

    def recommend_bridge_entries(self, bridge_entries: list[dict]) -> dict:
        """Get AI recommendations for which bridge entries to use."""
        grouped = {}
        for idx, entry in enumerate(bridge_entries):
            r_val = entry["r_val"]
            if r_val not in grouped:
                grouped[r_val] = []
            grouped[r_val].append(
                {"index": idx, "s_val": entry["s_val"], "npmi": entry["npmi"]}
            )

        template = self._load_prompt_template("bridge_recommendation.txt")
        prompt = template.format(bridge_candidates=json.dumps(grouped, indent=2))

        try:
            # Call Ollama
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "num_ctx": 8192  # Increase context window to 8192 tokens
                    },
                },
                timeout=self.timeout,
            )
            response.raise_for_status()

            response_text = response.json().get("response", "{}")
            ai_result = json.loads(response_text)

            recommendations = ai_result.get("recommendations", [])
            recommended_indices = []

            for rec in recommendations:
                r_val = rec["r_val"]
                recommended_s_val = rec["recommended_s_val"]

                found = False
                for entry_data in grouped.get(r_val, []):
                    entry_s_normalized = entry_data["s_val"].strip().lower()
                    recommended_s_normalized = recommended_s_val.strip().lower()

                    if entry_s_normalized == recommended_s_normalized:
                        recommended_indices.append(entry_data["index"])
                        found = True
                        break

                if not found:
                    # Fallback: Pick highest NPMI
                    entries_for_r = grouped.get(r_val, [])
                    if entries_for_r:
                        best_entry = max(entries_for_r, key=lambda e: e.get("npmi", 0))
                        recommended_indices.append(best_entry["index"])
                        print(
                            f"Warning: AI recommended '{recommended_s_val}' for '{r_val}' but it's not in the list. "
                            f"Falling back to best NPMI match: '{best_entry['s_val']}'"
                        )

            # Check if AI missed any r_vals
            all_r_vals = set(grouped.keys())
            recommended_r_vals = {r["r_val"] for r in recommendations}
            missed_r_vals = all_r_vals - recommended_r_vals

            if missed_r_vals:
                print(
                    f"Warning: AI didn't recommend matches for: {missed_r_vals}. Adding best NPMI matches."
                )
                for r_val in missed_r_vals:
                    entries_for_r = grouped.get(r_val, [])
                    if entries_for_r:
                        best_entry = max(entries_for_r, key=lambda e: e.get("npmi", 0))
                        recommended_indices.append(best_entry["index"])
                        recommendations.append(
                            {
                                "r_val": r_val,
                                "recommended_s_val": best_entry["s_val"],
                                "reason": "AI didn't provide recommendation, using highest NPMI",
                                "confidence": 0.5,
                            }
                        )

            return {
                "recommendations": recommendations,
                "analysis": ai_result.get("analysis", "AI analysis complete"),
                "recommended_indices": recommended_indices,
                "model_used": self.model,
            }

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response as JSON: {e}")
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to communicate with Ollama: {e}")
