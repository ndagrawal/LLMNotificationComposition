// NotifyComposeTests.swift
// NotifyCompose SDK — Unit Tests

import XCTest
@testable import NotifyCompose

final class NotifyComposeTests: XCTestCase {

    // MARK: - Model Tests

    func testUserProfileCLVTierMapping() {
        XCTAssertEqual(CLVTier.platinum.rawValue, "platinum")
        XCTAssertEqual(CLVTier.gold.rawValue, "gold")
        XCTAssertEqual(CLVTier.silver.rawValue, "silver")
        XCTAssertEqual(CLVTier.bronze.rawValue, "bronze")
    }

    func testNotificationRequestCreation() {
        let user = UserProfile(userId: "test_user", clvTier: .gold)
        let item = ContentItem(
            itemId: "item_001",
            title: "Margherita Pizza",
            category: "food/italian",
            attributes: ["price": "$12.99", "rating": "4.8"]
        )
        let request = NotificationRequest(
            user: user,
            domain: .foodDelivery,
            intent: .reEngagement,
            contentItem: item
        )

        XCTAssertEqual(request.user.userId, "test_user")
        XCTAssertEqual(request.domain, .foodDelivery)
        XCTAssertEqual(request.intent, .reEngagement)
        XCTAssertEqual(request.contentItem.attributes["price"], "$12.99")
        XCTAssertFalse(request.requestId.isEmpty)
    }

    func testComposedNotificationIdentifiable() {
        let trace = PipelineTrace(budgetDecision: "LLM Full Pipeline")
        let notification = ComposedNotification(
            notificationId: "notif_001",
            title: "Your pizza is ready!",
            body: "Margherita Pizza from Tony's is on its way.",
            compositionPath: .llmFull,
            rewardScore: 0.87,
            pipelineTrace: trace
        )

        XCTAssertEqual(notification.notificationId, "notif_001")
        XCTAssertEqual(notification.compositionPath, .llmFull)
        XCTAssertFalse(notification.isFrequencyCapped)
        XCTAssertEqual(notification.rewardScore, 0.87, accuracy: 0.001)
    }

    func testFrequencyCappedNotification() {
        let trace = PipelineTrace(budgetDecision: "Frequency Capped")
        let notification = ComposedNotification(
            notificationId: "notif_002",
            title: "",
            body: "",
            compositionPath: .frequencyCapped,
            rewardScore: 0.0,
            pipelineTrace: trace
        )
        XCTAssertTrue(notification.isFrequencyCapped)
    }

    // MARK: - Domain Adapter Tests

    func testFoodDeliveryAdapterCreatesCorrectRequest() {
        let request = FoodDeliveryAdapter.reEngagement(
            userId: "user_123",
            restaurantId: "rest_456",
            restaurantName: "Tony's Pizza",
            dishName: "Margherita Pizza",
            price: "$12.99",
            rating: "4.8",
            deliveryTime: "25 min",
            category: "food/italian",
            weatherCondition: "rainy"
        )

        XCTAssertEqual(request.domain, .foodDelivery)
        XCTAssertEqual(request.intent, .reEngagement)
        XCTAssertEqual(request.contentItem.attributes["restaurant"], "Tony's Pizza")
        XCTAssertEqual(request.contentItem.attributes["price"], "$12.99")
        XCTAssertEqual(request.triggerContext.weatherCondition, "rainy")
    }

    func testECommerceAdapterAbandonedCart() {
        let request = ECommerceAdapter.abandonedCart(
            userId: "user_789",
            productId: "prod_001",
            productName: "Sony WH-1000XM5",
            price: "$349.99",
            discount: "15% off",
            category: "electronics/audio"
        )

        XCTAssertEqual(request.domain, .eCommerce)
        XCTAssertEqual(request.intent, .abandonedCart)
        XCTAssertEqual(request.contentItem.attributes["discount"], "15% off")
    }

    func testSocialMediaAdapterNewContent() {
        let request = SocialMediaAdapter.newContent(
            userId: "user_456",
            postId: "post_789",
            postTitle: "10 Swift Tips",
            creatorName: "SwiftDev",
            viewCount: "12K",
            category: "technology"
        )

        XCTAssertEqual(request.domain, .socialMedia)
        XCTAssertEqual(request.intent, .newContent)
        XCTAssertEqual(request.contentItem.attributes["creator"], "SwiftDev")
    }

    // MARK: - Pipeline Options Tests

    func testDefaultPipelineOptions() {
        let options = PipelineOptions()
        XCTAssertTrue(options.enableGuardrails)
        XCTAssertTrue(options.enableFrequencyCap)
        XCTAssertTrue(options.enableSendTimeOptimization)
        XCTAssertEqual(options.maxCandidates, 5)
        XCTAssertEqual(options.maxTitleLength, 50)
        XCTAssertEqual(options.maxBodyLength, 120)
        XCTAssertNil(options.overrideCLVTier)
    }

    func testOrderUpdateBypassesFrequencyCap() {
        let request = FoodDeliveryAdapter.orderUpdate(
            userId: "user_123",
            orderId: "order_001",
            orderStatus: "Out for delivery",
            estimatedArrival: "10 min",
            restaurantName: "Tony's Pizza"
        )
        XCTAssertFalse(request.options.enableFrequencyCap)
    }

    // MARK: - TriggerContext Tests

    func testTriggerContextDefaults() {
        let context = TriggerContext()
        XCTAssertGreaterThanOrEqual(context.localHour, 0)
        XCTAssertLessThanOrEqual(context.localHour, 23)
        XCTAssertGreaterThanOrEqual(context.dayOfWeek, 1)
        XCTAssertLessThanOrEqual(context.dayOfWeek, 7)
        XCTAssertNil(context.weatherCondition)
        XCTAssertFalse(context.recentAppOpen)
    }

    // MARK: - PipelineTrace Tests

    func testPipelineTraceDefaults() {
        let trace = PipelineTrace(budgetDecision: "LLM Full Pipeline")
        XCTAssertEqual(trace.budgetDecision, "LLM Full Pipeline")
        XCTAssertTrue(trace.retrievedContextKeys.isEmpty)
        XCTAssertEqual(trace.candidatesGenerated, 0)
        XCTAssertTrue(trace.guardrailsApplied.isEmpty)
        XCTAssertFalse(trace.sendTimeOptimized)
    }
}
