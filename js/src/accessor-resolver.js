/**
 * Resolves Python accessor specifications into deck.gl-compatible JS functions.
 *
 * Accessor patterns:
 *   ["lon", "lat"]        -> d => [d.lon, d.lat]        (multi-column position)
 *   "column_name"         -> d => d.column_name          (single column)
 *   [255, 0, 0]           -> passed through as constant   (constant value)
 *   [[255,0,0],[0,255,0]] -> (d, {index}) => data[index] (per-row array)
 */

// Properties that are deck.gl accessor functions (get* pattern)
const ACCESSOR_PREFIXES = ["get"];

/**
 * Check if a property name is an accessor (starts with "get" and has a capital letter after).
 */
function isAccessorProp(key) {
  return key.length > 3 && key.startsWith("get") && key[3] === key[3].toUpperCase();
}

/**
 * Determine if an array looks like a list of column name strings.
 * e.g., ["lon", "lat"] -> true
 * e.g., [255, 0, 0] -> false
 */
function isColumnNameList(arr) {
  return arr.length > 0 && arr.every((item) => typeof item === "string");
}

/**
 * Determine if a value is a constant (not a column reference).
 * Numbers, booleans, and numeric arrays are constants.
 */
function isConstant(value) {
  if (typeof value === "number" || typeof value === "boolean") return true;
  if (Array.isArray(value) && value.length > 0 && value.length <= 4) {
    // Small numeric arrays like [255, 0, 0] or [255, 0, 0, 255] are RGBA constants
    return value.every((item) => typeof item === "number");
  }
  return false;
}

/**
 * Resolve accessor specs in a props object, mutating it in place.
 * Only processes properties that match the accessor naming pattern (get*).
 *
 * @param {Object} props - Layer props to resolve (mutated in place)
 * @param {Array|undefined} data - The layer's data array, used to verify column names
 */
export function resolveAccessors(props, data) {
  const dataLength = Array.isArray(data) ? data.length : undefined;
  // Get the set of valid column names from the first data row
  const dataColumns =
    Array.isArray(data) && data.length > 0 && typeof data[0] === "object" && data[0] !== null
      ? new Set(Object.keys(data[0]))
      : null;

  for (const key of Object.keys(props)) {
    if (!isAccessorProp(key)) continue;

    const value = props[key];

    if (typeof value === "function") {
      // Already a function, leave it
      continue;
    }

    if (typeof value === "string") {
      // Only convert to accessor if the string matches a column in the data.
      // Otherwise it's a constant string value (e.g., "middle", "center").
      if (dataColumns && dataColumns.has(value)) {
        const col = value;
        props[key] = (d) => d[col];
      }
      // If not a column name, leave as constant string
      continue;
    }

    if (Array.isArray(value)) {
      if (isColumnNameList(value)) {
        // Verify at least the first column exists in data before converting
        if (!dataColumns || value.every((col) => dataColumns.has(col))) {
          const cols = value;
          props[key] = (d) => cols.map((c) => d[c]);
          continue;
        }
        // If columns don't match data, leave as-is (could be a constant)
        continue;
      }

      if (isConstant(value)) {
        // Small numeric array constant like [255, 0, 0] — pass through
        continue;
      }

      // Per-row array: large array matching data length
      if (
        dataLength !== undefined &&
        value.length === dataLength &&
        !isConstant(value)
      ) {
        const arr = value;
        props[key] = (_d, { index }) => arr[index];
        continue;
      }

      // Otherwise leave as-is (could be a constant array)
    }

    // Numbers, booleans, null — pass through as constants
  }
}
