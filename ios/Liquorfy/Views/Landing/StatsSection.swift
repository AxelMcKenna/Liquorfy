import SwiftUI

struct StatsSection: View {
    var body: some View {
        VStack(spacing: 20) {
            Text("Transparent Pricing")
                .font(.appTitle3)

            Text("Compare prices across major retailers in real-time")
                .font(.appCardBody)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)

            HStack(spacing: 0) {
                statItem(value: "10+", label: "Retailers")
                statItem(value: "Daily", label: "Updates")
                statItem(value: "Free", label: "Always")
            }

            VStack(spacing: 4) {
                Text("Drink Responsibly")
                    .font(.appSansMedium(size: 14, relativeTo: .subheadline))

                Text("You must be 18+ to purchase alcohol. If you need support, visit [\("Alcohol.org.nz")](https://www.alcohol.org.nz)")
                    .font(.appCaption)
                    .foregroundStyle(.secondary)
                    .tint(Color.appPrimary)
                    .multilineTextAlignment(.center)
            }
            .padding(24)
            .frame(maxWidth: .infinity)
            .background(Color.appTertiaryBackground)
            .clipShape(RoundedRectangle(cornerRadius: 8))

            HStack(spacing: 16) {
                Link("Privacy Policy", destination: URL(string: "https://www.liquorfy.co.nz/privacy")!)
                Text("·")
                    .foregroundStyle(.secondary)
                Link("Support", destination: URL(string: "https://www.liquorfy.co.nz/support")!)
            }
            .font(.appCaption)
            .foregroundStyle(.secondary)
        }
    }

    private func statItem(value: String, label: String) -> some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.appSansSemiBold(size: 22, relativeTo: .title2))
                .foregroundStyle(.tint)
            Text(label)
                .font(.appCaption)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
    }
}

#Preview {
    StatsSection()
        .padding()
}
