import SwiftUI

struct RadiusSliderView: View {
    @Binding var radius: Double
    let storeCount: Int
    var onChanged: ((Double) -> Void)?

    var body: some View {
        VStack(spacing: 8) {
            HStack {
                Text("Search radius")
                    .font(.appSansMedium(size: 14, relativeTo: .subheadline))
                Spacer()
                Text("\(Int(radius)) km")
                    .font(.appSansSemiBold(size: 14, relativeTo: .subheadline))
                    .foregroundStyle(.tint)
            }

            Slider(
                value: $radius,
                in: Constants.Radius.min...Constants.Radius.max,
                step: 1
            )
            .onChange(of: radius) { _, newValue in
                onChanged?(newValue)
            }

            HStack {
                Text("\(Int(Constants.Radius.min)) km")
                    .font(.appCaption)
                    .foregroundStyle(.secondary)
                Spacer()
                Text("\(storeCount) stores")
                    .font(.appCaption)
                    .foregroundStyle(.secondary)
                Spacer()
                Text("\(Int(Constants.Radius.max)) km")
                    .font(.appCaption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .cardStyle()
    }
}

#Preview {
    RadiusSliderView(radius: .constant(20), storeCount: 12)
        .padding()
}
