/**
 * codec.ts — TypeScript port of the NB-1 semantic compression codec
 *
 * Encodes common patterns into short symbols to reduce token count.
 * Same codebook as the Python version.
 */

// NB-1 Codebook: frequent patterns -> short codes
const CODEBOOK: [string, string][] = [
  // French patterns
  ["c'est", "©"],
  ["qu'est-ce que", "⁇"],
  ["je suis", "ĵ"],
  ["il y a", "∃"],
  ["est-ce que", "⁈"],
  ["parce que", "∵"],
  ["peut-être", "℘"],
  ["quelque chose", "ℚ"],
  ["beaucoup", "∞b"],
  ["toujours", "∀t"],
  ["maintenant", "⊕m"],
  ["cependant", "⊖c"],
  ["également", "≡e"],
  ["probablement", "≈p"],
  ["exactement", "≡x"],
  ["vraiment", "✓v"],
  ["important", "‼i"],
  ["comprendre", "⊂c"],
  ["différent", "≠d"],
  ["ensemble", "∪e"],
  ["plusieurs", "∑p"],

  // English patterns
  ["because", "∵"],
  ["something", "ℚ"],
  ["everything", "∀e"],
  ["understand", "⊂u"],
  ["different", "≠d"],
  ["important", "‼i"],
  ["probably", "≈p"],
  ["together", "∪t"],
  ["actually", "⊕a"],
  ["something", "ℚs"],

  // Technical
  ["function", "ƒ"],
  ["return", "⏎"],
  ["const ", "κ "],
  ["interface", "ℐ"],
  ["export", "⇒"],
  ["import", "⇐"],
  ["async", "⊛"],
  ["await", "⊘"],

  // Conversational fillers (high compression value)
  ["en fait", "∴"],
  ["du coup", "⇒d"],
  ["en même temps", "∥"],
  ["par exemple", "eg"],
  ["c'est-à-dire", "ie"],
  ["tout à fait", "✓✓"],
];

/**
 * Encode text using NB-1 codebook
 */
export function encode(text: string): string {
  let encoded = text;
  for (const [pattern, code] of CODEBOOK) {
    encoded = encoded.split(pattern).join(code);
  }
  return encoded;
}

/**
 * Decode NB-1 encoded text back to original
 */
export function decode(encoded: string): string {
  let decoded = encoded;
  // Decode in reverse order to handle overlapping patterns
  for (let i = CODEBOOK.length - 1; i >= 0; i--) {
    const [pattern, code] = CODEBOOK[i];
    decoded = decoded.split(code).join(pattern);
  }
  return decoded;
}

/**
 * Calculate compression ratio
 */
export function compressionRatio(original: string): {
  originalLength: number;
  encodedLength: number;
  ratio: number;
  savings: string;
} {
  const encoded = encode(original);
  const originalLength = original.length;
  const encodedLength = encoded.length;
  const ratio = encodedLength / originalLength;
  const savings = ((1 - ratio) * 100).toFixed(1);

  return {
    originalLength,
    encodedLength,
    ratio,
    savings: `${savings}%`,
  };
}

/**
 * Get codebook size for UI display
 */
export function codebookSize(): number {
  return CODEBOOK.length;
}
