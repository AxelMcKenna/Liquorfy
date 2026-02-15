import SwiftUI

enum ChainType: String, CaseIterable, Codable, Identifiable, Sendable {
    case superLiquor = "super_liquor"
    case liquorland = "liquorland"
    case bottleO = "bottle_o"
    case countdown = "countdown"
    case newWorld = "new_world"
    case paknsave = "paknsave"
    case liquorCentre = "liquor_centre"
    case glengarry = "glengarry"
    case thirstyLiquor = "thirsty_liquor"
    case blackBull = "black_bull"
    case bigBarrel = "big_barrel"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .superLiquor: "Super Liquor"
        case .liquorland: "Liquorland"
        case .bottleO: "Bottle-O"
        case .countdown: "Countdown"
        case .newWorld: "New World"
        case .paknsave: "PAK'nSAVE"
        case .liquorCentre: "Liquor Centre"
        case .glengarry: "Glengarry"
        case .thirstyLiquor: "Thirsty Liquor"
        case .blackBull: "Black Bull"
        case .bigBarrel: "Big Barrel"
        }
    }

    var color: Color {
        Color(hex: colorHex)
    }

    var colorHex: String {
        switch self {
        case .superLiquor: "#0066cc"
        case .liquorland: "#50b848"
        case .bottleO: "#00984f"
        case .countdown: "#00984f"
        case .newWorld: "#e11a2c"
        case .paknsave: "#ffd600"
        case .liquorCentre: "#84cfca"
        case .glengarry: "#111111"
        case .thirstyLiquor: "#f6861e"
        case .blackBull: "#111827"
        case .bigBarrel: "#431717"
        }
    }

    /// Needs white text overlay (dark background)
    var needsLightText: Bool {
        switch self {
        case .paknsave, .liquorCentre: false
        default: true
        }
    }

    static func from(_ string: String) -> ChainType? {
        ChainType(rawValue: string)
    }

    static func color(for chain: String) -> Color {
        from(chain)?.color ?? Color.gray
    }

    static func displayName(for chain: String) -> String {
        from(chain)?.displayName ?? chain
    }
}
