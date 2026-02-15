import CoreLocation
import XCTest
@testable import Liquorfy

final class NZBoundsValidatorTests: XCTestCase {

    func testWellingtonIsInNZ() {
        XCTAssertTrue(NZBoundsValidator.isInNZ(lat: -41.2865, lon: 174.7762))
    }

    func testAucklandIsInNZ() {
        XCTAssertTrue(NZBoundsValidator.isInNZ(lat: -36.8485, lon: 174.7633))
    }

    func testChristchurchIsInNZ() {
        XCTAssertTrue(NZBoundsValidator.isInNZ(lat: -43.5321, lon: 172.6362))
    }

    func testInvercargillIsInNZ() {
        XCTAssertTrue(NZBoundsValidator.isInNZ(lat: -46.4132, lon: 168.3475))
    }

    func testSydneyIsNotInNZ() {
        XCTAssertFalse(NZBoundsValidator.isInNZ(lat: -33.8688, lon: 151.2093))
    }

    func testLondonIsNotInNZ() {
        XCTAssertFalse(NZBoundsValidator.isInNZ(lat: 51.5074, lon: -0.1278))
    }

    func testBoundaryEdges() {
        // South boundary
        XCTAssertTrue(NZBoundsValidator.isInNZ(lat: -47.0, lon: 170.0))
        XCTAssertFalse(NZBoundsValidator.isInNZ(lat: -47.1, lon: 170.0))

        // North boundary
        XCTAssertTrue(NZBoundsValidator.isInNZ(lat: -34.0, lon: 170.0))
        XCTAssertFalse(NZBoundsValidator.isInNZ(lat: -33.9, lon: 170.0))

        // West boundary
        XCTAssertTrue(NZBoundsValidator.isInNZ(lat: -40.0, lon: 165.0))
        XCTAssertFalse(NZBoundsValidator.isInNZ(lat: -40.0, lon: 164.9))

        // East boundary
        XCTAssertTrue(NZBoundsValidator.isInNZ(lat: -40.0, lon: 179.0))
        XCTAssertFalse(NZBoundsValidator.isInNZ(lat: -40.0, lon: 179.1))
    }

    func testCoordinateOverload() {
        let wellingtonCoord = CLLocationCoordinate2D(latitude: -41.2865, longitude: 174.7762)
        XCTAssertTrue(NZBoundsValidator.isInNZ(wellingtonCoord))

        let sydneyCoord = CLLocationCoordinate2D(latitude: -33.8688, longitude: 151.2093)
        XCTAssertFalse(NZBoundsValidator.isInNZ(sydneyCoord))
    }

    func testCLLocationOverload() {
        let wellington = CLLocation(latitude: -41.2865, longitude: 174.7762)
        XCTAssertTrue(NZBoundsValidator.isInNZ(wellington))
    }
}
