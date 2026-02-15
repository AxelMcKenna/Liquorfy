import Foundation

enum Constants {
    static let apiBaseURL = "https://api.liquorfy.co.nz"

    enum Radius {
        static let min: Double = 5
        static let max: Double = 40
        static let `default`: Double = 20
    }

    enum Pagination {
        static let defaultPageSize = 24
    }

    enum Cache {
        static let locationTTL: TimeInterval = 5 * 60 // 5 minutes
    }

    enum Comparison {
        static let maxProducts = 4
    }
}
