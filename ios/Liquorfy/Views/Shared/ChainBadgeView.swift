import SwiftUI

struct ChainBadgeView: View {
    let chain: String
    var colored: Bool = false

    var body: some View {
        if colored {
            Text(ChainConstants.displayName(for: chain))
                .font(.caption2)
                .fontWeight(.semibold)
                .padding(.horizontal, 8)
                .padding(.vertical, 3)
                .background(ChainConstants.color(for: chain))
                .foregroundStyle(ChainConstants.needsLightText(for: chain) ? .white : .black)
                .clipShape(RoundedRectangle(cornerRadius: 6))
                .accessibilityLabel(ChainConstants.displayName(for: chain))
        } else {
            Text(ChainConstants.displayName(for: chain))
                .font(.appCaption)
                .foregroundStyle(.secondary)
                .accessibilityLabel(ChainConstants.displayName(for: chain))
        }
    }
}

#Preview {
    VStack(spacing: 8) {
        ChainBadgeView(chain: "super_liquor")
        ChainBadgeView(chain: "super_liquor", colored: true)
        ChainBadgeView(chain: "paknsave")
        ChainBadgeView(chain: "liquorland")
    }
}
