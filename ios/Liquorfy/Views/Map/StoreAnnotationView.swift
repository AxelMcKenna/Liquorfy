import SwiftUI

struct StoreAnnotationView: View {
    let chain: String

    var body: some View {
        Image(systemName: "mappin.circle.fill")
            .font(.title2)
            .foregroundStyle(ChainConstants.color(for: chain))
            .background(
                Circle()
                    .fill(.white)
                    .frame(width: 20, height: 20)
            )
            .accessibilityLabel("\(ChainConstants.displayName(for: chain)) store")
    }
}

#Preview {
    HStack(spacing: 20) {
        StoreAnnotationView(chain: "super_liquor")
        StoreAnnotationView(chain: "liquorland")
        StoreAnnotationView(chain: "paknsave")
    }
}
