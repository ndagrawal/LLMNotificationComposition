// NotifyComposeSampleApp.swift
// NotifyCompose Sample App — Main Entry Point
//
// Demonstrates the NotifyCompose SDK across three domains:
//   1. Food Delivery (re-engagement, pizza example from the paper)
//   2. E-Commerce (abandoned cart recovery)
//   3. Social Media (new content recommendation)
//
// Author: Nilesh Agrawal (nilesh.d.agrawal@gmail.com)

import SwiftUI

@main
struct NotifyComposeSampleApp: App {

    @StateObject private var appState = AppState()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(appState)
        }
    }
}

// MARK: - App State

/// Shared app state — holds the SDK client and current user session.
@MainActor
final class AppState: ObservableObject {

    // MARK: - SDK Client
    /// The NotifyCompose SDK client — initialized once per app session.
    /// In a real app, replace the baseURL with your server URL.
    let client: NotifyComposeClient

    // MARK: - Demo User
    @Published var currentUserId: String = "demo_user_001"
    @Published var selectedDomain: DemoSection = .foodDelivery

    init() {
        // Initialize the SDK client with your server URL
        // For local development: http://localhost:8000
        // For production: https://your-server.com
        let serverURL = ProcessInfo.processInfo.environment["NOTIFY_COMPOSE_SERVER_URL"]
            ?? "http://localhost:8000"

        self.client = NotifyComposeClient(
            baseURL: serverURL,
            userId: "demo_user_001"
        )
    }
}

// MARK: - Demo Sections

enum DemoSection: String, CaseIterable, Identifiable {
    case foodDelivery = "Food Delivery"
    case eCommerce = "E-Commerce"
    case socialMedia = "Social Media"

    var id: String { rawValue }

    var icon: String {
        switch self {
        case .foodDelivery: return "fork.knife"
        case .eCommerce: return "cart.fill"
        case .socialMedia: return "person.2.fill"
        }
    }

    var color: Color {
        switch self {
        case .foodDelivery: return Color(red: 0.95, green: 0.35, blue: 0.25)
        case .eCommerce: return Color(red: 0.20, green: 0.55, blue: 0.90)
        case .socialMedia: return Color(red: 0.35, green: 0.75, blue: 0.45)
        }
    }
}
