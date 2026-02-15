import Foundation

enum SortOption: String, CaseIterable, Identifiable, Sendable {
    case discount = "discount"
    case bestValue = "price_per_100ml"
    case cheapest = "total_price"
    case bestPerDrink = "price_per_standard_drink"
    case distance = "distance"
    case newest = "newest"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .discount: "Biggest Discount"
        case .bestValue: "Best Value (per 100ml)"
        case .cheapest: "Cheapest"
        case .bestPerDrink: "Best per Std Drink"
        case .distance: "Nearest"
        case .newest: "Newest"
        }
    }

    var iconName: String {
        switch self {
        case .discount: "percent"
        case .bestValue: "drop.fill"
        case .cheapest: "dollarsign.circle"
        case .bestPerDrink: "wineglass"
        case .distance: "location"
        case .newest: "clock"
        }
    }
}
