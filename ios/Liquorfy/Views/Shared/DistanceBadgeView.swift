import SwiftUI

struct DistanceBadgeView: View {
    let distanceKm: Double?

    var body: some View {
        if let text = Formatters.formatDistance(distanceKm), let distanceKm {
            HStack(spacing: 3) {
                Image(systemName: "location.fill")
                    .font(.system(size: 9))
                Text(text)
                    .font(.caption2)
                    .fontWeight(.medium)
            }
            .foregroundStyle(Formatters.distanceColor(distanceKm))
        }
    }
}

#Preview {
    VStack {
        DistanceBadgeView(distanceKm: 0.8)
        DistanceBadgeView(distanceKm: 3.5)
        DistanceBadgeView(distanceKm: 12.0)
    }
}
