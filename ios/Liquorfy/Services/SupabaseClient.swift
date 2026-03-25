import Foundation
import Supabase

let supabase = SupabaseClient(
    supabaseURL: URL(string: Constants.supabaseURL)!,
    supabaseKey: Constants.supabaseAnonKey
)
