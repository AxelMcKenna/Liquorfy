import SwiftUI

// MARK: - Brand Colors
// Matches the web app's design system (web/src/styles.css)

extension Color {
    /// Primary green — HSL 158° 55% 23% (#1a5a43)
    static let appPrimary = Color(hex: "#1a5a43")

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
// Lora (serif) for headings, DM Sans for body — matches web exactly

extension Font {
    // MARK: Serif (Lora → Georgia on iOS, headings only)
    static func appSerif(size: CGFloat, relativeTo style: TextStyle = .body) -> Font {
        .custom("Georgia", size: size, relativeTo: style)
    }

    static var appLargeTitle: Font { appSerif(size: 34, relativeTo: .largeTitle) }
    static var appTitle: Font     { appSerif(size: 28, relativeTo: .title) }
    static var appTitle2: Font    { appSerif(size: 22, relativeTo: .title2) }
    static var appTitle3: Font    { appSerif(size: 20, relativeTo: .title3) }
    static var appHeadline: Font  { appSerif(size: 17, relativeTo: .headline) }

    // MARK: Sans (DM Sans — body text, cards, captions)
    static func appSans(size: CGFloat, relativeTo style: TextStyle = .body) -> Font {
        .custom("DMSans-Regular", size: size, relativeTo: style)
    }
    static func appSansMedium(size: CGFloat, relativeTo style: TextStyle = .body) -> Font {
        .custom("DMSans-Medium", size: size, relativeTo: style)
    }
    static func appSansSemiBold(size: CGFloat, relativeTo style: TextStyle = .body) -> Font {
        .custom("DMSans-SemiBold", size: size, relativeTo: style)
    }
    static func appSansBold(size: CGFloat, relativeTo style: TextStyle = .body) -> Font {
        .custom("DMSans-Bold", size: size, relativeTo: style)
    }

    // Web-matched presets (DM Sans sizes from web CSS)
    /// 16pt regular — web text-base
    static var appBody: Font       { appSans(size: 16, relativeTo: .body) }
    /// 14pt medium — web text-sm font-medium (product names)
    static var appCardTitle: Font  { appSansMedium(size: 14, relativeTo: .subheadline) }
    /// 20pt semibold — web text-xl font-semibold (prices)
    static var appPrice: Font      { appSansSemiBold(size: 20, relativeTo: .title3) }
    /// 14pt regular — web text-sm (secondary card text)
    static var appCardBody: Font   { appSans(size: 14, relativeTo: .subheadline) }
    /// 12pt regular — web text-xs (captions, distances, badges)
    static var appCaption: Font    { appSans(size: 12, relativeTo: .caption) }
    /// 12pt semibold — web text-xs font-semibold (badge labels)
    static var appBadge: Font      { appSansSemiBold(size: 12, relativeTo: .caption) }
    /// 15pt regular — web callout equivalent
    static var appCallout: Font    { appSans(size: 15, relativeTo: .callout) }
}
