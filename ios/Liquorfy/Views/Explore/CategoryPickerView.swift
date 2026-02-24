import SwiftUI

struct CategoryPickerView: View {
    @Binding var selection: Category?

    var body: some View {
        Menu {
            Button {
                selection = nil
            } label: {
                HStack {
                    Text("All Categories")
                    if selection == nil {
                        Image(systemName: "checkmark")
                    }
                }
            }

            ForEach(CategoryGroup.allCases) { group in
                Section(group.rawValue) {
                    ForEach(group.categories) { category in
                        Button {
                            if selection == category {
                                selection = nil
                            } else {
                                selection = category
                            }
                        } label: {
                            HStack {
                                Text(category.displayName)
                                if selection == category {
                                    Image(systemName: "checkmark")
                                }
                            }
                        }
                    }
                }
            }
        } label: {
            HStack {
                Text(selection?.displayName ?? "All Categories")
                    .font(.appCardBody)
                    .foregroundStyle(.primary)
                Spacer()
                Image(systemName: "chevron.down")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundStyle(.secondary)
            }
            .padding(.horizontal, 12)
            .frame(height: 40)
            .background(.white)
            .clipShape(RoundedRectangle(cornerRadius: 8))
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color.gray.opacity(0.3), lineWidth: 1)
            )
        }
    }
}

#Preview {
    CategoryPickerView(selection: .constant(.beer))
        .padding()
}
