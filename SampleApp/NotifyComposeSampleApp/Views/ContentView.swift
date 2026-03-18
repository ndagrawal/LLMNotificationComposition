// ContentView.swift
// NotifyCompose Sample App — Root Navigation

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        TabView {
            FoodDeliveryDemoView()
                .tabItem {
                    Label("Food", systemImage: "fork.knife")
                }

            ECommerceDemoView()
                .tabItem {
                    Label("Shop", systemImage: "cart.fill")
                }

            SocialMediaDemoView()
                .tabItem {
                    Label("Social", systemImage: "person.2.fill")
                }

            PipelineInspectorView()
                .tabItem {
                    Label("Inspector", systemImage: "magnifyingglass")
                }
        }
        .accentColor(.primary)
    }
}
