# Files Requiring Changes for Exchanges API Update

## Summary
The `/exchanges` API endpoint will be updated to accept a `product_type` query parameter and return exchanges filtered by product type from `config.json`'s `exchange_map` setting.

---

## Backend Files (Python/Flask)

### 1. `server/controllers/instrument_controller.py`
**Current State:**
- `get_all_exchanges()` endpoint currently hardcodes `product_type='stock'`
- Returns exchanges from `get_service('stock').get_all_exchanges()`

**Proposed Changes:**
- Add `product_type` query parameter (optional, defaults to 'stock')
- Validate `product_type` parameter (must be 'stock', 'option', or 'future')
- Use `ConfigService.get_csv_exchange_map(product_type)` to get exchanges from config.json
- Extract exchange codes from the exchange_map dictionary (keys)
- Return simple list of exchange codes: `["XHKG", "XNSE", "XTKS", ...]`
- Update Swagger documentation with new parameter

**Code Changes:**
```python
@instrument_api.route('/exchanges', methods=['GET'])
def get_all_exchanges():
    """
    Get all configured exchanges for a specific product type
    ---
    tags:
      - Instruments
    parameters:
      - name: product_type
        in: query
        type: string
        required: false
        default: stock
        enum:
          - stock
          - option
          - future
        description: Product type to filter exchanges
    responses:
      200:
        description: List of exchange codes for the specified product type
    """
    product_type = request.args.get('product_type', 'stock').lower()
    
    # Validate product_type
    if product_type not in ['stock', 'option', 'future']:
        return jsonify({"error": f"Invalid product_type '{product_type}'. Must be 'stock', 'option', or 'future'."}), 400
    
    try:
        config_service = ConfigService()
        exchange_map = config_service.get_csv_exchange_map(product_type)
        
        if not exchange_map:
            return jsonify({"error": f"No exchanges found for product_type '{product_type}'"}), 404
        
        # Extract exchange codes (keys) from exchange_map
        exchanges = list(exchange_map.keys())
        return jsonify(exchanges)
    except Exception as e:
        logger.error(f"Error retrieving exchanges: {e}", exc_info=True)
        return jsonify({"error": f"Error retrieving exchanges: {str(e)}"}), 500
```

---

## Frontend Files (Svelte/TypeScript)

### 2. `client/src/lib/services/api.ts`
**Current State:**
- `getExchanges()` function calls `/api/v1/instruments/exchanges` without any parameters
- Handles various response formats (array of objects, array of strings, nested objects)

**Proposed Changes:**
- Add optional `productType` parameter to `getExchanges()` function (defaults to 'stock')
- Append `?product_type={productType}` query parameter to the API URL
- Simplify response handling since API will now always return a simple array of strings
- Update function signature and JSDoc comments

**Code Changes:**
```typescript
export async function getExchanges(productType: string = 'stock'): Promise<Exchange[]> {
    const url = `${API_BASE_URL}${API_ENDPOINTS.exchanges}?product_type=${productType}`;
    const response = await fetch(url);
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    // API now returns simple array of strings: ["XHKG", "XNSE", ...]
    if (Array.isArray(result)) {
        return result.map((item: string) => ({
            value: item,
            label: item
        }));
    }
    
    return [];
}
```

---

### 3. `client/src/lib/stores/exchanges.svelte.ts`
**Current State:**
- `fetchExchanges()` function doesn't accept any parameters
- Uses module-level state that caches exchanges globally (not per product type)
- Single `exchanges` array shared across all components

**Proposed Changes:**
- Add optional `productType` parameter to `fetchExchanges()` (defaults to 'stock')
- Pass `productType` to `getExchanges()` call
- **Option A (Simple):** Keep single cache, refresh when productType changes
- **Option B (Advanced):** Cache exchanges per product type (recommended for better UX)

**Code Changes (Option B - Recommended):**
```typescript
// Cache exchanges per product type
let exchangesCache = $state<Record<string, Exchange[]>>({});
let loadingCache = $state<Record<string, boolean>>({});
let initializedCache = $state<Record<string, boolean>>({});

export async function fetchExchanges(productType: string = 'stock'): Promise<void> {
    // Return cached data if already initialized for this product type
    if (initializedCache[productType]) {
        return;
    }

    // Prevent concurrent fetches for same product type
    if (loadingCache[productType]) {
        return;
    }

    loadingCache[productType] = true;
    error = null;

    try {
        const fetchedExchanges = await getExchanges(productType);
        exchangesCache[productType] = fetchedExchanges;
        initializedCache[productType] = true;
    } catch (err) {
        console.error(`Failed to fetch exchanges for ${productType}:`, err);
        error = err instanceof Error ? err.message : 'Failed to fetch exchanges';
        exchangesCache[productType] = [];
        initializedCache[productType] = true;
    } finally {
        loadingCache[productType] = false;
    }
}

// Update store to get exchanges for specific product type
export const exchangesStore = {
    getExchanges(productType: string = 'stock') {
        return exchangesCache[productType] || [];
    },
    isLoading(productType: string = 'stock') {
        return loadingCache[productType] || false;
    },
    isInitialized(productType: string = 'stock') {
        return initializedCache[productType] || false;
    },
    // ... rest of store methods
};
```

