import SwiftUI

struct StoreCalloutView: View {
    let store: Store

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                ChainBadgeView(chain: store.chain, colored: true)
                Spacer()
                if let distance = store.distanceKm {
                    DistanceBadgeView(distanceKm: distance)
                }
            }

            Text(store.name)
                .font(.headline)

            if let address = store.address {
                HStack(spacing: 4) {
                    Image(systemName: "mappin")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text(address)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
            }

            if let region = store.region {
                Text(region)
                    .font(.caption)
                    .foregroundStyle(.tertiary)
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

#Preview {
    StoreCalloutView(store: PreviewData.store)
}
