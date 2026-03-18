// ECommerceDemoView.swift
// NotifyCompose Sample App — E-Commerce Domain Demo
//
// Demonstrates abandoned cart recovery with LLM-composed messages.

import SwiftUI

struct ECommerceDemoView: View {
    @EnvironmentObject var appState: AppState
    @StateObject private var viewModel = ECommerceDemoViewModel()

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {

                    PaperContextBanner(
                        text: "Paper Example: Abandoned cart recovery with urgency and social proof",
                        color: DemoSection.eCommerce.color
                    )

                    ScenarioCard(
                        title: "Abandoned Cart Scenario",
                        subtitle: "CLV-aware message with urgency signals",
                        items: [
                            ("person.fill", "WHO", "Gold-tier buyer, 8 purchases last 90 days"),
                            ("clock.fill", "WHEN", "4 hours after cart abandonment"),
                            ("cart.fill", "WHAT", "Sony WH-1000XM5 — $349.99, 4.7★, 2.1K reviews"),
                            ("sparkles", "HOW", "LLM adds scarcity + social proof signals")
                        ],
                        color: DemoSection.eCommerce.color
                    )

                    // Product selector
                    VStack(alignment: .leading, spacing: 10) {
                        Text("Select Product")
                            .font(.headline)
                        Picker("Product", selection: $viewModel.selectedProduct) {
                            ForEach(ECommerceDemoViewModel.sampleProducts, id: \.id) { product in
                                Text(product.name).tag(product)
                            }
                        }
                        .pickerStyle(.segmented)
                    }
                    .padding()
                    .background(Color(.systemGray6))
                    .cornerRadius(12)

                    // Discount toggle
                    Toggle(isOn: $viewModel.includeDiscount) {
                        Label("Include Limited-Time Discount", systemImage: "tag.fill")
                    }
                    .padding()
                    .background(Color(.systemGray6))
                    .cornerRadius(12)

                    ComposeButton(
                        isLoading: viewModel.isComposing,
                        color: DemoSection.eCommerce.color,
                        action: {
                            Task {
                                await viewModel.compose(using: appState.client)
                            }
                        }
                    )

                    if let notification = viewModel.result {
                        NotificationResultCard(
                            notification: notification,
                            color: DemoSection.eCommerce.color
                        )
                    }

                    if let error = viewModel.errorMessage {
                        ErrorCard(message: error)
                    }

                    Spacer(minLength: 40)
                }
                .padding()
            }
            .navigationTitle("E-Commerce")
            .navigationBarTitleDisplayMode(.large)
        }
    }
}

// MARK: - Product Model

struct DemoProduct: Hashable, Identifiable {
    let id: String
    let name: String
    let price: String
    let rating: String
    let reviews: String
    let category: String
}

// MARK: - ViewModel

@MainActor
final class ECommerceDemoViewModel: ObservableObject {
    @Published var isComposing = false
    @Published var result: ComposedNotification?
    @Published var errorMessage: String?
    @Published var includeDiscount = true
    @Published var selectedProduct: DemoProduct = sampleProducts[0]

    static let sampleProducts: [DemoProduct] = [
        DemoProduct(id: "prod_001", name: "Sony WH-1000XM5", price: "$349.99",
                    rating: "4.7", reviews: "2.1K", category: "electronics/audio"),
        DemoProduct(id: "prod_002", name: "Nike Air Max 270", price: "$129.99",
                    rating: "4.5", reviews: "8.4K", category: "fashion/shoes"),
        DemoProduct(id: "prod_003", name: "Instant Pot Duo 7-in-1", price: "$89.99",
                    rating: "4.8", reviews: "45K", category: "home/kitchen")
    ]

    func compose(using client: NotifyComposeClient) async {
        isComposing = true
        errorMessage = nil
        result = nil

        client.track(.itemClick, itemId: selectedProduct.id, category: selectedProduct.category)

        let request = ECommerceAdapter.abandonedCart(
            userId: "demo_user_001",
            productId: selectedProduct.id,
            productName: selectedProduct.name,
            price: selectedProduct.price,
            discount: includeDiscount ? "15% off — today only" : nil,
            stockLevel: "Only 3 left",
            category: selectedProduct.category
        )

        do {
            result = try await client.compose(request: request)
        } catch {
            errorMessage = error.localizedDescription
        }

        isComposing = false
    }
}