---

### 4. `client/src/lib/components/InstrumentsTab.svelte`
**Current State:**
- Has `productType` prop (defaults to 'stock')
- Calls `fetchExchanges()` without passing `productType`
- Uses `exchangesStore.exchanges` which is global

**Proposed Changes:**
- Pass `productType` to `fetchExchanges(productType)` call
- Update to use `exchangesStore.getExchanges(productType)` instead of `exchangesStore.exchanges`
- Update loading state to use `exchangesStore.isLoading(productType)`

**Code Changes:**
```svelte
// Update exchanges access
const exchanges = $derived.by(() => exchangesStore.getExchanges(productType));
const loadingExchanges = $derived.by(() => exchangesStore.isLoading(productType));

// Update fetch call
$effect(() => {
    if (!exchangesStore.isInitialized(productType) && !exchangesStore.isLoading(productType) && !exchangesFetched) {
        exchangesFetched = true;
        fetchExchanges(productType); // Pass productType
    }
});
```

---

### 5. `client/src/lib/components/ValidationTab.svelte`
**Current State:**
- Has `productType` prop (defaults to 'stock')
- Calls `fetchExchanges()` without passing `productType`
- Uses `exchangesStore.exchanges` which is global

**Proposed Changes:**
- Pass `productType` to `fetchExchanges(productType)` call
- Update to use `exchangesStore.getExchanges(productType)` instead of `exchangesStore.exchanges`
- Update loading state to use `exchangesStore.isLoading(productType)`

**Code Changes:**
```svelte
// Update exchanges access
const exchanges = $derived.by(() => exchangesStore.getExchanges(productType));
const loadingExchanges = $derived.by(() => exchangesStore.isLoading(productType));

// Update fetch call
$effect(() => {
    if (!exchangesStore.isInitialized(productType) && !exchangesStore.isLoading(productType) && !exchangesFetched) {
        exchangesFetched = true;
        fetchExchanges(productType); // Pass productType
    }
});
```

---

### 6. `client/src/lib/components/RulesTab.svelte`
**Current State:**
- Has `productType` prop (defaults to 'stock')
- Calls `fetchExchanges()` without passing `productType`
- Uses `exchangesStore.exchanges` which is global

**Proposed Changes:**
- Pass `productType` to `fetchExchanges(productType)` call
- Update to use `exchangesStore.getExchanges(productType)` instead of `exchangesStore.exchanges`
- Update loading state to use `exchangesStore.isLoading(productType)`

**Code Changes:**
```svelte
// Update exchanges access
const exchanges = $derived.by(() => exchangesStore.getExchanges(productType));
const loadingExchanges = $derived.by(() => exchangesStore.isLoading(productType));

// Update fetch call
$effect(() => {
    if (!exchangesStore.isInitialized(productType) && !exchangesStore.isLoading(productType) && !exchangesFetched) {
        exchangesFetched = true;
        fetchExchanges(productType); // Pass productType
    }
});
```

---

## Summary of Changes

### Backend (1 file):
1. ✅ `server/controllers/instrument_controller.py` - Update endpoint to accept `product_type` parameter

### Frontend (5 files):
1. ✅ `client/src/lib/services/api.ts` - Add `productType` parameter to `getExchanges()`
2. ✅ `client/src/lib/stores/exchanges.svelte.ts` - Add `productType` parameter and per-product-type caching
3. ✅ `client/src/lib/components/InstrumentsTab.svelte` - Pass `productType` to `fetchExchanges()`
4. ✅ `client/src/lib/components/ValidationTab.svelte` - Pass `productType` to `fetchExchanges()`
5. ✅ `client/src/lib/components/RulesTab.svelte` - Pass `productType` to `fetchExchanges()`

### Total: 6 files need to be modified

---

## Testing Considerations

1. **Backend Testing:**
   - Test `/exchanges` endpoint with each product type (stock, option, future)
   - Test invalid product_type parameter
   - Test default behavior (no parameter)
   - Verify response format is array of strings

2. **Frontend Testing:**
   - Test each tab (Stocks, Options, Futures) loads correct exchanges
   - Test switching between tabs updates exchanges correctly
   - Test loading states per product type
   - Verify exchange dropdowns show correct exchanges for each product type

3. **Integration Testing:**
   - Test that selecting an exchange in InstrumentsTab works correctly
   - Test that validation with selected exchange works correctly
   - Test that rules loading with selected exchange works correctly

