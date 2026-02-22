import SwiftUI

// MARK: - Brand Colors
// Matches the web app's design system (web/src/styles.css)

extension Color {
    /// Primary green — HSL 158° 55% 23% (#0d6b3b)
    static let appPrimary = Color(hex: "#0d6b3b")

    /// Warm off-white page background (#f8f4f1 in light, system in dark)
    static let appBackground = Color("AppBackground")

    /// Warm card background (#f0ebe7 in light, system in dark)
    static let appCardBackground = Color("AppCardBackground")

    /// Tertiary inset panel background (#e8e1db in light, system in dark)
    static let appTertiaryBackground = Color("AppTertiaryBackground")

    // MARK: Distance indicator colors (matching web CSS variables)
    /// Close (<2 km) — green
    static let distanceClose = Color(hex: "#22c55e")
    /// Medium (2–5 km) — amber
    static let distanceMedium = Color(hex: "#d4a500")
    /// Far (>5 km) — uses .secondary (gray)
}

// MARK: - Typography
// Georgia (built-in serif) mirrors Lora; SF Pro mirrors DM Sans

extension Font {
    static func appSerif(size: CGFloat, relativeTo style: TextStyle = .body) -> Font {
        .custom("Georgia", size: size, relativeTo: style)
    }

    static var appLargeTitle: Font { appSerif(size: 34, relativeTo: .largeTitle) }
    static var appTitle: Font     { appSerif(size: 28, relativeTo: .title) }
    static var appTitle2: Font    { appSerif(size: 22, relativeTo: .title2) }
    static var appTitle3: Font    { appSerif(size: 20, relativeTo: .title3) }
    static var appHeadline: Font  { appSerif(size: 17, relativeTo: .headline) }
}
