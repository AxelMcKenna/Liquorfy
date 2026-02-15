import SwiftUI

struct SortPickerView: View {
    @Binding var selection: SortOption

    var body: some View {
        ForEach(SortOption.allCases) { option in
            Button {
                selection = option
            } label: {
                HStack(spacing: 10) {
                    Image(systemName: option.iconName)
                        .frame(width: 20)
                        .foregroundStyle(.tint)

                    Text(option.displayName)
                        .foregroundStyle(.primary)

                    Spacer()

                    if selection == option {
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
        SortPickerView(selection: .constant(.discount))
    }
}
