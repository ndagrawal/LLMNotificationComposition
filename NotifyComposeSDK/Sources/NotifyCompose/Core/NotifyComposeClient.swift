// NotifyComposeClient.swift
// NotifyCompose SDK — Main Entry Point
//
// This is the primary interface iOS apps use to interact with the NotifyCompose pipeline.
// It handles: signal batching, notification composition requests, and feedback reporting.
//
// Usage:
//   let client = NotifyComposeClient(baseURL: "https://your-server.com", userId: "user_123")
//   let notification = try await client.compose(request: request)

import Foundation

// MARK: - Client Configuration

public struct NotifyComposeConfiguration {
    public let baseURL: URL
    public let userId: String
    public let signalBatchInterval: TimeInterval
    public let maxSignalBatchSize: Int
    public let requestTimeout: TimeInterval

    public init(
        baseURL: URL,
        userId: String,
        signalBatchInterval: TimeInterval = 30.0,
        maxSignalBatchSize: Int = 50,
        requestTimeout: TimeInterval = 15.0
    ) {
        self.baseURL = baseURL
        self.userId = userId
        self.signalBatchInterval = signalBatchInterval
        self.maxSignalBatchSize = maxSignalBatchSize
        self.requestTimeout = requestTimeout
    }
}

// MARK: - NotifyComposeClient

/// The main SDK client. Manages signal collection, composition requests, and feedback.
///
/// Initialize once per app session (e.g., in AppDelegate or @main App struct):
/// ```swift
/// let client = NotifyComposeClient(
///     configuration: NotifyComposeConfiguration(
///         baseURL: URL(string: "https://your-server.com")!,
///         userId: currentUser.id
///     )
/// )
/// ```
@MainActor
public final class NotifyComposeClient: ObservableObject {

    // MARK: - Published State
    @Published public private(set) var lastComposedNotification: ComposedNotification?
    @Published public private(set) var isComposing: Bool = false
    @Published public private(set) var lastError: Error?

    // MARK: - Private Properties
    private let configuration: NotifyComposeConfiguration
    private let networkClient: NCNetworkClient
    private let signalCollector: SignalCollector

    // MARK: - Initialization

    public init(configuration: NotifyComposeConfiguration) {
        self.configuration = configuration
        self.networkClient = NCNetworkClient(
            baseURL: configuration.baseURL,
            timeout: configuration.requestTimeout
        )
        self.signalCollector = SignalCollector(
            userId: configuration.userId,
            batchInterval: configuration.signalBatchInterval,
            maxBatchSize: configuration.maxSignalBatchSize
        )
    }

    /// Convenience initializer with URL string.
    public convenience init(baseURL: String, userId: String) {
        guard let url = URL(string: baseURL) else {
            fatalError("NotifyComposeClient: Invalid baseURL '\(baseURL)'")
        }
        self.init(configuration: NotifyComposeConfiguration(baseURL: url, userId: userId))
    }

    // MARK: - Signal Tracking

    /// Track a user interaction signal. Signals are batched and sent automatically.
    ///
    /// ```swift
    /// client.track(.itemClick, itemId: "pizza_001", category: "food/italian")
    /// client.track(.purchase, itemId: "pizza_001", category: "food/italian")
    /// ```
    public func track(
        _ type: SignalType,
        itemId: String? = nil,
        category: String? = nil,
        durationSeconds: Double? = nil,
        notificationId: String? = nil,
        metadata: [String: String] = [:]
    ) {
        let signal = Signal(
            type: type,
            itemId: itemId,
            category: category,
            durationSeconds: durationSeconds,
            notificationId: notificationId,
            metadata: metadata
        )
        signalCollector.add(signal)
    }

    /// Immediately flush all pending signals to the server.
    public func flushSignals() async {
        await signalCollector.flush(using: networkClient, userId: configuration.userId)
    }

    // MARK: - Notification Composition

    /// Request a composed notification from the pipeline.
    ///
    /// ```swift
    /// let request = NotificationRequest(
    ///     user: userProfile,
    ///     domain: .foodDelivery,
    ///     intent: .reEngagement,
    ///     contentItem: ContentItem(
    ///         itemId: "pizza_001",
    ///         title: "Margherita Pizza",
    ///         category: "food/italian",
    ///         attributes: ["price": "$12.99", "rating": "4.8", "deliveryTime": "25 min"]
    ///     )
    /// )
    /// let notification = try await client.compose(request: request)
    /// ```
    public func compose(request: NotificationRequest) async throws -> ComposedNotification {
        isComposing = true
        lastError = nil
        defer { isComposing = false }

        // Flush pending signals before composing so the server has latest context
        await flushSignals()

        let apiRequest = APIComposeRequest(from: request, userId: configuration.userId)
        let response = try await networkClient.compose(request: apiRequest)
        let notification = response.toComposedNotification()

        lastComposedNotification = notification
        return notification
    }

    // MARK: - Feedback Reporting

    /// Report that the user opened a notification.
    public func reportOpened(notificationId: String) async {
        track(.notificationOpened, notificationId: notificationId)
        await sendFeedback(notificationId: notificationId, outcome: .opened, openedAt: Date())
    }

    /// Report that the user dismissed a notification.
    public func reportDismissed(notificationId: String) async {
        track(.notificationDismissed, notificationId: notificationId)
        await sendFeedback(notificationId: notificationId, outcome: .dismissed)
    }

    /// Report that the user converted (e.g., made a purchase) after opening a notification.
    public func reportConverted(notificationId: String) async {
        await sendFeedback(notificationId: notificationId, outcome: .converted,
                          openedAt: Date(), convertedAt: Date())
    }

    private func sendFeedback(
        notificationId: String,
        outcome: FeedbackOutcome,
        openedAt: Date? = nil,
        convertedAt: Date? = nil
    ) async {
        let payload = APIFeedbackPayload(
            notificationId: notificationId,
            userId: configuration.userId,
            outcome: outcome,
            openedAt: openedAt,
            convertedAt: convertedAt
        )
        do {
            try await networkClient.sendFeedback(payload: payload)
        } catch {
            // Feedback errors are non-fatal — log and continue
            print("[NotifyCompose] Feedback send failed: \(error.localizedDescription)")
        }
    }
}

// MARK: - Signal Types (SDK-level, maps to server SignalType)

public enum SignalType: String {
    case screenView = "screen_view"
    case itemClick = "item_click"
    case purchase = "purchase"
    case save = "save"
    case share = "share"
    case dismiss = "dismiss"
    case notificationOpened = "notification_opened"
    case notificationDismissed = "notification_dismissed"
    case appForeground = "app_foreground"
    case appBackground = "app_background"
    case search = "search"
}

public enum FeedbackOutcome: String, Encodable {
    case opened, dismissed, converted, unsubscribed
}

// MARK: - Internal Signal Model

struct Signal {
    let type: SignalType
    let itemId: String?
    let category: String?
    let durationSeconds: Double?
    let notificationId: String?
    let metadata: [String: String]
    let timestamp: Date = Date()
}
