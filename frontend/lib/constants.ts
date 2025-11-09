
// Confidence level thresholds for AI recommendations
export const CONFIDENCE_THRESHOLDS = {
  HIGH: 0.8,
  MEDIUM: 0.6,
} as const;

// Default values
export const DEFAULTS = {
  TOP_K: 5,
  MAX_AI_SAMPLES: 100,
} as const;

// Error messages
export const ERROR_MESSAGES = {
  INVALID_JSON: 'Invalid JSON file. Please upload a valid JSON file.',
  MISSING_FILES: 'Please upload both files and select join columns',
  MISSING_TABLES: 'Please upload both tables first',
  MISSING_BRIDGE: 'Please create a bridge table first',
  NO_SELECTION: 'Please select at least one bridge table entry',
  AI_OLLAMA_NOT_RUNNING: '⚠️ Ollama is not running. Please start it with: ollama serve',
  AI_MODEL_NOT_FOUND: '⚠️ AI model not found. Please install it with: ollama pull mistral',
} as const;

// Join method display names
export const JOIN_METHOD_LABELS = {
  row: 'RS-JP (Row Method)',
  column: 'CS-JP-LP (Column Method)',
} as const;

