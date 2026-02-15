import SwiftUI

struct StatsSection: View {
    var body: some View {
        VStack(spacing: 20) {
            Text("Transparent Pricing")
                .font(.title3)
                .fontWeight(.semibold)

            Text("Compare prices across major retailers in real-time")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)

            HStack(spacing: 0) {
                statItem(value: "10+", label: "Retailers")
                statItem(value: "Daily", label: "Updates")
                statItem(value: "Free", label: "Always")
            }

            VStack(spacing: 6) {
                Text("Drink Responsibly")
                    .font(.subheadline)
                    .fontWeight(.medium)

                Text("You must be 18+ to purchase alcohol.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            .padding()
            .frame(maxWidth: .infinity)
            .background(Color(.secondarySystemGroupedBackground))
            .clipShape(RoundedRectangle(cornerRadius: 12))
        }
    }

    private func statItem(value: String, label: String) -> some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.title2)
                .fontWeight(.semibold)
                .foregroundStyle(.tint)
            Text(label)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
    }
}

#Preview {
    StatsSection()
        .padding()
}
