import SwiftUI

struct SortPickerView: View {
    @Binding var selection: SortOption

    var body: some View {
        Menu {
            ForEach(SortOption.allCases) { option in
                Button {
                    selection = option
                } label: {
                    HStack {
                        Label(option.displayName, systemImage: option.iconName)
                        if selection == option {
                            Image(systemName: "checkmark")
                        }
                    }
                }
            }
        } label: {
            HStack {
                Image(systemName: selection.iconName)
                    .font(.system(size: 12))
                    .foregroundStyle(.black)
                Text(selection.displayName)
                    .font(.appCardBody)
                    .foregroundStyle(.black)
                Spacer()
                Image(systemName: "chevron.down")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundStyle(.black)
            }
            .padding(.horizontal, 12)
            .frame(height: 40)
            .background(.white)
            .clipShape(RoundedRectangle(cornerRadius: 8))
            .shadow(color: .black.opacity(0.06), radius: 3, x: 0, y: 1)
        }
    }
}

#Preview {
    SortPickerView(selection: .constant(.discount))
        .padding()
}
