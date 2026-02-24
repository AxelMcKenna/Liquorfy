import SwiftUI

struct PromoBadgeView: View {
    let percent: Int

    var body: some View {
        Text("\(percent)% off")
            .font(.caption2)
            .fontWeight(.bold)
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(Color.appPrimary)
            .foregroundStyle(.white)
            .clipShape(Capsule())
            .accessibilityLabel("\(percent) percent off")
    }
}

#Preview {
    PromoBadgeView(percent: 25)
}
