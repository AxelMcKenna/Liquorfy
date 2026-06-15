import Foundation

@Observable
final class FilterState {
    var query: String = ""
    var category: Category?
    var selectedChains: Set<ChainType> = []
    var promoOnly: Bool = false
    var uniqueProducts: Bool = true
    var priceMin: Double?
    var priceMax: Double?
    /// nil until the user explicitly picks a sort, so the default tracks `promoOnly`
    /// — matching web: `sortParam || (promo_only ? DISCOUNT : BEST_VALUE)`.
    var userSelectedSort: SortOption?
    var currentPage: Int = 1

    /// Effective sort: the user's explicit choice, otherwise the promo-aware default.
    var sort: SortOption {
        get { userSelectedSort ?? (promoOnly ? .discount : .bestValue) }
        set { userSelectedSort = newValue }
    }

    var hasActiveFilters: Bool {
        category != nil
        || !selectedChains.isEmpty
        || promoOnly
        || priceMin != nil
        || priceMax != nil
    }

    var activeFilterCount: Int {
        var count = 0
        if category != nil { count += 1 }
        if !selectedChains.isEmpty { count += 1 }
        if promoOnly { count += 1 }
        if priceMin != nil || priceMax != nil { count += 1 }
        return count
    }

    func buildFilters(lat: Double?, lon: Double?, radiusKm: Double?) -> ProductFilters {
        ProductFilters(
            query: query.isEmpty ? nil : query,
            category: category,
            chains: selectedChains,
            promoOnly: promoOnly,
            uniqueProducts: uniqueProducts,
            priceMin: priceMin,
            priceMax: priceMax,
            sort: sort,
            lat: lat,
            lon: lon,
            radiusKm: radiusKm,
            page: currentPage,
            pageSize: Constants.Pagination.defaultPageSize
        )
    }

    func reset() {
        category = nil
        selectedChains = []
        promoOnly = false
        priceMin = nil
        priceMax = nil
        userSelectedSort = nil
        currentPage = 1
    }

    /// Apply the user's saved default filters (chains/category/promo), mirroring the
    /// web Explore behaviour of auto-applying `liquorfy_saved_filters` on a clean load.
    @MainActor
    func applySavedFilters() {
        guard let saved = SavedFiltersManager.shared.get() else { return }
        if let savedCategory = saved.category {
            category = Category(rawValue: savedCategory)
        }
        if let savedChains = saved.chains {
            selectedChains = Set(savedChains.compactMap(ChainType.init(rawValue:)))
        }
        if let promo = saved.promoOnly {
            promoOnly = promo
        }
    }
}
