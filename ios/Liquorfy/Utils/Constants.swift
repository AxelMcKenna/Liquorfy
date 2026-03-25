import Foundation

enum Constants {
    static let apiBaseURL = "https://api.liquorfy.co.nz"

    // Supabase Auth — set these after adding supabase-swift SPM package
    static let supabaseURL = "https://udrbkdygzhbyktlljkwp.supabase.co"
    static let supabaseAnonKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVkcmJrZHlnemhieWt0bGxqa3dwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjczMzU3NzAsImV4cCI6MjA4MjkxMTc3MH0.TEj7fK0PaMlvBzIeitpSEEwh14RvGvuvUh7rJqAw6a0"

    enum Radius {
        static let min: Double = 1
        static let max: Double = 10
        static let `default`: Double = 2
    }

    enum Pagination {
        static let defaultPageSize = 24
    }

    enum Cache {
        static let locationTTL: TimeInterval = 5 * 60 // 5 minutes
    }

}
