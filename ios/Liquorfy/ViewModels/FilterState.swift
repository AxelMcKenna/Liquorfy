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
    var sort: SortOption = .discount
    var currentPage: Int = 1

    var hasActiveFilters: Bool {
        category != nil
        || !selectedChains.isEmpty
        || promoOnly
        || priceMin != nil
        || priceMax != nil
        || sort != .discount
    }

    var activeFilterCount: Int {
        var count = 0
        if category != nil { count += 1 }
        if !selectedChains.isEmpty { count += 1 }
        if promoOnly { count += 1 }
        if priceMin != nil || priceMax != nil { count += 1 }
        if sort != .discount { count += 1 }
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
        sort = .discount
        currentPage = 1
    }
}
