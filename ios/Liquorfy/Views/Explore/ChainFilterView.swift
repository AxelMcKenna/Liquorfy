import SwiftUI

struct ChainFilterView: View {
    @Binding var selectedChains: Set<ChainType>

    var body: some View {
        ForEach(ChainType.allCases) { chain in
            Button {
                if selectedChains.contains(chain) {
                    selectedChains.remove(chain)
                } else {
                    selectedChains.insert(chain)
                }
            } label: {
                HStack(spacing: 10) {
                    Circle()
                        .fill(chain.color)
                        .frame(width: 12, height: 12)

                    Text(chain.displayName)
                        .foregroundStyle(.primary)

                    Spacer()

                    if selectedChains.contains(chain) {
                        Image(systemName: "checkmark")
                            .foregroundStyle(.tint)
                    }
                }
            }
        }
    }
}

#Preview {
    Form {
        ChainFilterView(selectedChains: .constant([.superLiquor, .liquorland]))
    }
}
