import XCTest
@testable import Liquorfy

final class FormattersTests: XCTestCase {

    // MARK: - Distance

    func testFormatDistanceNil() {
        XCTAssertNil(Formatters.formatDistance(nil))
    }

    func testFormatDistanceMeters() {
        XCTAssertEqual(Formatters.formatDistance(0.8), "800m")
        XCTAssertEqual(Formatters.formatDistance(0.15), "150m")
    }

    func testFormatDistanceKilometers() {
        XCTAssertEqual(Formatters.formatDistance(1.0), "1.0km")
        XCTAssertEqual(Formatters.formatDistance(2.5), "2.5km")
        XCTAssertEqual(Formatters.formatDistance(12.3), "12.3km")
    }

    func testFormatDistanceAway() {
        XCTAssertEqual(Formatters.formatDistanceAway(0.8), "800m away")
        XCTAssertEqual(Formatters.formatDistanceAway(2.5), "2.5km away")
        XCTAssertNil(Formatters.formatDistanceAway(nil))
    }

    // MARK: - Price

    func testFormatPrice() {
        XCTAssertEqual(Formatters.formatPrice(24.99), "$24.99")
        XCTAssertEqual(Formatters.formatPrice(10.0), "$10.00")
        XCTAssertEqual(Formatters.formatPrice(0.5), "$0.50")
    }

    func testFormatPricePerUnit() {
        XCTAssertEqual(Formatters.formatPricePerUnit(1.33, unit: "100ml"), "$1.33 per 100ml")
    }

    // MARK: - Savings

    func testSavingsPercent() {
        XCTAssertEqual(Formatters.savingsPercent(original: 100, promo: 80), 20)
        XCTAssertEqual(Formatters.savingsPercent(original: 24.99, promo: 19.99), 20)
        XCTAssertEqual(Formatters.savingsPercent(original: 100, promo: nil), 0)
        XCTAssertEqual(Formatters.savingsPercent(original: 100, promo: 100), 0)
        XCTAssertEqual(Formatters.savingsPercent(original: 100, promo: 120), 0)
    }

    // MARK: - Promo End Date

    func testFormatPromoEndDateNil() {
        XCTAssertNil(Formatters.formatPromoEndDate(nil))
    }

    func testFormatPromoEndDateToday() {
        let today = Calendar.current.startOfDay(for: Date())
        XCTAssertEqual(Formatters.formatPromoEndDate(today), "Ends today")
    }

    func testFormatPromoEndDateTomorrow() {
        let tomorrow = Calendar.current.date(byAdding: .day, value: 1, to: Calendar.current.startOfDay(for: Date()))!
        XCTAssertEqual(Formatters.formatPromoEndDate(tomorrow), "Ends tomorrow")
    }

    func testFormatPromoEndDateDaysLeft() {
        let inThreeDays = Calendar.current.date(byAdding: .day, value: 3, to: Calendar.current.startOfDay(for: Date()))!
        XCTAssertEqual(Formatters.formatPromoEndDate(inThreeDays), "3d left")
    }

    func testFormatPromoEndDateExpired() {
        let yesterday = Calendar.current.date(byAdding: .day, value: -1, to: Calendar.current.startOfDay(for: Date()))!
        XCTAssertEqual(Formatters.formatPromoEndDate(yesterday), "Expired")
    }

    // MARK: - Category

    func testFormatCategory() {
        XCTAssertEqual(Formatters.formatCategory("red_wine"), "Red Wine")
        XCTAssertEqual(Formatters.formatCategory("beer"), "Beer")
        XCTAssertEqual(Formatters.formatCategory("non_alcoholic"), "Non Alcoholic")
        XCTAssertEqual(Formatters.formatCategory(nil), "")
    }
}
