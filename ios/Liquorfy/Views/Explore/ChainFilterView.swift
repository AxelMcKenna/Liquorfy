import SwiftUI

struct ChainFilterView: View {
    @Binding var selectedChains: Set<ChainType>

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Select All / Clear actions
            HStack(spacing: 12) {
                Button {
                    selectedChains = Set(ChainType.allCases)
                } label: {
                    Text("Select All")
                        .font(.appSans(size: 12, relativeTo: .caption))
                        .foregroundStyle(.black)
                }

                Button {
                    selectedChains = []
                } label: {
                    Text("Clear")
                        .font(.appSans(size: 12, relativeTo: .caption))
                        .foregroundStyle(.black)
                }

                Spacer()
            }

            // Scrollable chain list
            ScrollView {
                VStack(alignment: .leading, spacing: 8) {
                    ForEach(ChainType.allCases) { chain in
                        Button {
                            if selectedChains.contains(chain) {
                                selectedChains.remove(chain)
                            } else {
                                selectedChains.insert(chain)
                            }
                        } label: {
                            HStack(spacing: 10) {
                                Image(systemName: selectedChains.contains(chain) ? "checkmark.square.fill" : "square")
                                    .font(.system(size: 16))
                                    .foregroundStyle(Color.appPrimary)

                                Text(chain.displayName)
                                    .font(.appCardBody)
                                    .foregroundStyle(.black)

                                Spacer()
                            }
                        }
                    }
                }
            }
            .frame(maxHeight: 256)
        }
    }
}

#Preview {
    ChainFilterView(selectedChains: .constant([.superLiquor, .liquorland]))
        .padding()
}
