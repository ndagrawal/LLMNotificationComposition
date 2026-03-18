// FoodDeliveryDemoView.swift
// NotifyCompose Sample App — Food Delivery Domain Demo
//
// Demonstrates the pizza re-engagement example from the paper:
// "The system knows WHO (frequent pizza buyer), WHEN (lunchtime, rainy day),
//  and WHAT (Margherita from Tony's). LLMs solve the HOW."

import SwiftUI

struct FoodDeliveryDemoView: View {
    @EnvironmentObject var appState: AppState
    @StateObject private var viewModel = FoodDeliveryDemoViewModel()

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {

                    // Paper context banner
                    PaperContextBanner(
                        text: "Paper Example: Re-engagement via context-aware message composition",
                        color: DemoSection.foodDelivery.color
                    )

                    // Scenario card
                    ScenarioCard(
                        title: "The Pizza Scenario",
                        subtitle: "WHO + WHEN + WHAT → LLM solves HOW",
                        items: [
                            ("person.fill", "WHO", "Frequent pizza buyer, 3 orders last month"),
                            ("clock.fill", "WHEN", "12:15 PM, Tuesday, rainy weather"),
                            ("cart.fill", "WHAT", "Margherita Pizza @ Tony's — $12.99, 4.8★"),
                            ("sparkles", "HOW", "LLM composes context-aware message")
                        ],
                        color: DemoSection.foodDelivery.color
                    )

                    // Context sliders
                    ContextControlPanel(
                        localHour: $viewModel.localHour,
                        weatherCondition: $viewModel.weatherCondition,
                        color: DemoSection.foodDelivery.color
                    )

                    // Compose button
                    ComposeButton(
                        isLoading: viewModel.isComposing,
                        color: DemoSection.foodDelivery.color,
                        action: {
                            Task {
                                await viewModel.compose(using: appState.client)
                            }
                        }
                    )

                    // Result
                    if let notification = viewModel.result {
                        NotificationResultCard(
                            notification: notification,
                            color: DemoSection.foodDelivery.color
                        )
                    }

                    if let error = viewModel.errorMessage {
                        ErrorCard(message: error)
                    }

                    Spacer(minLength: 40)
                }
                .padding()
            }
            .navigationTitle("Food Delivery")
            .navigationBarTitleDisplayMode(.large)
        }
    }
}

// MARK: - ViewModel

@MainActor
final class FoodDeliveryDemoViewModel: ObservableObject {
    @Published var isComposing = false
    @Published var result: ComposedNotification?
    @Published var errorMessage: String?
    @Published var localHour: Double = 12
    @Published var weatherCondition: String = "rainy"

    func compose(using client: NotifyComposeClient) async {
        isComposing = true
        errorMessage = nil
        result = nil

        // Track a signal before composing — simulates user browsing
        client.track(.screenView, itemId: "rest_tonys_001", category: "food/italian")

        let request = FoodDeliveryAdapter.reEngagement(
            userId: "demo_user_001",
            restaurantId: "rest_tonys_001",
            restaurantName: "Tony's Pizza",
            dishName: "Margherita Pizza",
            price: "$12.99",
            rating: "4.8",
            deliveryTime: "25 min",
            category: "food/italian",
            weatherCondition: weatherCondition,
            triggerContext: TriggerContext(
                localHour: Int(localHour),
                weatherCondition: weatherCondition,
                recentAppOpen: false
            )
        )

        do {
            result = try await client.compose(request: request)
        } catch {
            errorMessage = error.localizedDescription
        }

        isComposing = false
    }
}
