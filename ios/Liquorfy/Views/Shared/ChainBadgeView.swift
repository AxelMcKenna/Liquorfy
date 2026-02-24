import SwiftUI

struct ChainBadgeView: View {
    let chain: String

    var body: some View {
        Text(ChainConstants.displayName(for: chain))
            .font(.caption2)
            .fontWeight(.semibold)
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(ChainConstants.color(for: chain))
            .foregroundStyle(ChainConstants.needsLightText(for: chain) ? .white : .black)
            .clipShape(Capsule())
            .accessibilityLabel(ChainConstants.displayName(for: chain))
    }
}

#Preview {
    HStack {
        ChainBadgeView(chain: "super_liquor")
        ChainBadgeView(chain: "paknsave")
        ChainBadgeView(chain: "liquorland")
    }
}
