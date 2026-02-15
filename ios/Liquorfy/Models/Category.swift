import Foundation

enum Category: String, CaseIterable, Identifiable, Sendable {
    case beer, wine, spirits, rtd, cider
    case vodka, gin, rum, whisky, bourbon, scotch, tequila, brandy, liqueur
    case champagne, sparkling
    case redWine = "red_wine"
    case whiteWine = "white_wine"
    case rose
    case craftBeer = "craft_beer"
    case lager, ale, ipa, stout
    case mixer
    case nonAlcoholic = "non_alcoholic"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .rtd: "RTDs"
        case .ipa: "IPA"
        case .redWine: "Red Wine"
        case .whiteWine: "White Wine"
        case .rose: "Ros\u{00E9}"
        case .craftBeer: "Craft Beer"
        case .nonAlcoholic: "Non-Alcoholic"
        default:
            rawValue.capitalized
        }
    }

    /// Group categories for the picker UI
    var group: CategoryGroup {
        switch self {
        case .beer, .craftBeer, .lager, .ale, .ipa, .stout:
            return .beer
        case .wine, .redWine, .whiteWine, .rose, .champagne, .sparkling:
            return .wine
        case .spirits, .vodka, .gin, .rum, .whisky, .bourbon, .scotch, .tequila, .brandy, .liqueur:
            return .spirits
        case .rtd, .cider:
            return .readyToDrink
        case .mixer, .nonAlcoholic:
            return .other
        }
    }
}

enum CategoryGroup: String, CaseIterable, Identifiable {
    case beer = "Beer"
    case wine = "Wine"
    case spirits = "Spirits"
    case readyToDrink = "Ready to Drink"
    case other = "Other"

    var id: String { rawValue }

    var categories: [Category] {
        Category.allCases.filter { $0.group == self }
    }
}
