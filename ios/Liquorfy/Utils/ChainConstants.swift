import SwiftUI

/// Color extension for hex string initialization
extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet(charactersIn: "#"))
        let scanner = Scanner(string: hex)
        var rgbValue: UInt64 = 0
        scanner.scanHexInt64(&rgbValue)

        let r = Double((rgbValue & 0xFF0000) >> 16) / 255.0
        let g = Double((rgbValue & 0x00FF00) >> 8) / 255.0
        let b = Double(rgbValue & 0x0000FF) / 255.0

        self.init(red: r, green: g, blue: b)
    }
}

/// Convenience accessors for chain colors used across the app
enum ChainConstants {
    static let fallbackColor = Color.gray

    static func color(for chain: String) -> Color {
        ChainType.color(for: chain)
    }

    static func displayName(for chain: String) -> String {
        ChainType.displayName(for: chain)
    }

    static func needsLightText(for chain: String) -> Bool {
        ChainType.from(chain)?.needsLightText ?? true
    }
}
