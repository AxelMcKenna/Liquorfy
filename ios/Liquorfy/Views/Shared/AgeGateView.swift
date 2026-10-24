import SwiftUI

/// First-launch confirmation that the user is of legal drinking age in NZ.
struct AgeGateView: View {
    let onConfirm: () -> Void
    @State private var declined = false

    var body: some View {
        VStack(spacing: 24) {
            Spacer()

            Text("LIQUORFY")
                .font(.appSansSemiBold(size: 28, relativeTo: .title))
                .tracking(4)
                .foregroundStyle(.appPrimary)

            VStack(spacing: 8) {
                Text("Are you 18 or over?")
                    .font(.appTitle2)

                Text("Liquorfy compares alcohol prices and is only for people of legal drinking age in New Zealand.")
                    .font(.appBody)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }

            if declined {
                Text("Sorry, you need to be 18 or over to use Liquorfy.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            } else {
                VStack(spacing: 12) {
                    Button(action: onConfirm) {
                        Text("Yes, I'm 18 or over")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.large)

                    Button("No") { declined = true }
                        .controlSize(.large)
                }
            }

            Spacer()

            Text("Please drink responsibly.")
                .font(.appCaption)
                .foregroundStyle(.secondary)
        }
        .padding(32)
        .frame(maxWidth: 480)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.appBackground)
    }
}

#Preview {
    AgeGateView(onConfirm: {})
}
